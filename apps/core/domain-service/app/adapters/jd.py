"""JD adapter: Order + Shipment + AfterSale capabilities."""

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


class JDOrderAdapter(OrderAdapter):
    """Converts JD raw order data to unified order dict."""

    def to_unified_order(self, platform_data: Dict[str, Any]) -> Dict[str, Any]:
        # JD-specific API response format
        if "jingdong_order_search_responce" not in platform_data and "order" not in platform_data:
            receiver_info = platform_data.get("receiver", {})
            items = platform_data.get("items", platform_data.get("products", []))
            status_map = {
                "wait_seller_delivery": OrderStatus.WAIT_SHIP,
                "wait_ship": OrderStatus.WAIT_SHIP,
                "paid": OrderStatus.PAID,
                "shipped": OrderStatus.SHIPPED,
                "in_transit": OrderStatus.IN_TRANSIT,
                "delivered": OrderStatus.FINISHED,
                "finished": OrderStatus.FINISHED,
                "completed": OrderStatus.FINISHED,
                "cancelled": OrderStatus.TRADE_CLOSED,
            }

            created = _parse_datetime(platform_data.get("create_time"))
            updated = _parse_datetime(platform_data.get("update_time"))

            return {
                "order_id": str(platform_data.get("order_id", "")),
                "platform": "jd",
                "status": status_map.get(str(platform_data.get("status", "")), OrderStatus.WAIT_PAY).value,
                "status_text": _get_status_text(status_map.get(str(platform_data.get("status", "")), OrderStatus.WAIT_PAY)),
                "total_amount": str(platform_data.get("total_amount", "0")),
                "pay_amount": str(platform_data.get("pay_amount", "0")),
                "freight": str(platform_data.get("freight", "0")),
                "receiver": {
                    "name": receiver_info.get("name", ""),
                    "phone": receiver_info.get("phone", ""),
                    "address": receiver_info.get("address", ""),
                },
                "products": [
                    {
                        "product_id": str(item.get("item_id", "") or item.get("product_id", "")),
                        "name": item.get("name", ""),
                        "price": str(item.get("price", "0")),
                        "quantity": item.get("quantity", 1),
                    }
                    for item in items
                    if isinstance(item, dict)
                ],
                "created_at": created.isoformat() if hasattr(created, "isoformat") else str(created),
                "updated_at": updated.isoformat() if hasattr(updated, "isoformat") else str(updated),
                "external_order_id": platform_data.get("external_order_id"),
            }

        jd_resp = platform_data.get("jingdong_order_search_responce", platform_data.get("order", platform_data))

        if "jingdong_order_search_responce" in platform_data:
            receiver_info = {
                "name": jd_resp.get("buyerFullName", ""),
                "phone": jd_resp.get("buyerMobile", ""),
                "fullAddress": jd_resp.get("buyerFullAddress", ""),
            }
            items = jd_resp.get("product", [])

            products = []
            for item in items:
                if isinstance(item, dict):
                    products.append({
                        "product_id": str(item.get("skuId", "") or item.get("outerSkuId", "")),
                        "name": item.get("skuName", "") or item.get("itemName", ""),
                        "price": _amount_from_minor_units(item.get("jdPrice", item.get("price", 0))),
                        "quantity": item.get("num", 1) or item.get("itemCount", 1),
                    })

            status_map = {
                31000: OrderStatus.WAIT_PAY,
                32000: OrderStatus.PAID,
                33000: OrderStatus.WAIT_SHIP,
                33030: OrderStatus.SHIPPED,
                33040: OrderStatus.SHIPPED,
                33050: OrderStatus.IN_TRANSIT,
                33060: OrderStatus.FINISHED,
                34000: OrderStatus.FINISHED,
                34010: OrderStatus.FINISHED,
                35000: OrderStatus.IN_TRANSIT,
                36000: OrderStatus.IN_TRANSIT,
                37000: OrderStatus.FINISHED,
                90000: OrderStatus.FINISHED,
            }
            order_status = status_map.get(jd_resp.get("orderStatus", 31000), OrderStatus.WAIT_PAY)
            paid_amount = "0.00"
            if order_status != OrderStatus.WAIT_PAY or jd_resp.get("orderPurchaseTime"):
                paid_amount = _amount_from_minor_units(
                    jd_resp.get("orderPayment")
                    or jd_resp.get("orderBuyerPayableMoney")
                    or jd_resp.get("orderAmount")
                )

            created = _parse_datetime(jd_resp.get("orderStartTime"))
            updated = _parse_datetime(jd_resp.get("orderStatusTime"))

            return {
                "order_id": str(jd_resp.get("orderId", "")),
                "platform": "jd",
                "status": order_status.value,
                "status_text": _get_status_text(order_status),
                "total_amount": _amount_from_minor_units(
                    jd_resp.get("orderTotalMoney")
                    or jd_resp.get("orderAmount")
                    or jd_resp.get("orderPayment")
                ),
                "pay_amount": paid_amount,
                "freight": _amount_from_minor_units(jd_resp.get("orderFreightMoney", 0)),
                "receiver": {
                    "name": receiver_info.get("name", ""),
                    "phone": receiver_info.get("phone", ""),
                    "address": receiver_info.get("fullAddress", ""),
                },
                "products": products,
                "created_at": created.isoformat() if hasattr(created, "isoformat") else str(created),
                "updated_at": updated.isoformat() if hasattr(updated, "isoformat") else str(updated),
                "external_order_id": jd_resp.get("externalOrderId"),
            }

        order_data = jd_resp
        receiver_info = order_data.get("receiver", {})
        address_parts = [
            receiver_info.get("province", ""),
            receiver_info.get("city", ""),
            receiver_info.get("district", ""),
            receiver_info.get("address", ""),
        ]
        full_address = receiver_info.get("fullAddress", " ".join(address_parts).strip())

        receiver = {
            "name": receiver_info.get("name", ""),
            "phone": receiver_info.get("phone", ""),
            "address": full_address,
        }

        items = order_data.get("productItems", [])
        products = [
            {
                "product_id": str(item.get("skuId", "") or item.get("itemId", "")),
                "name": item.get("skuName", "") or item.get("itemName", ""),
                "price": _amount_from_minor_units(item.get("jdPrice", item.get("price", 0))),
                "quantity": item.get("num", 1) or item.get("itemCount", 1),
            }
            for item in items
        ]

        status_map = {
            31000: OrderStatus.WAIT_PAY,
            32000: OrderStatus.PAID,
            33000: OrderStatus.WAIT_SHIP,
            34000: OrderStatus.SHIPPED,
            35000: OrderStatus.IN_TRANSIT,
            36000: OrderStatus.IN_TRANSIT,
            37000: OrderStatus.FINISHED,
            "WAIT_BUYER_PAY": OrderStatus.WAIT_PAY,
            "PAID": OrderStatus.PAID,
            "WAIT_SELLER_DELIVERY": OrderStatus.WAIT_SHIP,
            "WAIT_BUYER_CONFIRM": OrderStatus.SHIPPED,
            "TRADE_FINISHED": OrderStatus.FINISHED,
            "CANCELLED": OrderStatus.TRADE_CLOSED,
            "wait_seller_delivery": OrderStatus.WAIT_SHIP,
        }

        order_price_detail = order_data.get("orderPriceDetail", {})
        created = _parse_datetime(order_data.get("createTime") or order_data.get("create_time"))
        updated = _parse_datetime(order_data.get("modifyTime") or order_data.get("update_time"))

        status_enum = status_map.get(order_data.get("orderStatus", order_data.get("status", 31000)), OrderStatus.WAIT_PAY)

        return {
            "order_id": str(order_data.get("orderId", "") or order_data.get("order_id", "")),
            "platform": "jd",
            "status": status_enum.value,
            "status_text": _get_status_text(status_enum),
            "total_amount": _amount_from_minor_units(
                order_price_detail.get("orderAmount")
                or order_data.get("totalPrice")
                or order_data.get("totalAmount")
            ),
            "pay_amount": _amount_from_minor_units(
                order_data.get("paymentAmount")
                or order_data.get("payAmount")
                or order_data.get("actualPrice")
            ),
            "freight": _amount_from_minor_units(
                order_data.get("freightAmount")
                or order_data.get("freight")
                or 0
            ),
            "receiver": receiver,
            "products": products,
            "created_at": created.isoformat() if hasattr(created, "isoformat") else str(created),
            "updated_at": updated.isoformat() if hasattr(updated, "isoformat") else str(updated),
            "external_order_id": order_data.get("externalOrderId"),
        }


class JDShipmentAdapter(ShipmentAdapter):
    """Converts JD raw shipment data to unified shipment dict."""

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
            "platform": "jd",
            "status": shipment_data.get("status", "unknown"),
            "status_text": _shipment_status_text(shipment_data.get("status", "unknown")),
            "company": shipment_data.get("company") or shipment_data.get("company_name"),
            "tracking_no": shipment_data.get("tracking_no") or shipment_data.get("out_sid"),
            "nodes": nodes,
            "created_at": shipment_data.get("created_at") or shipment_data.get("send_time") or now,
            "updated_at": shipment_data.get("updated_at") or now,
        }


class JDAfterSaleAdapter(AfterSaleAdapter):
    """Converts JD raw after-sale data to unified after-sale dict."""

    def to_unified_after_sale(self, platform_data: Dict[str, Any]) -> Dict[str, Any]:
        from datetime import datetime
        refund_data = platform_data.get("refund", platform_data)

        return {
            "after_sale_id": refund_data.get("refund_id") or refund_data.get("after_sale_id", ""),
            "order_id": refund_data.get("order_id", ""),
            "platform": "jd",
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
