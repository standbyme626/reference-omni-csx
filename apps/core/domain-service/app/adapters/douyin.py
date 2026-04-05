"""Douyin Shop adapter: Order + Shipment + AfterSale capabilities."""

from __future__ import annotations

from typing import Any, Dict

from models.unified import OrderStatus

from .protocols import OrderAdapter, ShipmentAdapter, AfterSaleAdapter


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


def _amount_from_minor_units(value: Any) -> str:
    if value in (None, ""):
        return "0"
    if isinstance(value, (int, float)):
        return f"{float(value) / 100:.2f}"
    string_value = str(value)
    if string_value.isdigit():
        return f"{int(string_value) / 100:.2f}"
    return string_value


class DouyinOrderAdapter(OrderAdapter):
    """Converts Douyin raw order data to unified order dict."""

    def to_unified_order(self, platform_data: Dict[str, Any]) -> Dict[str, Any]:
        order_data = platform_data.get("order", platform_data)

        receiver_info = order_data.get("receiver", {})
        address_parts = [
            receiver_info.get("province", ""),
            receiver_info.get("city", ""),
            receiver_info.get("district", ""),
            receiver_info.get("address", ""),
        ]

        order_amount = order_data.get("order_amount", {})
        status_map = {
            10: OrderStatus.WAIT_PAY,
            20: OrderStatus.PAID,
            30: OrderStatus.WAIT_SHIP,
            40: OrderStatus.WAIT_SHIP,
            100: OrderStatus.SHIPPED,
            110: OrderStatus.IN_TRANSIT,
            120: OrderStatus.IN_TRANSIT,
            200: OrderStatus.FINISHED,
            "wait_pay": OrderStatus.WAIT_PAY,
            "paid": OrderStatus.PAID,
            "wait_ship": OrderStatus.WAIT_SHIP,
            "shipped": OrderStatus.SHIPPED,
            "in_transit": OrderStatus.IN_TRANSIT,
            "finished": OrderStatus.FINISHED,
        }
        raw_status = order_data.get("order_status", order_data.get("status", 10))
        status_enum = status_map.get(raw_status, OrderStatus.WAIT_PAY)

        created = _parse_datetime(order_data.get("create_time"))
        updated = _parse_datetime(order_data.get("update_time"))

        product_items = order_data.get("product_items", order_data.get("products", []))
        products = [
            {
                "product_id": p.get("product_id", ""),
                "name": p.get("product_name", "") or p.get("name", ""),
                "price": _amount_from_minor_units(p.get("product_price", p.get("price", "0"))),
                "quantity": p.get("product_count", 1) or p.get("num", 1),
            }
            for p in product_items
        ]

        return {
            "order_id": str(order_data.get("order_id", "")),
            "platform": "douyin_shop",
            "status": status_enum.value,
            "status_text": _get_status_text(status_enum),
            "total_amount": _amount_from_minor_units(
                order_amount.get("total_amount", order_data.get("total_amount", "0"))
            ),
            "pay_amount": _amount_from_minor_units(
                order_amount.get("pay_amount", order_data.get("pay_amount", "0"))
            ),
            "freight": _amount_from_minor_units(
                order_amount.get("freight_amount", order_data.get("freight", "0"))
            ),
            "receiver": {
                "name": receiver_info.get("name", ""),
                "phone": receiver_info.get("phone", "") or receiver_info.get("mobile", ""),
                "address": receiver_info.get("address", "") or "".join(str(part) for part in address_parts),
            },
            "products": products,
            "created_at": created.isoformat() if hasattr(created, "isoformat") else str(created),
            "updated_at": updated.isoformat() if hasattr(updated, "isoformat") else str(updated),
            "external_order_id": order_data.get("external_order_id"),
        }


class DouyinShipmentAdapter(ShipmentAdapter):
    """Converts Douyin raw shipment data to unified shipment dict."""

    def to_unified_shipment(self, platform_data: Dict[str, Any]) -> Dict[str, Any]:
        from datetime import datetime
        shipment_data = platform_data.get("shipment", platform_data)

        nodes = []
        if "nodes" in shipment_data:
            nodes = [
                {
                    "node": n.get("node") or n.get("status", ""),
                    "time": n.get("time") or n.get("timestamp"),
                    "description": n.get("description") or n.get("desc"),
                }
                for n in shipment_data.get("nodes", [])
            ]
        elif "trace_list" in shipment_data:
            for trace in shipment_data.get("trace_list", []):
                nodes.append({
                    "node": trace.get("action", ""),
                    "time": trace.get("time"),
                    "description": trace.get("desc", ""),
                })

        now = datetime.now().isoformat()
        return {
            "shipment_id": shipment_data.get("shipment_id") or shipment_data.get("sid", ""),
            "order_id": shipment_data.get("order_id", ""),
            "platform": "douyin_shop",
            "status": shipment_data.get("status", "unknown"),
            "status_text": _shipment_status_text(shipment_data.get("status", "unknown")),
            "company": shipment_data.get("company") or shipment_data.get("company_name"),
            "tracking_no": shipment_data.get("tracking_no") or shipment_data.get("out_sid"),
            "nodes": nodes,
            "created_at": shipment_data.get("created_at") or shipment_data.get("send_time") or now,
            "updated_at": shipment_data.get("updated_at") or now,
        }


class DouyinAfterSaleAdapter(AfterSaleAdapter):
    """Converts Douyin raw after-sale data to unified after-sale dict."""

    def to_unified_after_sale(self, platform_data: Dict[str, Any]) -> Dict[str, Any]:
        from datetime import datetime
        refund_data = platform_data.get("refund", platform_data)

        return {
            "after_sale_id": refund_data.get("refund_id") or refund_data.get("after_sale_id", ""),
            "order_id": refund_data.get("order_id", ""),
            "platform": "douyin_shop",
            "status": refund_data.get("status", "unknown"),
            "status_text": _refund_status_text(refund_data.get("status", "unknown")),
            "type": refund_data.get("refund_type", "refund"),
            "reason": refund_data.get("reason") or refund_data.get("refund_reason", ""),
            "description": refund_data.get("description"),
            "refund_amount": str(refund_data.get("refund_amount") or refund_data.get("refund_fee") or "0"),
            "created_at": refund_data.get("created_at") or refund_data.get("apply_time") or datetime.now().isoformat(),
            "updated_at": refund_data.get("updated_at") or refund_data.get("refund_time") or datetime.now().isoformat(),
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


def _shipment_status_text(status: str) -> str:
    status_map = {
        "pending": "待发货",
        "shipped": "已发货",
        "in_transit": "运输中",
        "delivered": "已签收",
        "signed": "已签收",
        "returned": "已退回",
        "unknown": "未知",
    }
    return status_map.get(status, status)


def _refund_status_text(status: str) -> str:
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
