from typing import Dict, Any, Optional, List
from datetime import datetime

from app.services.platform_gateway_service import PlatformGatewayService
from models.unified import Platform


class AfterSaleDomainService:
    def __init__(self, gateway: PlatformGatewayService):
        self.gateway = gateway
    
    def get_after_sale(self, platform: str, after_sale_id: str) -> Dict[str, Any]:
        platform_enum = Platform(platform)
        
        raw_data = self.gateway.get_refund(platform_enum, after_sale_id)
        
        return self._normalize_after_sale(raw_data, platform)
    
    def get_after_sale_by_order(self, platform: str, order_id: str) -> Dict[str, Any]:
        from providers.utils.fixture_loader import FixtureLoader
        
        refund_data = FixtureLoader.get_refund(platform, order_id)
        if refund_data:
            return self._normalize_after_sale(refund_data, platform)
        
        return {
            "error": "No after-sale found for this order",
            "order_id": order_id,
        }
    
    def batch_get_after_sales(self, requests: List[Dict[str, str]]) -> Dict[str, Any]:
        after_sales = []
        for req in requests:
            try:
                after_sale = self.get_after_sale(req["platform"], req["after_sale_id"])
                after_sales.append(after_sale)
            except Exception:
                pass
        
        return {
            "after_sales": after_sales,
            "total": len(after_sales),
        }
    
    def _normalize_after_sale(
        self,
        raw: Dict[str, Any],
        platform: str,
    ) -> Dict[str, Any]:
        return {
            "after_sale_id": raw.get("after_sale_id") or raw.get("refund_id") or raw.get("refundId"),
            "order_id": raw.get("order_id") or raw.get("tid") or raw.get("orderId"),
            "platform": platform,
            "status": raw.get("status", "unknown"),
            "status_text": self._get_status_text(raw.get("status", "unknown")),
            "type": raw.get("type") or raw.get("refund_type", "refund"),
            "reason": raw.get("reason") or raw.get("refund_reason", ""),
            "description": raw.get("description"),
            "refund_amount": str(raw.get("refund_amount") or raw.get("refund_fee") or raw.get("refundAmount", "0")),
            "created_at": raw.get("created_at") or raw.get("apply_time") or datetime.now().isoformat(),
            "updated_at": raw.get("updated_at") or raw.get("refund_time") or datetime.now().isoformat(),
        }
    
    def _get_status_text(self, status: str) -> str:
        status_map = {
            "pending": "待处理",
            "approved": "已同意",
            "rejected": "已拒绝",
            "refunding": "退款中",
            "completed": "已完成",
            "closed": "已关闭",
            "WAIT_SELLER_AGREE": "等待卖家同意",
            "WAIT_BUYER_RETURN_GOODS": "等待买家退货",
            "WAIT_SELLER_CONFIRM_GOODS": "等待卖家确认收货",
            "SUCCESS": "退款成功",
            "CLOSED": "退款关闭",
        }
        return status_map.get(status, status)
