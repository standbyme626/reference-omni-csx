"""Mapper for Taobao platform fixture data to Provider SDK DTOs."""

from provider_sdk.dto.order_dto import OrderDTO, OrderItemDTO, AddressDTO
from provider_sdk.dto.shipment_dto import ShipmentDTO, ShipmentItemDTO
from provider_sdk.dto.after_sale_dto import AfterSaleDTO


def map_order(data: dict, platform: str) -> OrderDTO:
    response = data.get("response", data)
    trade = response.get("trade", response)
    receiver_name = trade.get("receiver_name", "")
    receiver_phone = trade.get("receiver_mobile", trade.get("receiver_phone", ""))

    address = None
    if receiver_name or trade.get("receiver_state"):
        address = AddressDTO(
            province=trade.get("receiver_state", ""),
            city=trade.get("receiver_city", ""),
            district=trade.get("receiver_district", ""),
            detail=trade.get("receiver_address", ""),
        )

    items = []
    orders = trade.get("orders", {})
    order_list = orders.get("order", []) if isinstance(orders, dict) else orders
    for item in order_list:
        items.append(
            OrderItemDTO(
                sku_id=str(item.get("sku_id", "")),
                sku_name=item.get("title") or item.get("sku_properties_name") or "",
                quantity=item.get("num", 0),
                price=float(item.get("price", 0)),
                sub_total=float(item.get("payment", 0)),
            )
        )

    return OrderDTO(
        platform=platform,
        order_id=str(trade.get("tid", "")),
        status=trade.get("status", ""),
        status_name=trade.get("status", ""),
        create_time=trade.get("created"),
        pay_time=trade.get("pay_time"),
        total_amount=float(trade.get("total_fee", 0)),
        freight_amount=float(trade.get("post_fee", 0)),
        discount_amount=float(trade.get("discount_fee", 0)),
        payment_amount=float(trade.get("payment", 0)),
        buyer_nick=trade.get("buyer_nick"),
        buyer_phone="",
        receiver_name=receiver_name,
        receiver_phone=receiver_phone,
        receiver_address=address,
        items=items,
        raw_json=data.get("raw_json", {}),
    )


def map_shipment(data: dict, platform: str) -> ShipmentDTO:
    response = data.get("response", data)
    trade = response.get("trade", response)
    shipments = []
    orders = trade.get("orders", {})
    order_list = orders.get("order", []) if isinstance(orders, dict) else orders
    for item in order_list:
        if item.get("invoice_no") or item.get("logistics_company"):
            shipments.append(
                ShipmentItemDTO(
                    shipment_id=str(item.get("oid", "")),
                    express_company=item.get("logistics_company", ""),
                    express_no=item.get("invoice_no", ""),
                    status="shipped",
                    status_name="已发货",
                    create_time=trade.get("consign_time"),
                    estimated_arrival=None,
                    trace=[],
                )
            )
    if not shipments:
        shipments.append(
            ShipmentItemDTO(
                shipment_id="",
                express_company="",
                express_no="",
                status="not_shipped",
                status_name="未发货",
                create_time=None,
                estimated_arrival=None,
                trace=[],
            )
        )
    return ShipmentDTO(
        platform=platform,
        order_id=str(trade.get("tid", "")),
        shipments=shipments,
        raw_json=data.get("raw_json", {}),
    )


def map_after_sale(data: dict, platform: str) -> AfterSaleDTO:
    response = data.get("response", data)
    refund = response.get("refund", response)
    return AfterSaleDTO(
        platform=platform,
        after_sale_id=str(refund.get("refund_id", refund.get("id", ""))),
        order_id=str(refund.get("tid", refund.get("oid", ""))),
        type=refund.get("type", ""),
        type_name=refund.get("type", ""),
        status=refund.get("status", ""),
        status_name=refund.get("status", ""),
        apply_time=refund.get("created"),
        handle_time=refund.get("modified"),
        apply_amount=float(refund.get("refund_fee", 0)),
        approve_amount=0.0,
        reason=refund.get("reason", ""),
        reason_detail=refund.get("description", ""),
        raw_json=data.get("raw_json", {}),
    )
