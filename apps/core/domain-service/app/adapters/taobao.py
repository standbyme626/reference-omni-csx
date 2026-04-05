"""Taobao adapter: Order-only capability."""
from __future__ import annotations

from typing import Any, Dict

from app.models import Order, OrderStatus, Address, OrderProduct
from app.adapters.utils import parse_datetime, parse_order_status, STATUS_TEXT


class TaobaoOrderAdapter:
    """Converts Taobao raw order data to unified Order model."""

    def to_unified_order(self, platform_data: Dict[str, Any]) -> Order:
        trade = platform_data.get("trade", {})
        orders_list = platform_data.get("orders", {}).get("order", [])
        if not orders_list:
            orders_list = trade.get("orders", {}).get("order", [])

        address_parts = [
            str(trade.get("receiver_state", "")),
            str(trade.get("receiver_city", "")),
            str(trade.get("receiver_district", "")),
            str(trade.get("receiver_address", "")),
        ]

        status = parse_order_status(trade.get("status", ""))
        created = parse_datetime(trade.get("created"))
        updated = parse_datetime(trade.get("modified"))

        return Order(
            order_id=str(trade.get("tid", "")),
            platform="taobao",
            status=status,
            status_text=STATUS_TEXT.get(status, "未知状态"),
            total_amount=str(trade.get("total_fee", "0")),
            pay_amount=str(trade.get("payment", "0")),
            freight="0",
            receiver=Address(name=trade.get("receiver_name", ""),
                             phone=str(trade.get("receiver_phone", "") or trade.get("receiver_mobile", "")),
                             address="".join(address_parts)),
            products=[OrderProduct(product_id=str(o.get("oid", "")), name=o.get("title", ""),
                                   price=str(o.get("price", "0")), quantity=int(o.get("num", 1)))
                      for o in orders_list],
            created_at=created.isoformat(),
            updated_at=updated.isoformat(),
            external_order_id=str(trade["tid"]) if trade.get("tid") is not None else None,
        )
