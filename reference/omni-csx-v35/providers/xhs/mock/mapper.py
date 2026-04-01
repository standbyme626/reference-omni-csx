"""Mapper for XHS platform fixture data to Provider SDK DTOs."""

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
        items.append(
            OrderItemDTO(
                sku_id=str(item.get("skuId", "")),
                sku_name=item.get("itemName") or item.get("skuName") or "",
                quantity=item.get("itemCount", 0),
                price=item.get("price", 0) / 100.0,
                sub_total=item.get("actuallyPayAmount", 0) / 100.0,
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
        status=order.get("orderStatus", ""),
        status_name=order.get("statusDesc", ""),
        create_time=create_time,
        pay_time=pay_time,
        total_amount=order.get("totalAmount", 0) / 100.0,
        freight_amount=order.get("postAmount", 0) / 100.0,
        discount_amount=order.get("discountAmount", 0) / 100.0,
        payment_amount=order.get("payAmount", order.get("actuallyPayAmount", 0))
        / 100.0,
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

    delivery_time = logistics.get("deliveryTime")
    if isinstance(delivery_time, int):
        from datetime import datetime

        delivery_time = datetime.utcfromtimestamp(delivery_time).isoformat() + "Z"

    shipments = (
        [
            ShipmentItemDTO(
                shipment_id=str(order.get("orderId", "")),
                express_company=logistics.get(
                    "logisticsCompany", logistics.get("company", "")
                ),
                express_no=logistics.get("trackingNo", ""),
                status=logistics.get("status", logistics.get("deliveryStatus", "")),
                status_name="运输中",
                create_time=delivery_time,
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


def map_after_sale(data: dict, platform: str) -> AfterSaleDTO:
    refund = data.get("response", {}).get("refund", data.get("refund", data))
    apply_time = refund.get("apply_time")
    if isinstance(apply_time, int):
        from datetime import datetime

        apply_time = datetime.utcfromtimestamp(apply_time).isoformat() + "Z"

    handle_time = refund.get("update_time")
    if isinstance(handle_time, int):
        from datetime import datetime

        handle_time = datetime.utcfromtimestamp(handle_time).isoformat() + "Z"

    return AfterSaleDTO(
        platform=platform,
        after_sale_id=str(refund.get("refund_id", "")),
        order_id=str(refund.get("order_id", "")),
        type=str(refund.get("refund_type", "")),
        type_name=refund.get("refund_type_desc", ""),
        status=refund.get("status", ""),
        status_name=refund.get("statusDesc", ""),
        apply_time=apply_time,
        handle_time=handle_time,
        apply_amount=refund.get("refund_amount", 0) / 100.0,
        approve_amount=0.0,
        reason=refund.get("reason_desc", ""),
        reason_detail=refund.get("reason_detail", ""),
        raw_json=data.get("raw_json", {}),
    )
