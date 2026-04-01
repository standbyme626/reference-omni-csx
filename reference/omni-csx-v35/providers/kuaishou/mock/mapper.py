"""Mapper for Kuaishou platform fixture data to Provider SDK DTOs."""

from provider_sdk.dto.order_dto import OrderDTO, OrderItemDTO, AddressDTO
from provider_sdk.dto.shipment_dto import ShipmentDTO, ShipmentItemDTO, ShipmentTraceDTO
from provider_sdk.dto.after_sale_dto import AfterSaleDTO


def map_order(data: dict, platform: str) -> OrderDTO:
    order = data.get("response", {}).get("order", data.get("order", data))
    receiver = order.get("receiver", {})

    address = None
    if receiver:
        address = AddressDTO(
            province=receiver.get("province", ""),
            city=receiver.get("city", ""),
            district=receiver.get("district", ""),
            detail=receiver.get("address", ""),
        )

    items = []
    for item in order.get("productItems", []):
        price = item.get("price", 0) / 100.0
        qty = item.get("itemCount", 0)
        sub = item.get("sub_total", price * qty)

        items.append(
            OrderItemDTO(
                sku_id=str(item.get("skuId", "")),
                sku_name=item.get("skuName", item.get("itemName", "")),
                quantity=qty,
                price=price,
                sub_total=sub,
            )
        )

    create_time = order.get("createTime")
    if isinstance(create_time, int):
        from datetime import datetime

        create_time = datetime.utcfromtimestamp(create_time).isoformat() + "Z"

    pay_time = order.get("payTime")
    if isinstance(pay_time, int):
        from datetime import datetime

        pay_time = datetime.utcfromtimestamp(pay_time).isoformat() + "Z"

    return OrderDTO(
        platform=platform,
        order_id=str(order.get("orderId", "")),
        status=str(order.get("orderStatus", "")),
        status_name=order.get("statusDesc", ""),
        create_time=create_time,
        pay_time=pay_time,
        total_amount=order.get("totalAmount", 0) / 100.0,
        freight_amount=order.get("freightAmount", 0) / 100.0,
        discount_amount=order.get("discountAmount", 0) / 100.0,
        payment_amount=order.get("payAmount", 0) / 100.0,
        buyer_nick=order.get("buyerNick", ""),
        buyer_phone="",
        receiver_name=receiver.get("name", ""),
        receiver_phone=receiver.get("phone", ""),
        receiver_address=address,
        items=items,
        raw_json=data.get("raw_json", {}),
    )


def map_shipment(data: dict, platform: str) -> ShipmentDTO:
    order = data.get("response", {}).get("order", data.get("order", data))
    logistics = order.get("logistics", {})

    shipments = (
        [
            ShipmentItemDTO(
                shipment_id=str(order.get("orderId", "")),
                express_company=logistics.get(
                    "company", logistics.get("logisticsCompany", "")
                ),
                express_no=logistics.get("trackingNo", ""),
                status=logistics.get("status", ""),
                status_name="已发货",
                create_time=None,
                estimated_arrival=None,
                trace=[],
            )
        ]
        if logistics
        else []
    )

    return ShipmentDTO(
        platform=platform,
        order_id=str(order.get("orderId", "")),
        shipments=shipments,
        raw_json=data.get("raw_json", {}),
    )


_REFUND_STATUS_MAP = {
    0: ("no_refund", "无退款"),
    1: ("refund_applied", "退款申请中"),
    2: ("refund_approved", "退款通过"),
    3: ("refund_rejecting", "拒绝中"),
    4: ("refund_rejected", "退款拒绝"),
    5: ("refund_success", "退款成功"),
    9: ("refund_closed", "退款关闭"),
}


def map_after_sale(data: dict, platform: str) -> AfterSaleDTO:
    order = data.get("response", {}).get("order", data.get("order", data))
    refund = order.get("refundInfo", {})
    apply_time = refund.get("applyTime")
    if isinstance(apply_time, int):
        from datetime import datetime

        apply_time = datetime.utcfromtimestamp(apply_time).isoformat() + "Z"

    handle_time = refund.get("rejectTime")
    if isinstance(handle_time, int):
        from datetime import datetime

        handle_time = datetime.utcfromtimestamp(handle_time).isoformat() + "Z"

    refund_status = refund.get("refundStatus", 0)
    status_code, status_name = _REFUND_STATUS_MAP.get(
        refund_status, (str(refund_status), refund.get("refundStatusDesc", ""))
    )

    return AfterSaleDTO(
        platform=platform,
        after_sale_id=str(refund.get("refundId", "")),
        order_id=str(order.get("orderId", "")),
        type="",
        type_name="",
        status=status_code,
        status_name=status_name,
        apply_time=apply_time,
        handle_time=handle_time,
        apply_amount=round(refund.get("refundAmount", 0) / 100, 2),
        approve_amount=0.0,
        reason=refund.get("refundReason", ""),
        reason_detail=refund.get("rejectReason", ""),
        raw_json=data.get("_raw", {}),
    )
