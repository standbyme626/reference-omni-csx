"""Taobao adapter: Order-only capability."""

from __future__ import annotations

from typing import Any, Dict

from models.unified import OrderStatus

from .protocols import OrderAdapter


def _parse_datetime(value: Any):  # noqa: ANN202
    from datetime import datetime
    if isinstance(value, datetime):
        return value
    if value in (None, "", 0):
        return datetime.now()
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value)
    try:
        return datetime.fromisoformat(str(value))
    except (TypeError, ValueError):
        return datetime.now()


class TaobaoOrderAdapter(OrderAdapter):
    """Converts Taobao raw order data to unified order dict."""

    def to_unified_order(self, platform_data: Dict[str, Any]) -> Dict[str, Any]:
        trade = platform_data.get("trade", {})
        orders_list = platform_data.get("orders", {}).get("order", [])
        if not orders_list:
            orders_list = trade.get("orders", {}).get("order", [])

        address = trade.get("receiver_address", "")
        if not address:
            address = "".join([
                str(trade.get("receiver_state", "")),
                str(trade.get("receiver_city", "")),
                str(trade.get("receiver_district", "")),
                str(trade.get("receiver_address", "")),
            ])

        status_map = {
            "wait_pay": OrderStatus.WAIT_PAY,
            "wait_ship": OrderStatus.WAIT_SHIP,
            "shipped": OrderStatus.SHIPPED,
            "trade_closed": OrderStatus.TRADE_CLOSED,
            "finished": OrderStatus.FINISHED,
            "WAIT_BUYER_PAY": OrderStatus.WAIT_PAY,
            "WAIT_SELLER_SEND_GOODS": OrderStatus.WAIT_SHIP,
            "WAIT_BUYER_CONFIRM_GOODS": OrderStatus.SHIPPED,
            "TRADE_FINISHED": OrderStatus.FINISHED,
        }

        created = _parse_datetime(trade.get("created"))
        updated = _parse_datetime(trade.get("modified"))

        return {
            "order_id": str(trade.get("tid", "")),
            "platform": "taobao",
            "status": status_map.get(trade.get("status", ""), OrderStatus.WAIT_PAY).value,
            "status_text": _get_status_text(OrderStatus.WAIT_PAY),
            "total_amount": trade.get("total_fee", "0"),
            "pay_amount": trade.get("payment", "0"),
            "freight": "0",
            "receiver": {
                "name": trade.get("receiver_name", ""),
                "phone": trade.get("receiver_phone", "") or trade.get("receiver_mobile", ""),
                "address": address,
            },
            "products": [
                {
                    "product_id": str(order.get("oid", "")),
                    "name": order.get("title", ""),
                    "price": order.get("price", "0"),
                    "quantity": order.get("num", 1),
                }
                for order in orders_list
            ],
            "created_at": created.isoformat() if hasattr(created, "isoformat") else str(created),
            "updated_at": updated.isoformat() if hasattr(updated, "isoformat") else str(updated),
            "external_order_id": str(trade.get("tid")) if trade.get("tid") is not None else None,
        }


def _get_status_text(status: OrderStatus) -> str:
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
