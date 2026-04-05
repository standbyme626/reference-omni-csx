"""Shared utilities for adapters — avoid duplication across platform files."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from app.models import OrderStatus, ShipmentStatus, AfterSaleStatus, ConversationStatus

STATUS_TEXT: dict[OrderStatus, str] = {
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

SHIPMENT_STATUS_TEXT: dict[str, str] = {
    "pending": "待发货", "shipped": "已发货", "in_transit": "运输中",
    "delivered": "已签收", "signed": "已签收", "returned": "已退回",
    "unknown": "未知",
}

AFTER_SALE_STATUS_TEXT: dict[str, str] = {
    "pending": "待处理", "approved": "已同意", "rejected": "已拒绝",
    "refunding": "退款中", "completed": "已完成", "closed": "已关闭",
    "WAIT_SELLER_AGREE": "等待卖家同意", "WAIT_BUYER_RETURN_GOODS": "等待买家退货",
    "WAIT_SELLER_CONFIRM_GOODS": "等待卖家确认收货",
    "SUCCESS": "退款成功", "CLOSED": "退款关闭",
}


def parse_datetime(value: Any) -> datetime:
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


def parse_order_status(status: Any) -> OrderStatus:
    status_map: dict[Any, OrderStatus] = {
        "wait_pay": OrderStatus.WAIT_PAY, "wait_ship": OrderStatus.WAIT_SHIP,
        "shipped": OrderStatus.SHIPPED, "finished": OrderStatus.FINISHED,
        "trade_closed": OrderStatus.TRADE_CLOSED,
        "WAIT_BUYER_PAY": OrderStatus.WAIT_PAY, "WAIT_SELLER_SEND_GOODS": OrderStatus.WAIT_SHIP,
        "WAIT_BUYER_CONFIRM_GOODS": OrderStatus.SHIPPED,
        "TRADE_FINISHED": OrderStatus.FINISHED,
        10: OrderStatus.WAIT_PAY, 20: OrderStatus.PAID,
        30: OrderStatus.WAIT_SHIP, 40: OrderStatus.WAIT_SHIP,
        100: OrderStatus.SHIPPED, 110: OrderStatus.IN_TRANSIT,
        120: OrderStatus.IN_TRANSIT, 200: OrderStatus.FINISHED,
    }
    return status_map.get(status, OrderStatus.WAIT_PAY)


def parse_shipment_status(status: str) -> ShipmentStatus:
    return ShipmentStatus(status) if status in ShipmentStatus else ShipmentStatus.UNKNOWN


def parse_after_sale_status(status: str) -> AfterSaleStatus:
    return AfterSaleStatus(status) if status in AfterSaleStatus else AfterSaleStatus.PENDING
