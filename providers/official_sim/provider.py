from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Dict, List, Optional

import httpx

from providers.utils.sim_identity import iter_order_id_aliases


class OfficialSimNotFoundError(ValueError):
    """Raised when official-sim explicitly returns 404 for an entity."""


class OfficialSimRequestError(RuntimeError):
    """Raised when official-sim is unavailable or returns non-2xx errors."""


class OfficialSimProxyProvider:
    """Provider facade that reads platform facts from official-sim endpoints.

    - Primary source: official-sim HTTP endpoints
    - Optional fallback: existing local mock provider (for availability only)

    NotFound errors are never masked by fallback to keep data semantics correct.
    """

    _PLATFORM_PATH = {
        "taobao": "taobao",
        "douyin_shop": "douyin-shop",
        "jd": "jd",
        "xhs": "xhs",
        "kuaishou": "kuaishou",
        "wecom_kf": "wecom-kf",
    }

    _ORDER_STATUS_MAP = {
        # Taobao
        "WAIT_BUYER_PAY": "wait_pay",
        "WAIT_SELLER_SEND_GOODS": "wait_ship",
        "WAIT_BUYER_CONFIRM_GOODS": "shipped",
        "TRADE_FINISHED": "finished",
        "TRADE_CLOSED": "trade_closed",
        "TRADE_CLOSED_BY_TAOBAO": "trade_closed",
        "TRADE_REFUNDING": "refunding",
        # Douyin/JD/XHS/Kuaishou common
        "ORDER_STATUS_SHIPPED": "shipped",
        "ORDER_STATUS_DELIVERED": "finished",
        "PAID": "paid",
        "SHIPPED": "shipped",
        "DELIVERED": "finished",
        "CANCELLED": "trade_closed",
        # Numeric-ish states seen in fixtures
        "0": "wait_pay",
        "10": "wait_pay",
        "20": "paid",
        "30": "wait_ship",
        "40": "wait_ship",
        "100": "shipped",
        "110": "in_transit",
        "120": "in_transit",
        "200": "finished",
        "300": "refunding",
        "500": "trade_closed",
    }

    _REFUND_STATUS_MAP = {
        "WAIT_SELLER_AGREE": "pending",
        "WAIT_BUYER_RETURN_GOODS": "pending",
        "WAIT_SELLER_CONFIRM_GOODS": "pending",
        "WAIT_SELLER_RECEIVE": "pending",
        "SUCCESS": "completed",
        "CLOSED": "closed",
        "REFUNDED": "completed",
        "refunded": "completed",
        "refunding": "refunding",
        "refund_processing": "refunding",
        "refund_applied": "pending",
        "applied": "pending",
        "refund_success": "completed",
        "refund_rejected": "rejected",
        "approved": "approved",
        "rejected": "rejected",
        "10": "pending",
        "20": "approved",
        "160": "completed",
        "170": "rejected",
    }

    _JD_SHIPMENT_STATUS_MAP = {
        "31000": "pending",
        "31010": "pending",
        "32000": "pending",
        "33030": "shipped",
        "33040": "shipped",
        "33050": "shipped",
        "33060": "delivered",
        "34000": "delivered",
        "34010": "delivered",
        "90000": "delivered",
    }

    def __init__(
        self,
        platform: str,
        base_url: str,
        fallback_provider: Optional[Any] = None,
        timeout_s: float = 5.0,
    ):
        self.platform = platform
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_s
        self.fallback_provider = fallback_provider

    # ---------- Public provider-like methods ----------

    def get_order(self, order_id: str, official_run_id: Optional[str] = None) -> Dict[str, Any]:
        def _remote() -> Dict[str, Any]:
            params: Dict[str, Any] = {"platform": self.platform}
            if official_run_id:
                params["run_id"] = official_run_id
            envelope = self._request_json(
                "GET",
                f"/official-sim/raw/orders/{order_id}",
                params=params,
            )
            payload = self._extract_data(envelope)
            payload_order_id = self._extract_order_id(payload)
            if payload_order_id and not self._matches_requested_order_id(order_id, payload_order_id):
                raise OfficialSimNotFoundError(f"order not found: {order_id}")
            return payload

        return self._execute_with_optional_fallback("get_order", _remote, order_id)

    def list_orders(self, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        if self.fallback_provider is not None and hasattr(self.fallback_provider, "list_orders"):
            return self.fallback_provider.list_orders(page, page_size)
        return {"order_list": [], "total_count": 0, "page": page, "page_size": page_size}

    def get_shipment(self, order_id: str, official_run_id: Optional[str] = None) -> Dict[str, Any]:
        def _remote() -> Dict[str, Any]:
            params: Dict[str, Any] = {"platform": self.platform}
            if official_run_id:
                params["run_id"] = official_run_id
            envelope = self._request_json(
                "GET",
                f"/official-sim/raw/shipments/{order_id}",
                params=params,
            )
            payload = self._extract_data(envelope)
            shipment = payload.get("shipment", payload)
            normalized = self._normalize_shipment(shipment, order_id)
            if (
                normalized.get("status") == "unknown"
                and not normalized.get("company")
                and not normalized.get("tracking_no")
                and not normalized.get("nodes")
            ):
                raise OfficialSimNotFoundError(f"shipment not found: {order_id}")
            return normalized

        return self._execute_with_optional_fallback("get_shipment", _remote, order_id)

    def get_refund(self, refund_id: str, official_run_id: Optional[str] = None) -> Dict[str, Any]:
        def _remote() -> Dict[str, Any]:
            params: Dict[str, Any] = {"platform": self.platform}
            if official_run_id:
                params["run_id"] = official_run_id
            envelope = self._request_json(
                "GET",
                f"/official-sim/raw/after-sales/{refund_id}",
                params=params,
            )
            payload = self._extract_data(envelope)
            refund = payload.get("after_sale") or payload.get("refund") or payload
            payload_refund_ids = self._extract_refund_ids(refund)
            if payload_refund_ids and str(refund_id) not in payload_refund_ids:
                raise OfficialSimNotFoundError(f"after-sale not found: {refund_id}")
            return self._normalize_refund(refund, refund_id)

        return self._execute_with_optional_fallback("get_refund", _remote, refund_id)

    def get_refund_by_order(
        self,
        order_id: str,
        official_run_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        def _remote() -> Dict[str, Any]:
            params: Dict[str, Any] = {"platform": self.platform}
            if official_run_id:
                params["run_id"] = official_run_id
            envelope = self._request_json(
                "GET",
                f"/official-sim/raw/after-sales/by-order/{order_id}",
                params=params,
            )
            payload = self._extract_data(envelope)
            refund = payload.get("after_sale") or payload.get("refund") or payload
            payload_order_id = (
                refund.get("requested_order_id")
                or refund.get("order_id")
                or refund.get("orderId")
                or refund.get("tid")
            )
            if payload_order_id and not self._matches_requested_order_id(order_id, payload_order_id):
                raise OfficialSimNotFoundError(f"after-sale not found for order: {order_id}")
            normalized_identifier = (
                refund.get("after_sale_id")
                or refund.get("refund_id")
                or refund.get("refundId")
                or order_id
            )
            return self._normalize_refund(refund, str(normalized_identifier))

        return self._execute_with_optional_fallback("get_refund_by_order", _remote, order_id)

    def create_refund(self, order_id: str, reason: str, amount: str) -> Dict[str, Any]:
        if self.fallback_provider is not None and hasattr(self.fallback_provider, "create_refund"):
            return self.fallback_provider.create_refund(order_id, reason, amount)
        return {
            "refund_id": f"REF_{order_id}",
            "order_id": order_id,
            "status": "pending",
            "refund_amount": amount,
            "reason": reason,
            "created_at": datetime.utcnow().isoformat(),
        }

    def search_conversations(self, limit: int = 100) -> Dict[str, Any]:
        if self.platform != "wecom_kf":
            raise ValueError(f"Platform {self.platform} does not support conversation operations")

        def _remote() -> Dict[str, Any]:
            envelope = self._request_json(
                "GET",
                "/official-sim/raw/conversations",
                params={"platform": self.platform, "limit": limit},
            )
            payload = self._extract_data(envelope)
            items = payload.get("items", []) if isinstance(payload, dict) else []
            normalized_items = [
                self._normalize_conversation_search_item(item)
                for item in items
                if isinstance(item, dict)
            ]
            return {
                "items": normalized_items,
                "total": payload.get("total", len(normalized_items))
                if isinstance(payload, dict)
                else len(normalized_items),
            }

        return self._execute_with_optional_fallback("search_conversations", _remote, limit)

    def get_conversation(
        self,
        conversation_id: str,
        official_run_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        if self.platform != "wecom_kf":
            raise ValueError(f"Platform {self.platform} does not support conversation operations")

        def _remote() -> Dict[str, Any]:
            params: Dict[str, Any] = {"platform": self.platform}
            if official_run_id:
                params["run_id"] = official_run_id
            envelope = self._request_json(
                "GET",
                f"/official-sim/raw/conversations/{conversation_id}",
                params=params,
            )
            payload = self._extract_data(envelope)
            return self._normalize_conversation(payload, conversation_id)

        try:
            return _remote()
        except OfficialSimNotFoundError:
            raise
        except Exception as exc:
            if self.fallback_provider is not None and hasattr(self.fallback_provider, "get_conversation"):
                return self.fallback_provider.get_conversation(conversation_id)
            raise OfficialSimRequestError(str(exc)) from exc

    def list_messages(
        self,
        conversation_id: str,
        limit: int = 100,
        official_run_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        if self.platform != "wecom_kf":
            raise ValueError(f"Platform {self.platform} does not support message operations")

        def _remote() -> Dict[str, Any]:
            params: Dict[str, Any] = {"platform": self.platform, "limit": limit}
            if official_run_id:
                params["run_id"] = official_run_id
            envelope = self._request_json(
                "GET",
                f"/official-sim/raw/conversations/{conversation_id}/messages",
                params=params,
            )
            payload = self._extract_data(envelope)
            return self._normalize_messages(payload, conversation_id, limit)

        try:
            return _remote()
        except OfficialSimNotFoundError:
            raise
        except Exception as exc:
            if self.fallback_provider is not None and hasattr(self.fallback_provider, "list_messages"):
                return self.fallback_provider.list_messages(conversation_id, limit)
            raise OfficialSimRequestError(str(exc)) from exc

    # ---------- HTTP helpers ----------

    def _request_json(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        try:
            with httpx.Client(timeout=self.timeout_s) as client:
                response = client.request(method, url, params=params, json=json_body)
        except Exception as exc:  # network/timeouts
            raise OfficialSimRequestError(f"official-sim unavailable: {exc}") from exc

        detail = None
        try:
            error_payload = response.json()
            if isinstance(error_payload, dict):
                detail = error_payload.get("detail") or error_payload.get("message")
        except Exception:
            detail = None

        if response.status_code == 404:
            raise OfficialSimNotFoundError(detail or f"resource not found: {path}")
        if response.status_code >= 400:
            raise OfficialSimRequestError(
                detail or f"official-sim error {response.status_code}: {response.text[:200]}"
            )

        payload = response.json()
        if isinstance(payload, dict):
            return payload
        return {"data": payload}

    def _extract_data(self, envelope: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(envelope, dict):
            return {}
        data = envelope.get("data")
        if isinstance(data, dict):
            return data
        return envelope

    def _extract_order_id(self, payload: Dict[str, Any]) -> Optional[str]:
        if not isinstance(payload, dict):
            return None
        if isinstance(payload.get("trade"), dict):
            trade = payload["trade"]
            order_id = trade.get("tid") or trade.get("order_id") or trade.get("orderId")
            return str(order_id) if order_id is not None else None
        if isinstance(payload.get("order"), dict):
            order = payload["order"]
            order_id = order.get("order_id") or order.get("orderId") or order.get("tid")
            return str(order_id) if order_id is not None else None
        if isinstance(payload.get("jingdong_order_search_responce"), dict):
            order_id = payload["jingdong_order_search_responce"].get("orderId")
            return str(order_id) if order_id is not None else None
        order_id = payload.get("order_id") or payload.get("orderId") or payload.get("tid")
        return str(order_id) if order_id is not None else None

    def _extract_refund_ids(self, payload: Dict[str, Any]) -> set[str]:
        if not isinstance(payload, dict):
            return set()
        candidates = {
            payload.get("after_sale_id"),
            payload.get("canonical_after_sale_id"),
            payload.get("external_after_sale_id"),
            payload.get("requested_identifier"),
            payload.get("refund_id"),
            payload.get("refundId"),
            payload.get("afsServiceId"),
            payload.get("id"),
        }
        return {str(candidate) for candidate in candidates if candidate not in (None, "")}

    def _matches_requested_order_id(self, requested_order_id: Any, payload_order_id: Any) -> bool:
        requested = str(requested_order_id)
        payload = str(payload_order_id)
        if requested == payload:
            return True
        return payload in iter_order_id_aliases(self.platform, requested)

    def _execute_with_optional_fallback(self, method_name: str, remote_call, *fallback_args):
        try:
            return remote_call()
        except OfficialSimNotFoundError:
            raise
        except Exception as exc:
            if self.fallback_provider is not None and hasattr(self.fallback_provider, method_name):
                return getattr(self.fallback_provider, method_name)(*fallback_args)
            raise OfficialSimRequestError(str(exc)) from exc

    # ---------- Normalizers ----------

    def _normalize_order(self, payload: Dict[str, Any], order_id: str) -> Dict[str, Any]:
        payload = payload or {}

        # official fixture style: {"response": {"trade": ...}}
        if isinstance(payload.get("response"), dict):
            response = payload["response"]
            if isinstance(response.get("trade"), dict):
                payload = response["trade"]

        # taobao official style in provider mocks
        if isinstance(payload.get("trade"), dict):
            payload = payload["trade"]

        receiver = self._normalize_receiver(payload)
        products = self._normalize_products(payload)

        raw_status = payload.get("status") or payload.get("orderStatus")
        normalized_status = self._map_order_status(raw_status)

        normalized_order_id = (
            payload.get("order_id")
            or payload.get("orderId")
            or payload.get("tid")
            or payload.get("trade_id")
            or order_id
        )

        return {
            "order_id": str(normalized_order_id),
            "status": normalized_status,
            "status_text": payload.get("status_text") or payload.get("orderStatusName") or normalized_status,
            "total_amount": self._to_amount(
                payload.get("total_amount")
                or payload.get("amount")
                or payload.get("total_fee")
                or payload.get("totalAmount")
            ),
            "pay_amount": self._to_amount(
                payload.get("pay_amount")
                or payload.get("payment")
                or payload.get("paymentAmount")
                or payload.get("amount")
            ),
            "freight": self._to_amount(
                payload.get("freight")
                or payload.get("post_fee")
                or payload.get("freightAmount")
                or 0
            ),
            "receiver": receiver,
            "products": products,
            "created_at": self._to_iso(
                payload.get("created_at")
                or payload.get("create_time")
                or payload.get("createTime")
                or payload.get("created")
            ),
            "updated_at": self._to_iso(
                payload.get("updated_at")
                or payload.get("update_time")
                or payload.get("updateTime")
                or payload.get("paid_at")
                or payload.get("pay_time")
                or payload.get("payTime")
                or payload.get("modified")
            ),
        }

    def _normalize_shipment(self, payload: Dict[str, Any], order_id: str) -> Dict[str, Any]:
        payload = payload or {}
        if isinstance(payload.get("response"), dict):
            response = payload["response"]
            payload = (
                response.get("shipment")
                or response.get("trade")
                or response.get("order")
                or response.get("jingdong_order_search_responce")
                or response
            )

        if isinstance(payload.get("trade"), dict):
            return self._normalize_taobao_shipment(payload["trade"], order_id)

        if isinstance(payload.get("order"), dict):
            return self._normalize_order_shipment(payload["order"], order_id)

        if isinstance(payload.get("shipment"), dict):
            payload = payload["shipment"]

        if isinstance(payload.get("jingdong_order_search_responce"), dict):
            payload = payload["jingdong_order_search_responce"]

        if self._looks_like_jd_shipment_payload(payload):
            return self._normalize_jd_shipment(payload, order_id)

        nodes: List[Dict[str, Any]] = []
        for node in payload.get("nodes", []):
            if not isinstance(node, dict):
                continue
            nodes.append(
                {
                    "node": node.get("node") or node.get("status") or "",
                    "time": self._to_iso(node.get("time") or node.get("timestamp")),
                    "description": node.get("description") or node.get("desc") or node.get("node") or "",
                }
            )

        tracking_no = payload.get("tracking_no") or payload.get("out_sid") or payload.get("waybill_no")
        company = payload.get("company") or payload.get("company_name") or payload.get("companyName")

        return {
            "shipment_id": payload.get("shipment_id") or payload.get("sid") or f"SHIP_{order_id}",
            "order_id": payload.get("order_id") or order_id,
            "status": self._map_generic_shipment_status(
                payload.get("status"),
                tracking_no=tracking_no,
                company=company,
                delivered_at=payload.get("delivered_at"),
            ),
            "company": company,
            "tracking_no": tracking_no,
            "nodes": nodes,
            "created_at": self._to_iso(payload.get("created_at") or payload.get("send_time")),
            "updated_at": self._to_iso(payload.get("updated_at") or payload.get("update_time")),
        }

    def _normalize_taobao_shipment(self, payload: Dict[str, Any], order_id: str) -> Dict[str, Any]:
        orders = payload.get("orders", {}) if isinstance(payload.get("orders"), dict) else {}
        items = orders.get("order", [])
        if not items and isinstance(payload.get("orders"), list):
            items = payload.get("orders", [])
        first_item = items[0] if items else {}
        company = first_item.get("logistics_company")
        tracking_no = first_item.get("invoice_no")
        created_at = payload.get("consign_time") or payload.get("modified")
        updated_at = payload.get("end_time") or payload.get("modified") or created_at
        status = self._map_generic_shipment_status(
            payload.get("status"),
            tracking_no=tracking_no,
            company=company,
            delivered_at=payload.get("end_time"),
        )

        nodes: List[Dict[str, Any]] = []
        self._append_shipment_node(nodes, "订单创建", payload.get("created"), "订单已创建")
        self._append_shipment_node(nodes, "已支付", payload.get("pay_time"), "订单已完成支付")
        shipment_description = "包裹已进入物流环节"
        if company and tracking_no:
            shipment_description = f"承运商 {company}，运单号 {tracking_no}"
        elif company:
            shipment_description = f"承运商 {company}"
        elif tracking_no:
            shipment_description = f"运单号 {tracking_no}"
        self._append_shipment_node(
            nodes,
            "已签收" if status == "delivered" else "已发货",
            payload.get("consign_time"),
            shipment_description,
        )
        self._append_shipment_node(nodes, "已签收", payload.get("end_time"), "包裹已完成签收")

        return {
            "shipment_id": payload.get("shipment_id") or payload.get("sid") or f"SHIP_{order_id}",
            "order_id": str(payload.get("tid") or payload.get("order_id") or order_id),
            "status": status,
            "company": company,
            "tracking_no": tracking_no,
            "nodes": nodes,
            "created_at": self._to_iso(created_at),
            "updated_at": self._to_iso(updated_at),
        }

    def _normalize_order_shipment(self, payload: Dict[str, Any], order_id: str) -> Dict[str, Any]:
        delivery_info = payload.get("delivery_info", {})
        if not isinstance(delivery_info, dict):
            delivery_info = {}
        logistics = payload.get("logistics", {})
        if not isinstance(logistics, dict):
            logistics = {}

        company = (
            delivery_info.get("company_name")
            or logistics.get("logisticsCompany")
            or logistics.get("company")
            or logistics.get("companyName")
        )
        tracking_no = (
            delivery_info.get("tracking_no")
            or logistics.get("trackingNo")
            or logistics.get("tracking_no")
        )
        created_at = (
            payload.get("deliveryTime")
            or payload.get("delivery_time")
            or payload.get("consign_time")
            or payload.get("consignTime")
            or payload.get("updateTime")
            or payload.get("update_time")
        )
        updated_at = (
            payload.get("finishTime")
            or payload.get("finish_time")
            or payload.get("updateTime")
            or payload.get("update_time")
            or created_at
        )
        raw_status = (
            logistics.get("status")
            or delivery_info.get("delivery_status_desc")
            or delivery_info.get("delivery_status")
            or payload.get("deliveryStatus")
            or payload.get("statusDesc")
        )
        status = self._map_generic_shipment_status(
            raw_status,
            tracking_no=tracking_no,
            company=company,
            delivered_at=payload.get("finishTime") or payload.get("finish_time"),
        )

        nodes: List[Dict[str, Any]] = []
        self._append_shipment_node(
            nodes,
            "订单创建",
            payload.get("createTime") or payload.get("create_time"),
            "订单已创建",
        )
        self._append_shipment_node(
            nodes,
            "已支付",
            payload.get("payTime") or payload.get("pay_time") or payload.get("confirmTime") or payload.get("confirm_time"),
            "订单已完成支付",
        )
        shipment_description = "包裹已进入物流环节"
        if company and tracking_no:
            shipment_description = f"承运商 {company}，运单号 {tracking_no}"
        elif company:
            shipment_description = f"承运商 {company}"
        elif tracking_no:
            shipment_description = f"运单号 {tracking_no}"
        self._append_shipment_node(
            nodes,
            "已签收" if status == "delivered" else "已发货",
            payload.get("deliveryTime")
            or payload.get("delivery_time")
            or payload.get("consign_time")
            or payload.get("consignTime"),
            shipment_description,
        )
        self._append_shipment_node(
            nodes,
            "已签收",
            payload.get("finishTime") or payload.get("finish_time"),
            "包裹已完成签收",
        )

        return {
            "shipment_id": payload.get("shipment_id") or payload.get("shipmentId") or f"SHIP_{order_id}",
            "order_id": str(payload.get("order_id") or payload.get("orderId") or order_id),
            "status": status,
            "company": company,
            "tracking_no": tracking_no,
            "nodes": nodes,
            "created_at": self._to_iso(created_at),
            "updated_at": self._to_iso(updated_at),
        }

    def _looks_like_jd_shipment_payload(self, payload: Dict[str, Any]) -> bool:
        if not isinstance(payload, dict):
            return False
        if "orderStatus" not in payload and "orderId" not in payload:
            return False
        return any(
            key in payload
            for key in (
                "deliveryCarrierName",
                "deliveryBillNo",
                "orderStatusTime",
                "deliveryConfirmTime",
            )
        )

    def _normalize_jd_shipment(self, payload: Dict[str, Any], order_id: str) -> Dict[str, Any]:
        company = payload.get("deliveryCarrierName")
        tracking_no = payload.get("deliveryBillNo")
        created_at = payload.get("orderPurchaseTime") or payload.get("orderStartTime") or payload.get("orderStatusTime")
        updated_at = payload.get("deliveryConfirmTime") or payload.get("orderStatusTime") or created_at
        status = self._map_jd_shipment_status(
            payload.get("orderStatus"),
            tracking_no=tracking_no,
            company=company,
            delivered_at=payload.get("deliveryConfirmTime"),
        )

        nodes: List[Dict[str, Any]] = []
        self._append_shipment_node(nodes, "订单创建", payload.get("orderStartTime"), "订单已创建")
        self._append_shipment_node(nodes, "已支付", payload.get("orderPurchaseTime"), "订单已完成支付")

        shipment_description = "包裹已进入物流环节"
        if company and tracking_no:
            shipment_description = f"承运商 {company}，运单号 {tracking_no}"
        elif company:
            shipment_description = f"承运商 {company}"
        elif tracking_no:
            shipment_description = f"运单号 {tracking_no}"

        shipment_node_name = "已签收" if status == "delivered" else "已发货"
        self._append_shipment_node(
            nodes,
            shipment_node_name,
            payload.get("orderStatusTime"),
            shipment_description,
        )
        self._append_shipment_node(
            nodes,
            "已签收",
            payload.get("deliveryConfirmTime"),
            "包裹已完成签收",
        )

        return {
            "shipment_id": payload.get("shipment_id") or payload.get("shipmentId") or f"SHIP_{order_id}",
            "order_id": str(payload.get("order_id") or payload.get("orderId") or order_id),
            "status": status,
            "company": company,
            "tracking_no": tracking_no,
            "nodes": nodes,
            "created_at": self._to_iso(created_at),
            "updated_at": self._to_iso(updated_at),
        }

    def _map_jd_shipment_status(
        self,
        raw_status: Any,
        *,
        tracking_no: Any,
        company: Any,
        delivered_at: Any,
    ) -> str:
        if delivered_at not in (None, ""):
            return "delivered"

        if raw_status is not None:
            mapped = self._JD_SHIPMENT_STATUS_MAP.get(str(raw_status))
            if mapped:
                return mapped

        if tracking_no or company:
            return "shipped"

        fallback = self._map_order_status(raw_status)
        return fallback if fallback != "unknown" else "pending"

    def _map_generic_shipment_status(
        self,
        raw_status: Any,
        *,
        tracking_no: Any,
        company: Any,
        delivered_at: Any,
    ) -> str:
        if delivered_at not in (None, ""):
            return "delivered"

        key = str(raw_status or "").strip().lower()
        explicit_map = {
            "wait_buyer_confirm_goods": "shipped",
            "wait_buyer_receive_goods": "shipped",
            "wait_buyer_receive": "shipped",
            "已发货": "shipped",
            "shipped": "shipped",
            "100": "shipped",
            "运输中": "in_transit",
            "配送中": "in_transit",
            "delivering": "in_transit",
            "in_transit": "in_transit",
            "20": "in_transit",
            "已签收": "delivered",
            "已完成": "delivered",
            "delivered": "delivered",
            "signed": "delivered",
            "finished": "delivered",
            "completed": "delivered",
        }
        if key in explicit_map:
            return explicit_map[key]

        fallback = self._map_order_status(raw_status)
        if fallback in {"finished"}:
            return "delivered"
        if fallback in {"shipped"}:
            return "shipped"
        if fallback in {"in_transit", "delivering"}:
            return "in_transit"
        if fallback in {"wait_ship", "paid", "seller_received", "jd_received", "station_received", "wait_self_pickup"}:
            return "pending"
        if fallback in {"trade_closed", "cancelled", "closed"}:
            return "cancelled"

        if tracking_no or company:
            return "shipped"
        return fallback if fallback != "unknown" else "unknown"

    def _append_shipment_node(
        self,
        nodes: List[Dict[str, Any]],
        node_name: str,
        raw_time: Any,
        description: str,
    ) -> None:
        if raw_time in (None, ""):
            return
        nodes.append(
            {
                "node": node_name,
                "time": self._to_iso(raw_time),
                "description": description,
            }
        )

    def _normalize_refund(self, payload: Dict[str, Any], refund_id: str) -> Dict[str, Any]:
        payload = payload or {}
        if isinstance(payload.get("response"), dict):
            response = payload["response"]
            payload = response.get("refund") or response

        if isinstance(payload.get("refund"), dict):
            payload = payload["refund"]

        raw_status = payload.get("status")
        normalized_status = self._map_refund_status(raw_status)
        external_after_sale_id = payload.get("external_after_sale_id")
        if external_after_sale_id in (None, ""):
            refund_identifier = payload.get("refundId") or payload.get("refund_id")
            after_sale_identifier = payload.get("after_sale_id")
            if refund_identifier not in (None, "") and str(refund_identifier) != str(after_sale_identifier):
                external_after_sale_id = refund_identifier

        return {
            "refund_id": payload.get("refund_id") or payload.get("after_sale_id") or refund_id,
            "after_sale_id": payload.get("after_sale_id") or payload.get("refund_id") or refund_id,
            "canonical_after_sale_id": payload.get("canonical_after_sale_id") or payload.get("after_sale_id") or refund_id,
            "external_after_sale_id": external_after_sale_id,
            "order_id": payload.get("order_id") or payload.get("tid") or refund_id,
            "external_order_id": payload.get("external_order_id"),
            "requested_order_id": payload.get("requested_order_id"),
            "status": normalized_status,
            "status_text": payload.get("status_text") or normalized_status,
            "reason": payload.get("reason") or payload.get("refund_reason") or "",
            "description": payload.get("description") or payload.get("reason_desc"),
            "refund_amount": self._to_amount(
                payload.get("refund_amount")
                or payload.get("amount")
                or payload.get("refund_fee")
                or payload.get("refundAmount")
            ),
            "created_at": self._to_iso(payload.get("created_at") or payload.get("apply_time")),
            "updated_at": self._to_iso(payload.get("updated_at") or payload.get("update_time") or payload.get("refund_time")),
        }

    def _normalize_conversation(self, payload: Dict[str, Any], conversation_id: str) -> Dict[str, Any]:
        payload = payload or {}

        if isinstance(payload.get("response"), dict):
            response = payload["response"]
            payload = response.get("conversation") or response

        if isinstance(payload.get("conversation"), dict):
            payload = payload["conversation"]

        customer = payload.get("customer") if isinstance(payload.get("customer"), dict) else {}

        conv_id = payload.get("conversation_id") or payload.get("session_id") or conversation_id
        status = payload.get("status") or payload.get("service_state") or "pending"

        return {
            "conversation_id": conv_id,
            "status": status,
            "openid": payload.get("openid") or payload.get("external_userid") or customer.get("external_userid"),
            "scene": payload.get("scene") or "customer_service",
            "created_at": self._to_iso(payload.get("create_time") or payload.get("created_at")),
            "updated_at": self._to_iso(payload.get("update_time") or payload.get("updated_at")),
            "customer_id": payload.get("customer_id") or customer.get("user_id") or customer.get("external_userid"),
            "customer_nick": payload.get("customer_nick") or customer.get("name") or customer.get("nickname"),
            "biz_id": payload.get("biz_id") or payload.get("order_id"),
            "biz_type": payload.get("biz_type", "conversation"),
            "biz_platform": payload.get("biz_platform", self.platform),
            "official_run_id": payload.get("official_run_id"),
            "message_count": payload.get("message_count"),
        }

    def _normalize_messages(self, payload: Dict[str, Any], conversation_id: str, limit: int) -> Dict[str, Any]:
        payload = payload or {}
        if isinstance(payload.get("response"), dict):
            response = payload["response"]
            raw_messages = response.get("msg_list") or response.get("messages") or []
        elif isinstance(payload.get("messages"), list):
            raw_messages = payload.get("messages", [])
        elif isinstance(payload.get("msg_list"), list):
            raw_messages = payload.get("msg_list", [])
        else:
            raw_messages = [payload]

        msg_list: List[Dict[str, Any]] = []
        for msg in raw_messages[: max(limit, 0)]:
            if not isinstance(msg, dict):
                continue
            msg_list.append(
                {
                    "msgid": msg.get("msgid") or msg.get("msg_id") or "",
                    "msgtype": msg.get("msgtype") or msg.get("msg_type") or "text",
                    "content": msg.get("content") or msg.get("text") or "",
                    "origin": msg.get("origin") if msg.get("origin") is not None else (3 if msg.get("role") == "customer" else 5),
                    "send_time": self._to_iso(msg.get("send_time") or msg.get("create_time") or msg.get("time")),
                    "conversation_id": msg.get("conversation_id") or conversation_id,
                    "sender_type": msg.get("sender_type"),
                    "created_at": self._to_iso(
                        msg.get("created_at") or msg.get("send_time") or msg.get("create_time") or msg.get("time")
                    ),
                }
            )

        return {
            "msg_list": msg_list,
            "messages": msg_list,
            "total": len(msg_list),
            "conversation_id": payload.get("conversation_id") or conversation_id,
            "official_run_id": payload.get("official_run_id"),
        }

    def _normalize_conversation_search_item(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        normalized = self._normalize_conversation(payload, payload.get("conversation_id", ""))
        normalized.update(
            {
                "id": payload.get("id") or normalized.get("conversation_id"),
                "platform": payload.get("platform", self.platform),
                "unread_count": payload.get("unread_count", 0),
                "last_message_time": payload.get("last_message_time") or normalized.get("updated_at"),
                "created_at": payload.get("created_at") or normalized.get("created_at"),
                "external_biz_id": payload.get("external_biz_id") or normalized.get("biz_id"),
            }
        )
        return normalized

    def _normalize_receiver(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        receiver = payload.get("receiver") if isinstance(payload.get("receiver"), dict) else {}
        receiver_addr = payload.get("receiverAddress") if isinstance(payload.get("receiverAddress"), dict) else {}

        if not receiver and receiver_addr:
            receiver = {
                "name": payload.get("receiverName") or "",
                "phone": payload.get("receiverPhone") or "",
                "address": " ".join(
                    [
                        str(receiver_addr.get("province", "")),
                        str(receiver_addr.get("city", "")),
                        str(receiver_addr.get("district", "")),
                        str(receiver_addr.get("detail", "")),
                    ]
                ).strip(),
            }

        if not receiver:
            receiver = {
                "name": payload.get("receiver_name") or "",
                "phone": payload.get("receiver_mobile") or payload.get("receiver_phone") or "",
                "address": payload.get("receiver_address") or "",
            }

        return {
            "name": receiver.get("name", ""),
            "phone": receiver.get("phone", ""),
            "address": receiver.get("address", ""),
        }

    def _normalize_products(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        source_products: List[Dict[str, Any]] = []

        if isinstance(payload.get("products"), list):
            source_products = payload["products"]
        elif isinstance(payload.get("items"), list):
            source_products = payload["items"]
        elif isinstance(payload.get("orders"), dict):
            source_products = payload.get("orders", {}).get("order", []) or []

        normalized: List[Dict[str, Any]] = []
        for item in source_products:
            if not isinstance(item, dict):
                continue
            normalized.append(
                {
                    "product_id": str(
                        item.get("product_id")
                        or item.get("productId")
                        or item.get("item_id")
                        or item.get("oid")
                        or item.get("skuId")
                        or ""
                    ),
                    "name": item.get("name") or item.get("productName") or item.get("title") or item.get("skuName") or "",
                    "price": self._to_amount(item.get("price") or item.get("unit_price") or 0),
                    "quantity": int(item.get("quantity") or item.get("num") or 1),
                }
            )

        return normalized

    def _map_order_status(self, raw_status: Any) -> str:
        if raw_status is None:
            return "unknown"
        key = str(raw_status)
        return self._ORDER_STATUS_MAP.get(key, key.lower())

    def _map_refund_status(self, raw_status: Any) -> str:
        if raw_status is None:
            return "unknown"
        key = str(raw_status)
        return self._REFUND_STATUS_MAP.get(key, key.lower())

    def _to_amount(self, value: Any) -> str:
        if value is None:
            return "0"
        try:
            return str(value)
        except Exception:
            return "0"

    def _to_iso(self, value: Any) -> str:
        if value in (None, ""):
            return datetime.now(UTC).isoformat()

        text = str(value).strip()
        if text.isdigit() and len(text) >= 10:
            try:
                return datetime.fromtimestamp(int(text), UTC).isoformat()
            except Exception:
                pass

        text = text.replace(" ", "T")
        if text.endswith("Z"):
            text = text[:-1]

        try:
            datetime.fromisoformat(text)
            return text
        except Exception:
            return datetime.utcnow().isoformat()

    def _platform_path(self) -> str:
        return self._PLATFORM_PATH.get(self.platform, self.platform.replace("_", "-"))
