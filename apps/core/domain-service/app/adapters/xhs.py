"""XHS adapter: Order + Shipment + AfterSale capabilities."""
from __future__ import annotations

from typing import Any, Dict

from app.models import (
    Order, OrderProduct, Address, OrderStatus,
    Shipment, ShipmentNode, AfterSale, AfterSaleStatus,
)
from app.adapters.utils import (
    parse_datetime, parse_order_status, parse_shipment_status, parse_after_sale_status,
    STATUS_TEXT, SHIPMENT_STATUS_TEXT, AFTER_SALE_STATUS_TEXT,
)

XHS_ORDER_STATUS_MAP: dict[str, OrderStatus] = {
    "created": OrderStatus.WAIT_PAY, "pending": OrderStatus.WAIT_PAY,
    "paid": OrderStatus.PAID, "delivering": OrderStatus.IN_TRANSIT,
    "delivered": OrderStatus.FINISHED, "completed": OrderStatus.FINISHED,
    "cancelled": OrderStatus.TRADE_CLOSED,
}


class XHSOrderAdapter:
    def to_unified_order(self, platform_data: Dict[str, Any]) -> Order:
        data = platform_data.get("order", platform_data)
        rcv = data.get("receiver", {})
        address = rcv.get("fullAddress", " ".join(
            str(rcv.get(k, "")) for k in ("province", "city", "district", "address")
        ).strip())
        items = data.get("productItems", data.get("items", []))
        raw_status = data.get("orderStatus", data.get("status", "created"))
        status = XHS_ORDER_STATUS_MAP.get(raw_status, OrderStatus.WAIT_PAY)
        created = parse_datetime(data.get("createTime") or data.get("create_time"))
        updated = parse_datetime(data.get("updateTime") or data.get("update_time") or data.get("createTime"))
        return Order(
            order_id=str(data.get("orderId", "") or data.get("order_id", "")), platform="xhs",
            status=status, status_text=STATUS_TEXT.get(status, "未知状态"),
            total_amount=_amount(data.get("totalAmount", data.get("total_amount", 0))),
            pay_amount=_amount(data.get("payAmount", data.get("pay_amount", 0))),
            freight=_amount(data.get("postAmount", data.get("freight", 0))),
            receiver=Address(name=rcv.get("name", ""), phone=rcv.get("phone", ""), address=address),
            products=[
                OrderProduct(
                    product_id=str(item.get("itemId", "") or item.get("skuId", "") or item.get("item_id", "")),
                    name=item.get("itemName", "") or item.get("skuName", ""),
                    price=_amount(item.get("price", 0)),
                    quantity=int(item.get("itemCount", item.get("quantity", 1)) or item.get("num", 1)),
                )
                for item in items
            ],
            created_at=created.isoformat(), updated_at=updated.isoformat(),
            external_order_id=data.get("externalOrderId"),
        )


class XHSShipmentAdapter:
    def to_unified_shipment(self, platform_data: Dict[str, Any]) -> Shipment:
        data = platform_data.get("shipment", platform_data)
        status = data.get("status", "unknown")
        nodes = self._extract_nodes(data)
        return Shipment(
            order_id=data.get("order_id", ""), platform="xhs",
            status=parse_shipment_status(status),
            status_text=SHIPMENT_STATUS_TEXT.get(status, status),
            company=str(data.get("company") or data.get("company_name")),
            tracking_no=str(data.get("tracking_no") or data.get("out_sid")),
            nodes=nodes,
            created_at=str(data.get("created_at") or data.get("send_time", "")),
            updated_at=str(data.get("updated_at", "")),
        )

    @staticmethod
    def _extract_nodes(data: Dict[str, Any]) -> list[ShipmentNode]:
        nodes: list[ShipmentNode] = []
        for n in data.get("nodes", []):
            nodes.append(ShipmentNode(
                node=str(n.get("node") or n.get("status", "")),
                time=str(n.get("time") or n.get("timestamp", "")),
                description=str(n.get("description") or n.get("desc", "")),
            ))
        for t in data.get("trace_list", []):
            nodes.append(ShipmentNode(
                node=str(t.get("action", "")), time=str(t.get("time", "")),
                description=str(t.get("desc", "")),
            ))
        return nodes


class XHSAfterSaleAdapter:
    def to_unified_after_sale(self, platform_data: Dict[str, Any]) -> AfterSale:
        data = platform_data.get("refund", platform_data)
        status = data.get("status", "unknown")
        return AfterSale(
            after_sale_id=str(data.get("refund_id") or data.get("after_sale_id", "")),
            order_id=str(data.get("order_id", "")), platform="xhs",
            status=parse_after_sale_status(status),
            status_text=AFTER_SALE_STATUS_TEXT.get(status, status),
            reason=str(data.get("reason") or data.get("refund_reason", "")),
            description=str(data.get("description", "")),
            refund_amount=str(data.get("refund_amount") or data.get("refund_fee") or "0"),
            created_at=str(data.get("created_at") or data.get("apply_time", "")),
            updated_at=str(data.get("updated_at") or data.get("refund_time", "")),
        )


def _amount(value: Any) -> str:
    if value in (None, ""):
        return "0"
    if isinstance(value, (int, float)):
        return f"{float(value) / 100:.2f}"
    s = str(value)
    return f"{int(s) / 100:.2f}" if s.isdigit() else s
