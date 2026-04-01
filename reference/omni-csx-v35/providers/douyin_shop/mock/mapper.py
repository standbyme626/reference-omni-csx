from datetime import datetime
from provider_sdk.dto.order_dto import OrderDTO, OrderItemDTO, AddressDTO
from provider_sdk.dto.shipment_dto import ShipmentDTO, ShipmentItemDTO
from provider_sdk.dto.after_sale_dto import AfterSaleDTO


def _ts(ts: int) -> str:
    if ts and ts > 0:
        return datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
    return None


_ORDER_STATUS_MAP = {
    10: ("wait_buyer_pay", "待付款"),
    20: ("paid", "已付款"),
    30: ("wait_seller_delivery", "待发货"),
    40: ("shipped", "已发货"),
    50: ("trade_finished", "已完成"),
    90: ("canceled", "已取消"),
}


def map_order(data: dict, platform: str) -> OrderDTO:
    order_amount = data.get("order_amount") or {}
    receiver = data.get("receiver") or {}

    def to_yuan(v):
        return round((v or 0) / 100, 2)

    address = None
    if receiver:
        address = AddressDTO(
            province=receiver.get("province", ""),
            city=receiver.get("city", ""),
            district=receiver.get("district", ""),
            detail=receiver.get("address", ""),
        )

    items = []
    for p in data.get("product_items", []):
        price = to_yuan(p.get("product_price") or p.get("sku_price") or 0)
        qty = p.get("product_count", 1)
        items.append(
            OrderItemDTO(
                sku_id=str(p.get("sku_id", "")),
                sku_name=p.get("product_name", ""),
                quantity=qty,
                price=price,
                sub_total=round(price * qty, 2),
            )
        )

    order_status = data.get("order_status", 0)
    status_code, status_name = _ORDER_STATUS_MAP.get(
        order_status, (str(order_status), data.get("order_status_desc", ""))
    )

    raw = data.get("_raw", {})
    return OrderDTO(
        platform=platform,
        order_id=data.get("order_id", ""),
        status=status_code,
        status_name=status_name,
        create_time=_ts(data.get("create_time", 0)),
        pay_time=_ts(data.get("pay_time", 0)),
        total_amount=to_yuan(order_amount.get("total_amount")),
        freight_amount=to_yuan(order_amount.get("freight_amount")),
        discount_amount=to_yuan(order_amount.get("discount_amount")),
        payment_amount=to_yuan(order_amount.get("actually_pay_amount")),
        buyer_nick=data.get("buyer_message"),
        buyer_phone=receiver.get("phone"),
        receiver_name=receiver.get("name"),
        receiver_phone=receiver.get("phone"),
        receiver_address=address,
        items=items,
        raw_json=raw,
    )


def map_shipment(data: dict, platform: str) -> ShipmentDTO:
    delivery = data.get("delivery_info") or {}
    status_code = delivery.get("delivery_status", 0)
    status_name_map = {
        0: "未发货",
        10: "待揽收",
        20: "揽收中",
        30: "运输中",
        40: "派送中",
        50: "已签收",
        100: "已发货",
    }
    shipments = (
        [
            ShipmentItemDTO(
                shipment_id=data.get("order_id", ""),
                express_company=delivery.get("company_name", ""),
                express_no=delivery.get("tracking_no", ""),
                status=str(status_code),
                status_name=delivery.get(
                    "delivery_status_desc", status_name_map.get(status_code, "")
                ),
                create_time=None,
                estimated_arrival=None,
                trace=[],
            )
        ]
        if delivery.get("company_name") or delivery.get("tracking_no")
        else []
    )
    return ShipmentDTO(
        platform=platform,
        order_id=data.get("order_id", ""),
        shipments=shipments,
        raw_json=data.get("_raw", {}),
    )


_REFUND_STATUS_MAP = {
    10: ("refund_applied", "退款申请中"),
    20: ("refund_approved", "退款通过"),
    30: ("refund_rejected", "退款拒绝"),
    40: ("refund_success", "退款成功"),
    50: ("refund_closed", "退款关闭"),
    0: ("no_refund", "无退款"),
}


def map_refund(data: dict, platform: str) -> AfterSaleDTO:
    refund_amount = data.get("refund_amount", 0)
    refund_status = data.get("refund_status", 0)
    status_code, status_name = _REFUND_STATUS_MAP.get(
        refund_status, (str(refund_status), data.get("refund_status_desc", ""))
    )
    return AfterSaleDTO(
        platform=platform,
        after_sale_id=str(data.get("refund_id", "")),
        order_id=str(data.get("order_id", "")),
        type=str(data.get("refund_type", "")),
        type_name=data.get("refund_type_desc", ""),
        status=status_code,
        status_name=status_name,
        apply_time=_ts(data.get("apply_time", 0)),
        handle_time=_ts(data.get("update_time", 0)),
        apply_amount=round(refund_amount / 100, 2),
        approve_amount=0.0,
        reason=data.get("reason_desc", ""),
        reason_detail=data.get("reason_detail", ""),
        raw_json=data.get("_raw", {}),
    )
