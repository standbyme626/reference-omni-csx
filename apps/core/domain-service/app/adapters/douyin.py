"""Douyin Shop adapter: Order + Shipment + AfterSale capabilities."""
from __future__ import annotations

from typing import Any, Dict

from app.models import (
    Order, OrderProduct, Address, OrderStatus,
    Shipment, ShipmentNode, ShipmentStatus,
    AfterSale, AfterSaleStatus,
)
from app.adapters.utils import (
    parse_datetime, parse_order_status, parse_shipment_status, parse_after_sale_status,
    STATUS_TEXT, SHIPMENT_STATUS_TEXT, AFTER_SALE_STATUS_TEXT,
)


def _amount(value: Any) -> str:
    if value in (None, ""):
        return "0"
    if isinstance(value, (int, float)):
        return f"{float(value) / 100:.2f}"
    s = str(value)
    return f"{int(s) / 100:.2f}" if s.isdigit() else s


class DouyinOrderAdapter:
    """Converts Douyin raw order data to unified Order model."""

    def to_unified_order(self, platform_data: Dict[str, Any]) -> Order:
        data = platform_data.get("order", platform_data)
        rcv = data.get("receiver", {})
        amount = data.get("order_amount", {})
        status = parse_order_status(data.get("order_status", data.get("status", 10)))
        created = parse_datetime(data.get("create_time"))
        updated = parse_datetime(data.get("update_time"))

        return Order(
            order_id=str(data.get("order_id", "")), platform="douyin_shop",
            status=status, status_text=STATUS_TEXT.get(status, "未知状态"),
            total_amount=_amount(amount.get("total_amount", data.get("total_amount", "0"))),
            pay_amount=_amount(amount.get("pay_amount", data.get("pay_amount", "0"))),
            freight=_amount(amount.get("freight_amount", data.get("freight", "0"))),
            receiver=Address(
                name=rcv.get("name", ""),
                phone=str(rcv.get("phone", "") or rcv.get("mobile", "")),
                address=rcv.get("address", "") or "".join(
                    str(rcv.get(k, "")) for k in ("province", "city", "district", "address")
                ),
            ),
            products=[
                OrderProduct(
                    product_id=p.get("product_id", "") or p.get("product_id_str", ""),
                    name=p.get("product_name", "") or p.get("name", ""),
                    price=_amount(p.get("product_price", p.get("price", "0"))),
                    quantity=int(p.get("product_count", 1) or p.get("num", 1)),
                )
                for p in data.get("product_items", data.get("products", []))
            ],
            created_at=created.isoformat(), updated_at=updated.isoformat(),
            external_order_id=data.get("external_order_id"),
        )


class DouyinShipmentAdapter:
    """Converts Douyin raw shipment data to unified Shipment model."""

    def to_unified_shipment(self, platform_data: Dict[str, Any]) -> Shipment:
        data = platform_data.get("shipment", platform_data)
        status = data.get("status", "unknown")

        nodes_raw = data.get("nodes", [])
        if "trace_list" in data:
            nodes_raw = data["trace_list"]

        nodes = []
        if "nodes" in platform_data.get("shipment", {}):
            for n in data.get("nodes", []):
                nodes.append(ShipmentNode(
                    node=str(n.get("node") or n.get("status", "")),
                    time=str(n.get("time") or n.get("timestamp", "")),
                    description=str(n.get("description") or n.get("desc", "")),
                ))
        elif "trace_list" in data:
            for t in data.get("trace_list", []):
                nodes.append(ShipmentNode(
                    node=str(t.get("action", "")),
                    time=str(t.get("time", "")),
                    description=str(t.get("desc", "")),
                ))

        return Shipment(
            order_id=data.get("order_id", ""), platform="douyin_shop",
            status=parse_shipment_status(status),
            status_text=SHIPMENT_STATUS_TEXT.get(status, status),
            company=str(data.get("company") or data.get("company_name")),
            tracking_no=str(data.get("tracking_no") or data.get("out_sid")),
            nodes=nodes,
            created_at=str(data.get("created_at") or data.get("send_time", "")),
            updated_at=str(data.get("updated_at", "")),
        )


class DouyinAfterSaleAdapter:
    """Converts Douyin raw after-sale data to unified AfterSale model."""

    def to_unified_after_sale(self, platform_data: Dict[str, Any]) -> AfterSale:
        data = platform_data.get("refund", platform_data)
        status = data.get("status", "unknown")
        return AfterSale(
            after_sale_id=str(data.get("refund_id") or data.get("after_sale_id", "")),
            order_id=str(data.get("order_id", "")), platform="douyin_shop",
            status=parse_after_sale_status(status),
            status_text=AFTER_SALE_STATUS_TEXT.get(status, status),
            reason=str(data.get("reason") or data.get("refund_reason", "")),
            description=str(data.get("description", "")),
            refund_amount=str(data.get("refund_amount") or data.get("refund_fee") or "0"),
            created_at=str(data.get("created_at") or data.get("apply_time", "")),
            updated_at=str(data.get("updated_at") or data.get("refund_time", "")),
        )
