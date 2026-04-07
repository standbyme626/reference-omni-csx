"""After-sale query service.

Only handles after-sale / refund retrieval and normalization.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from app.services.platform_gateway_service import PlatformGatewayService
from app.models.unified import Platform

from providers.utils.sim_identity import build_canonical_order_id, get_primary_order_id


_STATUS_TEXT = {
    "pending": "待处理", "approved": "已同意", "rejected": "已拒绝",
    "refunding": "退款中", "completed": "已完成", "closed": "已关闭",
    "WAIT_SELLER_AGREE": "等待卖家同意", "WAIT_BUYER_RETURN_GOODS": "等待买家退货",
    "WAIT_SELLER_CONFIRM_GOODS": "等待卖家确认收货",
    "SUCCESS": "退款成功", "CLOSED": "退款关闭",
}


class AfterSaleService:
    """Slim after-sale-query service."""

    def __init__(self, gateway: PlatformGatewayService):
        self.gateway = gateway

    def get_after_sale(
        self, platform: str, after_sale_id: str,
        official_run_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        platform_enum = Platform(platform)
        raw_data = self.gateway.get_refund(
            platform_enum, after_sale_id, official_run_id=official_run_id,
        )
        return self._normalize(raw_data, platform)

    def get_after_sale_by_order(
        self, platform: str, order_id: str,
        official_run_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        platform_enum = Platform(platform)
        try:
            raw_data = self.gateway.get_refund_by_order(
                platform_enum, order_id, official_run_id=official_run_id,
            )
            return self._normalize(raw_data, platform)
        except Exception:
            return {"error": "No after-sale found for this order", "order_id": order_id}

    def batch_get_after_sales(self, requests: List[Dict[str, str]]) -> Dict[str, Any]:
        after_sales: List[Dict[str, Any]] = []
        for req in requests:
            try:
                after_sales.append(self.get_after_sale(
                    req["platform"], req["after_sale_id"],
                    official_run_id=req.get("official_run_id"),
                ))
            except Exception:
                pass
        return {"after_sales": after_sales, "total": len(after_sales)}

    def _normalize(self, raw: Dict[str, Any], platform: str) -> Dict[str, Any]:
        ext_order_id = raw.get("external_order_id")
        if not ext_order_id:
            ext_order_id = get_primary_order_id(
                platform, str(raw.get("order_id") or raw.get("tid") or raw.get("orderId") or ""),
            )
        return {
            "after_sale_id": raw.get("after_sale_id") or raw.get("refund_id") or raw.get("refundId"),
            "canonical_after_sale_id": raw.get("canonical_after_sale_id")
                or raw.get("after_sale_id") or raw.get("refund_id") or raw.get("refundId"),
            "external_after_sale_id": raw.get("external_after_sale_id"),
            "order_id": raw.get("order_id") or raw.get("tid") or raw.get("orderId"),
            "external_order_id": ext_order_id,
            "requested_order_id": raw.get("requested_order_id"),
            "canonical_order_id": build_canonical_order_id(
                platform, str(ext_order_id or raw.get("order_id") or raw.get("tid") or raw.get("orderId") or ""),
            ),
            "platform": platform,
            "status": raw.get("status", "unknown"),
            "status_text": raw.get("status_text") or _STATUS_TEXT.get(raw.get("status", ""), raw.get("status", "未知")),
            "type": raw.get("type") or raw.get("refund_type", "refund"),
            "reason": raw.get("reason") or raw.get("refund_reason", ""),
            "description": raw.get("description"),
            "refund_amount": str(raw.get("refund_amount") or raw.get("refund_fee") or raw.get("refundAmount", "0")),
            "created_at": raw.get("created_at") or raw.get("apply_time") or datetime.now().isoformat(),
            "updated_at": raw.get("updated_at") or raw.get("refund_time") or datetime.now().isoformat(),
        }
