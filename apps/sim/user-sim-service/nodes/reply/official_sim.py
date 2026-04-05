from typing import Any, Dict

import httpx

from .base import ReplyAdapter, ReplySource


class OfficialSimReplyAdapter(ReplyAdapter):
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url.rstrip("/")

    def get_reply(
        self,
        run_id: str,
        user_message: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        platform = context.get("platform", "taobao")
        order_id = context.get("order_id", "")
        user_id = context.get("user_id", "")
        intent = context.get("intent", "")
        official_run_id = context.get("official_run_id")

        if not order_id:
            return {
                "text": "缺少订单信息，已切换到兜底回复。",
                "source": ReplySource.OFFICIAL_SIM.value,
                "run_id": run_id,
                "platform": platform,
                "fallback_to_stub": True,
                "timestamp": self._get_timestamp(),
            }

        try:
            response = self._call_official_sim(
                platform=platform,
                order_id=order_id,
                user_id=user_id,
                user_message=user_message,
                intent=intent,
                official_run_id=official_run_id,
            )
            reply_text = self._build_reply_text(intent=intent, order_id=order_id, response=response)
            if not reply_text:
                raise ValueError("official-sim response missing readable content")

            return {
                "text": reply_text,
                "source": ReplySource.OFFICIAL_SIM.value,
                "run_id": run_id,
                "platform": platform,
                "order_id": order_id,
                "api_response": response,
                "timestamp": self._get_timestamp(),
            }
        except Exception as e:
            return {
                "text": f"官方Sim调用失败: {str(e)}",
                "source": ReplySource.OFFICIAL_SIM.value,
                "run_id": run_id,
                "error": str(e),
                "fallback_to_stub": True,
                "timestamp": self._get_timestamp(),
            }

    def _call_official_sim(
        self,
        platform: str,
        order_id: str,
        user_id: str,
        user_message: str,
        intent: str,
        official_run_id: str | None = None,
    ) -> Dict[str, Any]:
        route_prefix = self._resolve_query_route(intent)
        params = {"platform": platform}
        if official_run_id:
            params["run_id"] = official_run_id
        with httpx.Client(timeout=30.0) as client:
            response = client.get(
                f"{self.base_url}{route_prefix}/{order_id}",
                params=params,
            )
            response.raise_for_status()
            return response.json()

    def _resolve_query_route(self, intent: str) -> str:
        if intent == "ask_shipment":
            return "/official-sim/raw/shipments"
        if intent in {"ask_refund", "refund_progress"}:
            return "/official-sim/raw/after-sales"
        return "/official-sim/raw/orders"

    def _build_reply_text(self, intent: str, order_id: str, response: Dict[str, Any]) -> str:
        data = response.get("data", {})
        if not isinstance(data, dict):
            return ""

        if intent == "ask_shipment":
            shipment = data.get("shipment", {})
            if not isinstance(shipment, dict):
                return ""
            shipment_status = self._pick_first(
                shipment,
                ["status", "status_text", "node", "shipment_status"],
            )
            tracking_no = self._pick_first(
                shipment,
                ["tracking_no", "out_sid", "waybill_no", "logistics_no"],
            )
            if shipment_status and tracking_no:
                return f"订单{order_id} 当前物流状态为 {shipment_status}，运单号 {tracking_no}。"
            if shipment_status:
                return f"订单{order_id} 当前物流状态为 {shipment_status}。"
            return f"订单{order_id} 的物流信息已查询到，但状态字段为空。"

        if intent in {"ask_refund", "refund_progress"}:
            after_sale = data.get("after_sale") or data.get("refund") or {}
            if not isinstance(after_sale, dict):
                return ""
            refund_status = self._pick_first(
                after_sale,
                ["status", "refund_status", "status_text"],
            )
            refund_amount = self._pick_first(
                after_sale,
                ["refund_amount", "refund_fee", "amount"],
            )
            if refund_status and refund_amount:
                return f"订单{order_id} 退款状态为 {refund_status}，退款金额 {refund_amount}。"
            if refund_status:
                return f"订单{order_id} 退款状态为 {refund_status}。"
            return f"订单{order_id} 的退款信息已查询到，但状态字段为空。"

        order = data.get("order", {})
        if not isinstance(order, dict):
            return ""
        order_status = self._pick_first(
            order,
            ["status", "status_text", "trade_status", "order_status"],
        )
        if order_status:
            return f"订单{order_id} 当前状态为 {order_status}。"
        return f"订单{order_id} 已查询到，但状态字段为空。"

    def _pick_first(self, payload: Dict[str, Any], keys: list[str]) -> str:
        for key in keys:
            value = payload.get(key)
            if value not in (None, "", []):
                return str(value)
        return ""

    def get_source(self) -> ReplySource:
        return ReplySource.OFFICIAL_SIM

    def _get_timestamp(self) -> str:
        from datetime import datetime
        return datetime.now().isoformat()
