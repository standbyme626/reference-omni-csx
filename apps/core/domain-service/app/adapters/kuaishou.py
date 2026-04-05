"""Kuaishou adapter: Order + Shipment + AfterSale capabilities."""

from __future__ import annotations

from typing import Any

from app.models import (
    Order,
    OrderStatus,
    OrderProduct,
    Address,
    Shipment,
    ShipmentNode,
    ShipmentStatus,
    AfterSale,
    AfterSaleStatus,
)
from app.adapters.utils import (
    parse_datetime,
    parse_shipment_status,
    parse_after_sale_status,
    SHIPMENT_STATUS_TEXT,
    AFTER_SALE_STATUS_TEXT,
    STATUS_TEXT,
)


def _amount(value: Any) -> str:
    """Convert minor-units amount (cents) to string with 2 decimal places."""
    if value in (None, ""):
        return "0"
    if isinstance(value, (int, float)):
        return f"{float(value) / 100:.2f}"
    string_value = str(value)
    if string_value.isdigit():
        return f"{int(string_value) / 100:.2f}"
    return string_value


_KS_ORDER_STATUS_MAP: dict[Any, OrderStatus] = {
    # String status codes
    "CREATED": OrderStatus.WAIT_PAY,
    "PAID": OrderStatus.PAID,
    "WAIT_SEND": OrderStatus.WAIT_SHIP,
    "SEND": OrderStatus.SHIPPED,
    "DELIVERED": OrderStatus.FINISHED,
    "FINISHED": OrderStatus.FINISHED,
    "CLOSED": OrderStatus.TRADE_CLOSED,
    "REFUNDING": OrderStatus.REFUNDING,
    # Numeric status codes (legacy)
    1: OrderStatus.WAIT_PAY,
    2: OrderStatus.PAID,
    3: OrderStatus.WAIT_SHIP,
    4: OrderStatus.SHIPPED,
    5: OrderStatus.IN_TRANSIT,
    6: OrderStatus.FINISHED,
    # Additional string fallbacks
    "pending": OrderStatus.WAIT_PAY,
    "paid": OrderStatus.PAID,
    "delivering": OrderStatus.IN_TRANSIT,
    "delivered": OrderStatus.FINISHED,
    "cancelled": OrderStatus.TRADE_CLOSED,
}


def _parse_order_status(raw: Any) -> OrderStatus:
    return _KS_ORDER_STATUS_MAP.get(raw, OrderStatus.WAIT_PAY)


class KuaishouOrderAdapter:
    """Converts Kuaishou raw order data to unified Order model."""

    def to_unified_order(self, platform_data: dict[str, Any]) -> Order:
        order_data = platform_data.get("order", platform_data)

        receiver_info = order_data.get("receiver", {})
        receiver = Address(
            name=receiver_info.get("name", ""),
            phone=receiver_info.get("phone", ""),
            province=receiver_info.get("province"),
            city=receiver_info.get("city"),
            district=receiver_info.get("district"),
            address=receiver_info.get("address", "")
            or " ".join(
                p
                for p in [
                    receiver_info.get("province", ""),
                    receiver_info.get("city", ""),
                    receiver_info.get("district", ""),
                    receiver_info.get("address", ""),
                ]
                if p
            ).strip(),
        )

        product_items = order_data.get("orderItemVOs") or order_data.get("productItems") or order_data.get("products", [])
        products = [
            OrderProduct(
                product_id=str(item.get("itemId", "") or item.get("product_id", "")),
                name=item.get("itemName", "") or item.get("name", ""),
                price=_amount(item.get("price", 0)),
                quantity=item.get("itemCount", item.get("quantity", 1)),
            )
            for item in product_items
        ]

        raw_status = order_data.get("orderStatus", order_data.get("status", 1))
        status = _parse_order_status(raw_status)
        status_text = STATUS_TEXT.get(status, "未知状态")

        created = parse_datetime(order_data.get("createTime") or order_data.get("create_time"))
        updated = parse_datetime(
            order_data.get("updateTime") or order_data.get("update_time") or order_data.get("createTime")
        )

        return Order(
            order_id=str(order_data.get("orderId", "") or order_data.get("order_id", "")),
            platform="kuaishou",
            status=status,
            status_text=status_text,
            total_amount=_amount(order_data.get("totalAmount", order_data.get("total_amount", 0))),
            pay_amount=_amount(order_data.get("payAmount", order_data.get("pay_amount", 0))),
            freight=_amount(order_data.get("freightAmount", order_data.get("freight", 0))),
            receiver=receiver,
            products=products,
            created_at=created.isoformat() if hasattr(created, "isoformat") else str(created),
            updated_at=updated.isoformat() if hasattr(updated, "isoformat") else str(updated),
            external_order_id=order_data.get("externalOrderId"),
        )


class KuaishouShipmentAdapter:
    """Converts Kuaishou raw shipment data to unified Shipment model."""

    def to_unified_shipment(self, platform_data: dict[str, Any]) -> Shipment:
        from datetime import datetime

        shipment_data = platform_data.get("shipment", platform_data)

        nodes: list[ShipmentNode] = []
        if "nodes" in shipment_data:
            nodes = [
                ShipmentNode(
                    node=n.get("node") or n.get("status", ""),
                    time=n.get("time") or n.get("timestamp") or "",
                    description=n.get("description") or n.get("desc", ""),
                )
                for n in shipment_data.get("nodes", [])
            ]
        elif "trace_list" in shipment_data:
            nodes = [
                ShipmentNode(
                    node=trace.get("action", ""),
                    time=trace.get("time", ""),
                    description=trace.get("desc", ""),
                )
                for trace in shipment_data.get("trace_list", [])
            ]

        raw_status = shipment_data.get("status", "unknown")
        status = parse_shipment_status(raw_status)
        status_text = SHIPMENT_STATUS_TEXT.get(raw_status, raw_status)
        now = datetime.now().isoformat()

        return Shipment(
            shipment_id=shipment_data.get("shipment_id") or shipment_data.get("sid", ""),
            order_id=shipment_data.get("order_id", ""),
            platform="kuaishou",
            status=status,
            status_text=status_text,
            company=shipment_data.get("company") or shipment_data.get("company_name"),
            tracking_no=shipment_data.get("tracking_no") or shipment_data.get("out_sid"),
            nodes=nodes,
            created_at=shipment_data.get("created_at") or shipment_data.get("send_time") or now,
            updated_at=shipment_data.get("updated_at") or now,
        )


class KuaishouAfterSaleAdapter:
    """Converts Kuaishou raw after-sale data to unified AfterSale model."""

    def to_unified_after_sale(self, platform_data: dict[str, Any]) -> AfterSale:
        from datetime import datetime

        refund_data = platform_data.get("refund", platform_data)

        raw_status = refund_data.get("status", "pending")
        status = parse_after_sale_status(raw_status)
        status_text = AFTER_SALE_STATUS_TEXT.get(raw_status, raw_status)

        return AfterSale(
            after_sale_id=refund_data.get("refund_id") or refund_data.get("after_sale_id", ""),
            order_id=refund_data.get("order_id", ""),
            platform="kuaishou",
            status=status,
            status_text=status_text,
            reason=refund_data.get("reason") or refund_data.get("refund_reason", ""),
            description=refund_data.get("description") or "",
            refund_amount=_amount(refund_data.get("refund_amount") or refund_data.get("refund_fee") or 0),
            created_at=refund_data.get("created_at") or refund_data.get("apply_time") or datetime.now().isoformat(),
            updated_at=refund_data.get("updated_at") or refund_data.get("refund_time") or datetime.now().isoformat(),
        )
