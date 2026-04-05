"""JD adapter: Order + Shipment + AfterSale capabilities."""
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


def _amount(value: Any) -> str:
    if value in (None, ""):
        return "0"
    if isinstance(value, (int, float)):
        return f"{float(value) / 100:.2f}"
    s = str(value)
    return f"{int(s) / 100:.2f}" if s.isdigit() else s


JD_ORDER_STATUS_MAP: dict[Any, OrderStatus] = {
    31000: OrderStatus.WAIT_PAY, 32000: OrderStatus.PAID,
    33000: OrderStatus.WAIT_SHIP, 33030: OrderStatus.SHIPPED,
    33040: OrderStatus.SHIPPED, 33050: OrderStatus.IN_TRANSIT,
    34000: OrderStatus.FINISHED, 34010: OrderStatus.FINISHED,
    35000: OrderStatus.IN_TRANSIT, 36000: OrderStatus.IN_TRANSIT,
    37000: OrderStatus.FINISHED, 90000: OrderStatus.FINISHED,
    "WAIT_BUYER_PAY": OrderStatus.WAIT_PAY, "PAID": OrderStatus.PAID,
    "WAIT_SELLER_DELIVERY": OrderStatus.WAIT_SHIP, "wait_seller_delivery": OrderStatus.WAIT_SHIP,
    "WAIT_BUYER_CONFIRM": OrderStatus.SHIPPED, "TRADE_FINISHED": OrderStatus.FINISHED,
    "CANCELLED": OrderStatus.TRADE_CLOSED, "cancel": OrderStatus.TRADE_CLOSED,
}


class JDOrderAdapter:
    """Converts JD raw order data to unified Order model."""

    def to_unified_order(self, platform_data: Dict[str, Any]) -> Order:
        # Handle JD-specific API response format
        if "jingdong_order_search_responce" in platform_data:
            return self._parse_jd_api_response(platform_data)
        # Handle generic order dict
        if "order" in platform_data and "jingdong_order_search_responce" not in platform_data:
            return self._parse_generic_order(platform_data)
        # Generic flat dict
        return self._parse_generic_order(platform_data)

    def _parse_jd_api_response(self, platform_data: Dict[str, Any]) -> Order:
        jd_resp = platform_data["jingdong_order_search_responce"]
        rcv = Address(
            name=jd_resp.get("buyerFullName", ""),
            phone=jd_resp.get("buyerMobile", ""),
            address=jd_resp.get("buyerFullAddress", ""),
        )
        items = jd_resp.get("product", [])
        products = [
            OrderProduct(
                product_id=str(item.get("skuId", "") or item.get("outerSkuId", "")),
                name=item.get("skuName", "") or item.get("itemName", ""),
                price=_amount(item.get("jdPrice", item.get("price", 0))),
                quantity=int(item.get("num", 1) or item.get("itemCount", 1)),
            )
            for item in items if isinstance(item, dict)
        ]
        raw_status = jd_resp.get("orderStatus", 31000)
        status = JD_ORDER_STATUS_MAP.get(raw_status, OrderStatus.WAIT_PAY)
        paid = "0.00"
        if status != OrderStatus.WAIT_PAY or jd_resp.get("orderPurchaseTime"):
            paid = _amount(jd_resp.get("orderPayment") or jd_resp.get("orderBuyerPayableMoney") or jd_resp.get("orderAmount"))
        created = parse_datetime(jd_resp.get("orderStartTime"))
        updated = parse_datetime(jd_resp.get("orderStatusTime"))
        return Order(
            order_id=str(jd_resp.get("orderId", "")), platform="jd",
            status=status, status_text=STATUS_TEXT.get(status, "未知状态"),
            total_amount=_amount(jd_resp.get("orderTotalMoney") or jd_resp.get("orderAmount") or jd_resp.get("orderPayment")),
            pay_amount=paid,
            freight=_amount(jd_resp.get("orderFreightMoney", 0)),
            receiver=rcv, products=products,
            created_at=created.isoformat(), updated_at=updated.isoformat(),
            external_order_id=jd_resp.get("externalOrderId"),
        )

    def _parse_generic_order(self, platform_data: Dict[str, Any]) -> Order:
        data = platform_data.get("order", platform_data)
        rcv = data.get("receiver", {})
        address = rcv.get("fullAddress", " ".join(
            str(rcv.get(k, "")) for k in ("province", "city", "district", "address")
        ).strip())
        items = data.get("productItems", data.get("items", []))
        products = [
            OrderProduct(
                product_id=str(item.get("skuId", "") or item.get("itemId", "")),
                name=item.get("skuName", "") or item.get("itemName", ""),
                price=_amount(item.get("jdPrice", item.get("price", 0))),
                quantity=int(item.get("num", 1) or item.get("itemCount", 1)),
            )
            for item in items if isinstance(item, dict)
        ]
        raw_status = data.get("orderStatus", data.get("status", 31000))
        status = JD_ORDER_STATUS_MAP.get(raw_status, OrderStatus.WAIT_PAY)
        price_detail = data.get("orderPriceDetail", {})
        created = parse_datetime(data.get("createTime") or data.get("create_time"))
        updated = parse_datetime(data.get("modifyTime") or data.get("update_time"))
        return Order(
            order_id=str(data.get("orderId", "") or data.get("order_id", "")), platform="jd",
            status=status, status_text=STATUS_TEXT.get(status, "未知状态"),
            total_amount=_amount(price_detail.get("orderAmount") or data.get("totalPrice") or data.get("totalAmount", "0")),
            pay_amount=_amount(data.get("paymentAmount") or data.get("payAmount") or data.get("actualPrice", "0")),
            freight=_amount(data.get("freightAmount") or data.get("freight", 0)),
            receiver=Address(name=rcv.get("name", ""), phone=rcv.get("phone", ""), address=address),
            products=products,
            created_at=created.isoformat(), updated_at=updated.isoformat(),
            external_order_id=data.get("externalOrderId"),
        )


class JDShipmentAdapter:
    """Converts JD raw shipment data to unified Shipment model."""

    def to_unified_shipment(self, platform_data: Dict[str, Any]) -> Shipment:
        data = platform_data.get("shipment", platform_data)
        status = data.get("status", "unknown")
        nodes = self._extract_nodes(data)
        return Shipment(
            order_id=data.get("order_id", ""), platform="jd",
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
        if "nodes" in data:
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
        return nodes


class JDAfterSaleAdapter:
    """Converts JD raw after-sale data to unified AfterSale model."""

    def to_unified_after_sale(self, platform_data: Dict[str, Any]) -> AfterSale:
        data = platform_data.get("refund", platform_data)
        status = data.get("status", "unknown")
        return AfterSale(
            after_sale_id=str(data.get("refund_id") or data.get("after_sale_id", "")),
            order_id=str(data.get("order_id", "")), platform="jd",
            status=parse_after_sale_status(status),
            status_text=AFTER_SALE_STATUS_TEXT.get(status, status),
            reason=str(data.get("reason") or data.get("refund_reason", "")),
            description=str(data.get("description", "")),
            refund_amount=str(data.get("refund_amount") or data.get("refund_fee") or "0"),
            created_at=str(data.get("created_at") or data.get("apply_time", "")),
            updated_at=str(data.get("updated_at") or data.get("refund_time", "")),
        )
