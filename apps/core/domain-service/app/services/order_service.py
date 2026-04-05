"""Order query service.

Only handles order retrieval and timeline generation.
Adapter field mapping is delegated to the adapter protocol.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from app.adapters.registry import PlatformRegistry, AdapterRegistry
from app.services.platform_gateway_service import PlatformGatewayService
from models.unified import OrderStatus, Platform

from providers.utils.fixture_loader import FixtureLoader
from providers.utils.sim_identity import build_canonical_order_id, get_primary_order_id


class OrderService:
    """Slim order-query service. Delegates field mapping to adapters."""

    def __init__(self, gateway: PlatformGatewayService, registry: AdapterRegistry):
        self.gateway = gateway
        self.registry = registry

    def get_order(
        self,
        platform: str,
        order_id: str,
        official_run_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        platform_enum = Platform(platform)

        raw_data = self.gateway.get_order(
            platform_enum,
            order_id,
            official_run_id=official_run_id,
        )
        if not isinstance(raw_data, dict) or not raw_data:
            raise ValueError(f"Order not found: {order_id}")

        adapter = self.registry.get_adapter(platform_enum)
        if adapter:
            try:
                unified = adapter.to_unified_order(raw_data)
                response = self._unified_to_response(unified)
                if response.get("order_id"):
                    return self._attach_identity(response, platform, order_id)
            except Exception:
                # Fallback to generic normalization for sim-layer raw payloads.
                pass

        response = self._normalize_raw(raw_data, platform)
        if response.get("order_id"):
            return self._attach_identity(response, platform, order_id)
        raise ValueError(f"Order not found: {order_id}")

    def get_order_with_user(
        self,
        platform: str,
        order_id: str,
        official_run_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        order = self.get_order(platform, order_id, official_run_id=official_run_id)
        user_data = FixtureLoader.get_user_by_order(platform, order_id)
        return {
            "order": order,
            "user": {
                "user_id": user_data.get("user_id") if user_data else None,
                "name": user_data.get("name") if user_data else None,
            } if user_data else None,
        }

    def get_order_timeline(
        self,
        platform: str,
        order_id: str,
        official_run_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        order = self.get_order(platform, order_id, official_run_id=official_run_id)
        timeline = [
            {"event": "order_created", "timestamp": order.get("created_at"), "description": "订单创建"},
        ]
        status = order.get("status")
        if status in ("paid", "wait_ship", "shipped", "finished"):
            timeline.append(
                {"event": "order_paid", "timestamp": order.get("updated_at"), "description": "订单支付"}
            )
        if status in ("shipped", "finished"):
            timeline.append(
                {"event": "order_shipped", "timestamp": order.get("updated_at"), "description": "订单发货"}
            )
        if status == "finished":
            timeline.append(
                {"event": "order_finished", "timestamp": order.get("updated_at"), "description": "订单完成"}
            )
        return timeline

    def batch_get_orders(self, requests: List[Dict[str, str]]) -> Dict[str, Any]:
        orders: List[Dict[str, Any]] = []
        for req in requests:
            try:
                orders.append(self.get_order(
                    req["platform"], req["order_id"],
                    official_run_id=req.get("official_run_id"),
                ))
            except Exception:
                pass
        return {"orders": orders, "total": len(orders)}

    # -- internal helpers ---------------------------------------------------

    def _unified_to_response(self, unified: Dict[str, Any]) -> Dict[str, Any]:
        receiver = unified.get("receiver", {})
        return {
            "order_id": unified.get("order_id"),
            "platform": unified.get("platform"),
            "status": unified.get("status"),
            "status_text": _status_text_for(unified.get("status")),
            "total_amount": unified.get("total_amount"),
            "pay_amount": unified.get("pay_amount"),
            "freight": unified.get("freight"),
            "receiver": {
                "name": receiver.get("name", ""),
                "phone": receiver.get("phone", ""),
                "address": receiver.get("address", ""),
            },
            "products": [
                {"product_id": p.get("product_id"), "name": p.get("name"),
                 "price": p.get("price"), "quantity": p.get("quantity")}
                for p in unified.get("products", [])
            ],
            "created_at": _iso(unified.get("created_at")),
            "updated_at": _iso(unified.get("updated_at")),
            "external_order_id": unified.get("external_order_id"),
        }

    def _normalize_raw(self, raw: Dict[str, Any], platform: str) -> Dict[str, Any]:
        if isinstance(raw.get("trade"), dict):
            trade = raw["trade"]
            raw = {**trade, "order_id": trade.get("tid"), "items": raw.get("orders", {}).get("order", [])}
        elif isinstance(raw.get("order"), dict):
            order = raw["order"]
            raw = {
                **order,
                "order_id": order.get("order_id") or order.get("orderId"),
                "items": order.get("productItems", raw.get("items", [])),
                "receiver": order.get("receiver", raw.get("receiver", {})),
            }
        elif isinstance(raw.get("jingdong_order_search_responce"), dict):
            order = raw["jingdong_order_search_responce"]
            raw = {
                **order,
                "order_id": order.get("orderId"),
                "items": order.get("product", []),
                "receiver": {"name": order.get("buyerFullName", ""), "phone": order.get("buyerMobile", ""),
                             "address": order.get("buyerFullAddress", "")},
                "total_amount": order.get("orderTotalMoney"),
                "pay_amount": order.get("orderBuyerPayableMoney"),
                "freight": order.get("orderFreightMoney", 0),
                "create_time": order.get("orderStartTime"),
                "update_time": order.get("orderStatusTime"),
                "status": order.get("orderStatus"),
            }

        receiver = raw.get("receiver", {})
        if not isinstance(receiver, dict):
            receiver = {}
        if not receiver and isinstance(raw.get("receiverAddress"), dict):
            addr = raw["receiverAddress"]
            receiver = {
                "name": raw.get("receiverName", ""),
                "phone": raw.get("receiverPhone", ""),
                "address": " ".join(str(addr.get(k, "")) for k in ("province", "city", "district", "detail")).strip(),
            }

        products = raw.get("products", [])
        if not products and isinstance(raw.get("items"), list):
            products = [
                {"product_id": str(item.get("product_id") or item.get("productId")
                                   or item.get("item_id") or item.get("oid") or item.get("skuId") or ""),
                 "name": item.get("name") or item.get("productName") or item.get("title") or item.get("skuName") or "",
                 "price": str(item.get("price", "0")),
                 "quantity": int(item.get("quantity") or item.get("num") or 1)}
                for item in raw["items"] if isinstance(item, dict)
            ]

        return {
            "order_id": raw.get("order_id") or raw.get("tid") or raw.get("orderId"),
            "platform": platform,
            "status": str(raw.get("status", "unknown")).lower(),
            "status_text": raw.get("status_text") or raw.get("orderStatusName") or "未知状态",
            "total_amount": str(raw.get("total_amount") or raw.get("amount") or raw.get("total_fee")
                                or raw.get("totalAmount") or "0"),
            "pay_amount": str(raw.get("pay_amount") or raw.get("payment") or raw.get("payAmount")
                              or raw.get("paymentAmount") or raw.get("amount") or "0"),
            "freight": str(raw.get("freight") or raw.get("post_fee") or raw.get("freightAmount") or "0"),
            "receiver": receiver,
            "products": products,
            "created_at": raw.get("created_at") or raw.get("create_time") or raw.get("createTime") or raw.get("created"),
            "updated_at": raw.get("updated_at") or raw.get("update_time") or raw.get("updateTime")
                          or raw.get("paid_at") or raw.get("modified"),
        }

    def _attach_identity(
        self, response: Dict[str, Any], platform: str, requested_order_id: str,
    ) -> Dict[str, Any]:
        observed = str(response.get("order_id") or requested_order_id)
        resolved_external = get_primary_order_id(platform, str(response.get("external_order_id") or observed))
        response["requested_order_id"] = str(requested_order_id)
        response["external_order_id"] = resolved_external
        response["canonical_order_id"] = build_canonical_order_id(platform, resolved_external)
        return response


# -- module-level helpers --------------------------------------------------

def _iso(value: Any) -> str:
    if value is None:
        return datetime.now().isoformat()
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _status_text_for(status) -> str:
    mapping = {
        OrderStatus.WAIT_PAY: "待付款", OrderStatus.PAID: "已付款",
        OrderStatus.WAIT_SHIP: "待发货", OrderStatus.SHIPPED: "已发货",
        OrderStatus.IN_TRANSIT: "运输中", OrderStatus.FINISHED: "已完成",
        OrderStatus.TRADE_CLOSED: "交易关闭",
        OrderStatus.REFUNDING: "退款中", OrderStatus.REFUNDED: "已退款",
    }
    try:
        return mapping.get(status, "未知状态")
    except Exception:
        return str(status)
