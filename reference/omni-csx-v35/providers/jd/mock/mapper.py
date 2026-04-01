from provider_sdk.dto.order_dto import OrderDTO, OrderItemDTO, AddressDTO
from provider_sdk.dto.shipment_dto import ShipmentDTO, ShipmentItemDTO, ShipmentTraceDTO
from provider_sdk.dto.after_sale_dto import AfterSaleDTO


_ORDER_STATUS_MAP = {
    32000: ("wait_seller_delivery", "待发货"),
    32001: ("wait_buyer_pay", "待付款"),
    32002: ("shipped", "已发货"),
    32003: ("trade_finished", "已完成"),
    32004: ("canceled", "已取消"),
    32005: ("trade_closed", "交易关闭"),
}


def map_order(data: dict, platform: str) -> OrderDTO:
    raw = data.get("_raw", {})
    order_id_str = str(data.get("orderId", ""))
    order_status = data.get("orderStatus", 0)
    status_code, status_name = _ORDER_STATUS_MAP.get(
        order_status, (str(order_status), f"状态{order_status}")
    )

    total_money = data.get("orderTotalMoney", 0)
    freight_money = data.get("orderFreightMoney", 0)
    payable_money = data.get("orderBuyerPayableMoney", 0)
    discount_money = data.get("orderDiscountMoney", 0)

    ship_info = data.get("orderShipInfo") or {}
    address_str = ship_info.get("fullAddress", "")

    address = None
    if address_str:
        parts = address_str.split()
        address = AddressDTO(
            province=parts[0] if len(parts) > 0 else "",
            city=parts[1] if len(parts) > 1 else "",
            district=parts[2] if len(parts) > 2 else "",
            detail=" ".join(parts[3:]) if len(parts) > 3 else "",
        )

    items = []
    for p in data.get("product", []):
        items.append(
            OrderItemDTO(
                sku_id=str(p.get("skuId", "")),
                sku_name=p.get("skuName", ""),
                quantity=p.get("num", 1),
                price=round(p.get("price", 0.0) / 100, 2),
                sub_total=round(p.get("price", 0.0) / 100 * p.get("num", 1), 2),
            )
        )

    return OrderDTO(
        platform=platform,
        order_id=order_id_str,
        status=status_code,
        status_name=status_name,
        create_time=data.get("orderStartTime"),
        pay_time=data.get("orderPurchaseTime"),
        total_amount=round(total_money / 100, 2),
        freight_amount=round(freight_money / 100, 2),
        discount_amount=round(discount_money / 100, 2),
        payment_amount=round(payable_money / 100, 2),
        buyer_nick=data.get("venderId"),
        buyer_phone=data.get("buyerMobile"),
        receiver_name=ship_info.get("receiverName"),
        receiver_phone=ship_info.get("phone"),
        receiver_address=address,
        items=items,
        raw_json=raw,
    )


def map_shipment(data: dict, platform: str) -> ShipmentDTO:
    carrier = data.get("deliveryCarrierName", "")
    bill_no = data.get("deliveryBillNo", "")
    confirm_time = data.get("deliveryConfirmTime")
    order_status = data.get("orderStatus", 0)

    _SHIP_STATUS_MAP = {
        32000: ("wait_seller_delivery", "待发货"),
        33040: ("shipped", "已发货"),
        33041: ("delivering", "配送中"),
        34000: ("delivered", "已收货"),
        35000: ("trade_finished", "已完成"),
    }
    ship_status, ship_status_name = _SHIP_STATUS_MAP.get(
        order_status, (str(order_status), f"状态{order_status}")
    )

    shipments = []
    if carrier or bill_no:
        shipments.append(
            ShipmentItemDTO(
                shipment_id=str(data.get("orderId", "")),
                express_company=carrier,
                express_no=bill_no,
                status=ship_status,
                status_name=ship_status_name,
                create_time=confirm_time,
                estimated_arrival=None,
                trace=[],
            )
        )

    return ShipmentDTO(
        platform=platform,
        order_id=str(data.get("orderId", "")),
        shipments=shipments,
        raw_json=data.get("_raw", {}),
    )


def map_after_sale(data: dict, platform: str) -> AfterSaleDTO:
    refund_amount = data.get("refundAmount", 0)
    afs_status = data.get("afsServiceStatus") or {}
    return AfterSaleDTO(
        platform=platform,
        after_sale_id=str(data.get("applyId", "")),
        order_id=str(data.get("orderId", "")),
        type=str(data.get("refundType", "")),
        type_name=data.get("refundTypeName", ""),
        status=str(afs_status.get("afsServiceStep", "")),
        status_name=afs_status.get("afsServiceStepName", "待审核"),
        apply_time=data.get("afsApplyTime"),
        handle_time=data.get("updateTime"),
        apply_amount=round(refund_amount / 100, 2),
        approve_amount=round(refund_amount / 100, 2),
        reason=data.get("questionDesc"),
        reason_detail=data.get("questionDesc"),
        raw_json=data.get("_raw", {}),
    )
