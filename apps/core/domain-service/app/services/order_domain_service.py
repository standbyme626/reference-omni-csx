from typing import Dict, Any, Optional, List
from datetime import datetime

from app.services.platform_gateway_service import PlatformGatewayService
from app.adapters.registry import PlatformRegistry
from models.unified import Platform, UnifiedOrder, UnifiedAddress, UnifiedProduct, OrderStatus
from adapters.platform_adapter import TaobaoAdapter, DouyinShopAdapter, JDAdapter, XhsAdapter, KuaishouAdapter


class OrderDomainService:
    def __init__(self, gateway: PlatformGatewayService, registry: PlatformRegistry):
        self.gateway = gateway
        self.registry = registry
        self._adapters = {
            Platform.TAOBAO: TaobaoAdapter(),
            Platform.DOUYIN_SHOP: DouyinShopAdapter(),
            Platform.JD: JDAdapter(),
            Platform.XHS: XhsAdapter(),
            Platform.KUAISHOU: KuaishouAdapter(),
        }
    
    def get_order(self, platform: str, order_id: str) -> Dict[str, Any]:
        platform_enum = Platform(platform)
        
        raw_data = self.gateway.get_order(platform_enum, order_id)
        
        adapter = self._adapters.get(platform_enum)
        if adapter:
            unified = adapter.to_unified_order(raw_data)
            return self._unified_to_response(unified)
        
        return self._raw_to_response(raw_data, platform)
    
    def get_order_with_user(self, platform: str, order_id: str) -> Dict[str, Any]:
        order = self.get_order(platform, order_id)
        
        from providers.utils.fixture_loader import FixtureLoader
        user_data = FixtureLoader.get_user_by_order(platform, order_id)
        
        return {
            "order": order,
            "user": {
                "user_id": user_data.get("user_id") if user_data else None,
                "name": user_data.get("name") if user_data else None,
            } if user_data else None,
        }
    
    def get_order_timeline(self, platform: str, order_id: str) -> List[Dict[str, Any]]:
        order = self.get_order(platform, order_id)
        
        timeline = [
            {
                "event": "order_created",
                "timestamp": order.get("created_at"),
                "description": "订单创建",
            },
        ]
        
        status = order.get("status")
        if status in ["paid", "wait_ship", "shipped", "finished"]:
            timeline.append({
                "event": "order_paid",
                "timestamp": order.get("updated_at"),
                "description": "订单支付",
            })
        
        if status in ["shipped", "finished"]:
            timeline.append({
                "event": "order_shipped",
                "timestamp": order.get("updated_at"),
                "description": "订单发货",
            })
        
        if status == "finished":
            timeline.append({
                "event": "order_finished",
                "timestamp": order.get("updated_at"),
                "description": "订单完成",
            })
        
        return timeline
    
    def batch_get_orders(self, requests: List[Dict[str, str]]) -> Dict[str, Any]:
        orders = []
        for req in requests:
            try:
                order = self.get_order(req["platform"], req["order_id"])
                orders.append(order)
            except Exception:
                pass
        
        return {
            "orders": orders,
            "total": len(orders),
        }
    
    def _unified_to_response(self, unified: UnifiedOrder) -> Dict[str, Any]:
        return {
            "order_id": unified.order_id,
            "platform": unified.platform.value,
            "status": unified.status.value,
            "status_text": self._get_status_text(unified.status),
            "total_amount": unified.total_amount,
            "pay_amount": unified.pay_amount,
            "freight": unified.freight,
            "receiver": {
                "name": unified.receiver.name,
                "phone": unified.receiver.phone,
                "address": unified.receiver.address,
            },
            "products": [
                {
                    "product_id": p.product_id,
                    "name": p.name,
                    "price": p.price,
                    "quantity": p.quantity,
                }
                for p in unified.products
            ],
            "created_at": unified.created_at.isoformat(),
            "updated_at": unified.updated_at.isoformat(),
            "external_order_id": unified.external_order_id,
        }
    
    def _raw_to_response(self, raw: Dict[str, Any], platform: str) -> Dict[str, Any]:
        return {
            "order_id": raw.get("order_id") or raw.get("tid") or raw.get("orderId"),
            "platform": platform,
            "status": raw.get("status", "unknown"),
            "status_text": raw.get("status_text", "未知状态"),
            "total_amount": str(raw.get("total_amount") or raw.get("total_fee") or raw.get("totalAmount", "0")),
            "pay_amount": str(raw.get("pay_amount") or raw.get("payment") or raw.get("payAmount", "0")),
            "freight": str(raw.get("freight", "0")),
            "receiver": raw.get("receiver", {}),
            "products": raw.get("products", []),
            "created_at": raw.get("created_at") or raw.get("created"),
            "updated_at": raw.get("updated_at") or raw.get("modified"),
        }
    
    def _get_status_text(self, status: OrderStatus) -> str:
        status_texts = {
            OrderStatus.WAIT_PAY: "待付款",
            OrderStatus.PAID: "已付款",
            OrderStatus.WAIT_SHIP: "待发货",
            OrderStatus.SHIPPED: "已发货",
            OrderStatus.IN_TRANSIT: "运输中",
            OrderStatus.FINISHED: "已完成",
            OrderStatus.TRADE_CLOSED: "交易关闭",
            OrderStatus.REFUNDING: "退款中",
            OrderStatus.REFUNDED: "已退款",
        }
        return status_texts.get(status, "未知状态")
