from datetime import datetime
from typing import Any, Dict

from app.models.unified import (
    OrderStatus,
    Platform,
    UnifiedAddress,
    UnifiedOrder,
    UnifiedProduct,
)


def _parse_datetime(value: Any) -> datetime:
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


class TaobaoAdapter:
    @staticmethod
    def to_unified_order(platform_data: Dict[str, Any]) -> UnifiedOrder:
        trade = platform_data.get("trade", {})
        orders_list = platform_data.get("orders", {}).get("order", [])
        if not orders_list:
            orders_list = trade.get("orders", {}).get("order", [])

        address = trade.get("receiver_address", "")
        if not address:
            address = "".join(
                [
                    str(trade.get("receiver_state", "")),
                    str(trade.get("receiver_city", "")),
                    str(trade.get("receiver_district", "")),
                    str(trade.get("receiver_address", "")),
                ]
            )

        receiver = UnifiedAddress(
            name=trade.get("receiver_name", ""),
            phone=trade.get("receiver_phone", "") or trade.get("receiver_mobile", ""),
            address=address,
        )

        products = [
            UnifiedProduct(
                product_id=str(order.get("oid", "")),
                name=order.get("title", ""),
                price=order.get("price", "0"),
                quantity=order.get("num", 1),
            )
            for order in orders_list
        ]

        status_map = {
            "wait_pay": OrderStatus.WAIT_PAY,
            "wait_ship": OrderStatus.WAIT_SHIP,
            "shipped": OrderStatus.SHIPPED,
            "trade_closed": OrderStatus.TRADE_CLOSED,
            "finished": OrderStatus.FINISHED,
            "WAIT_BUYER_PAY": OrderStatus.WAIT_PAY,
            "WAIT_SELLER_SEND_GOODS": OrderStatus.WAIT_SHIP,
            "WAIT_BUYER_CONFIRM_GOODS": OrderStatus.SHIPPED,
            "TRADE_FINISHED": OrderStatus.FINISHED,
        }

        return UnifiedOrder(
            order_id=str(trade.get("tid", "")),
            platform=Platform.TAOBAO,
            status=status_map.get(trade.get("status", ""), OrderStatus.WAIT_PAY),
            total_amount=trade.get("total_fee", "0"),
            pay_amount=trade.get("payment", "0"),
            receiver=receiver,
            products=products,
            created_at=_parse_datetime(trade.get("created")),
            updated_at=_parse_datetime(trade.get("modified")),
            external_order_id=str(trade.get("tid")) if trade.get("tid") is not None else None,
        )

    @staticmethod
    def from_unified_order(unified: UnifiedOrder) -> Dict[str, Any]:
        return {
            "trade": {
                "tid": unified.order_id,
                "status": unified.status.value,
                "total_fee": unified.total_amount,
                "payment": unified.pay_amount,
                "receiver_name": unified.receiver.name,
                "receiver_phone": unified.receiver.phone,
                "receiver_address": unified.receiver.address,
                "created": unified.created_at.isoformat(),
                "modified": unified.updated_at.isoformat(),
            },
            "orders": {
                "order": [
                    {
                        "oid": p.product_id,
                        "title": p.name,
                        "price": p.price,
                        "num": p.quantity,
                    }
                    for p in unified.products
                ]
            },
        }


class DouyinShopAdapter:
    @staticmethod
    def to_unified_order(platform_data: Dict[str, Any]) -> UnifiedOrder:
        order_data = platform_data.get("order", platform_data)

        receiver_info = order_data.get("receiver", {})
        address_parts = [
            receiver_info.get("province", ""),
            receiver_info.get("city", ""),
            receiver_info.get("district", ""),
            receiver_info.get("address", ""),
        ]

        receiver = UnifiedAddress(
            name=receiver_info.get("name", ""),
            phone=receiver_info.get("phone", "") or receiver_info.get("mobile", ""),
            address=receiver_info.get("address", "") or "".join(str(part) for part in address_parts),
        )

        product_items = order_data.get("product_items", order_data.get("products", []))
        products = [
            UnifiedProduct(
                product_id=p.get("product_id", ""),
                name=p.get("product_name", "") or p.get("name", ""),
                price=_amount_from_minor_units(p.get("product_price", p.get("price", "0"))),
                quantity=p.get("product_count", 1) or p.get("num", 1),
            )
            for p in product_items
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

        return UnifiedOrder(
            order_id=str(order_data.get("order_id", "")),
            platform=Platform.DOUYIN_SHOP,
            status=status_map.get(
                order_data.get("order_status", order_data.get("status", 10)),
                OrderStatus.WAIT_PAY,
            ),
            total_amount=_amount_from_minor_units(
                order_amount.get("total_amount", order_data.get("total_amount", "0"))
            ),
            pay_amount=_amount_from_minor_units(
                order_amount.get("pay_amount", order_data.get("pay_amount", "0"))
            ),
            freight=_amount_from_minor_units(
                order_amount.get("freight_amount", order_data.get("freight", "0"))
            ),
            receiver=receiver,
            products=products,
            created_at=_parse_datetime(order_data.get("create_time")),
            updated_at=_parse_datetime(order_data.get("update_time")),
        )

    @staticmethod
    def from_unified_order(unified: UnifiedOrder) -> Dict[str, Any]:
        return {
            "order_id": unified.order_id,
            "status": unified.status.value,
            "total_amount": unified.total_amount,
            "pay_amount": unified.pay_amount,
            "freight": unified.freight,
            "receiver": {
                "name": unified.receiver.name,
                "phone": unified.receiver.phone,
                "address": unified.receiver.address,
            },
            "products": [
                {
                    "product_id": p.product_id,
                    "name": p.name,
                    "price": p.price,
                    "num": p.quantity,
                }
                for p in unified.products
            ],
            "create_time": unified.created_at.isoformat(),
            "update_time": unified.updated_at.isoformat(),
        }


class WecomKfAdapter:
    @staticmethod
    def to_unified_conversation(platform_data: Dict[str, Any]) -> Dict[str, Any]:
        from app.models.unified import ConversationStatus, Platform, UnifiedConversation

        return UnifiedConversation(
            conversation_id=platform_data.get("conversation_id", ""),
            platform=Platform.WECOM_KF,
            status=ConversationStatus.IN_SESSION
            if platform_data.get("status") == "in_session"
            else ConversationStatus.PENDING,
            openid=platform_data.get("openid"),
            scene=platform_data.get("scene"),
            created_at=datetime.fromisoformat(platform_data.get("created_at", datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(platform_data.get("updated_at", datetime.now().isoformat())),
        )


class JDAdapter:
    @staticmethod
    def to_unified_order(platform_data: Dict[str, Any]) -> UnifiedOrder:
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

            return UnifiedOrder(
                order_id=str(platform_data.get("order_id", "")),
                platform=Platform.JD,
                status=status_map.get(str(platform_data.get("status", "")), OrderStatus.WAIT_PAY),
                total_amount=str(platform_data.get("total_amount", "0")),
                pay_amount=str(platform_data.get("pay_amount", "0")),
                freight=str(platform_data.get("freight", "0")),
                receiver=UnifiedAddress(
                    name=receiver_info.get("name", ""),
                    phone=receiver_info.get("phone", ""),
                    address=receiver_info.get("address", ""),
                ),
                products=[
                    UnifiedProduct(
                        product_id=str(item.get("item_id", "") or item.get("product_id", "")),
                        name=item.get("name", ""),
                        price=str(item.get("price", "0")),
                        quantity=item.get("quantity", 1),
                    )
                    for item in items
                    if isinstance(item, dict)
                ],
                created_at=_parse_datetime(platform_data.get("create_time")),
                updated_at=_parse_datetime(platform_data.get("update_time")),
            )

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
                    products.append(UnifiedProduct(
                        product_id=str(item.get("skuId", "") or item.get("outerSkuId", "")),
                        name=item.get("skuName", "") or item.get("itemName", ""),
                        price=_amount_from_minor_units(item.get("jdPrice", item.get("price", 0))),
                        quantity=item.get("num", 1) or item.get("itemCount", 1),
                    ))

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

            return UnifiedOrder(
                order_id=str(jd_resp.get("orderId", "")),
                platform=Platform.JD,
                status=order_status,
                total_amount=_amount_from_minor_units(
                    jd_resp.get("orderTotalMoney")
                    or jd_resp.get("orderAmount")
                    or jd_resp.get("orderPayment")
                ),
                pay_amount=paid_amount,
                freight=_amount_from_minor_units(jd_resp.get("orderFreightMoney", 0)),
                receiver=UnifiedAddress(
                    name=receiver_info.get("name", ""),
                    phone=receiver_info.get("phone", ""),
                    address=receiver_info.get("fullAddress", ""),
                ),
                products=products,
                created_at=_parse_datetime(jd_resp.get("orderStartTime")),
                updated_at=_parse_datetime(jd_resp.get("orderStatusTime")),
            )

        order_data = jd_resp
        receiver_info = order_data.get("receiver", {})
        address_parts = [
            receiver_info.get("province", ""),
            receiver_info.get("city", ""),
            receiver_info.get("district", ""),
            receiver_info.get("address", ""),
        ]
        full_address = receiver_info.get("fullAddress", " ".join(address_parts).strip())

        receiver = UnifiedAddress(
            name=receiver_info.get("name", ""),
            phone=receiver_info.get("phone", ""),
            address=full_address,
        )

        items = order_data.get("productItems", [])
        products = [
            UnifiedProduct(
                product_id=str(item.get("skuId", "") or item.get("itemId", "")),
                name=item.get("skuName", "") or item.get("itemName", ""),
                price=_amount_from_minor_units(item.get("jdPrice", item.get("price", 0))),
                quantity=item.get("num", 1) or item.get("itemCount", 1),
            )
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

        return UnifiedOrder(
            order_id=str(order_data.get("orderId", "") or order_data.get("order_id", "")),
            platform=Platform.JD,
            status=status_map.get(order_data.get("orderStatus", order_data.get("status", 31000)), OrderStatus.WAIT_PAY),
            total_amount=_amount_from_minor_units(
                order_price_detail.get("orderAmount")
                or order_data.get("totalPrice")
                or order_data.get("totalAmount")
            ),
            pay_amount=_amount_from_minor_units(
                order_data.get("paymentAmount")
                or order_data.get("payAmount")
                or order_data.get("actualPrice")
            ),
            freight=_amount_from_minor_units(
                order_data.get("freightAmount")
                or order_data.get("freight")
                or 0
            ),
            receiver=receiver,
            products=products,
            created_at=_parse_datetime(order_data.get("createTime") or order_data.get("create_time")),
            updated_at=_parse_datetime(order_data.get("modifyTime") or order_data.get("update_time")),
        )
    
    @staticmethod
    def from_unified_order(unified: UnifiedOrder) -> Dict[str, Any]:
        return {
            "order_id": unified.order_id,
            "status": unified.status.value,
            "total_amount": unified.total_amount,
            "pay_amount": unified.pay_amount,
            "freight": unified.freight,
            "receiver": {
                "name": unified.receiver.name,
                "phone": unified.receiver.phone,
                "address": unified.receiver.address,
            },
            "items": [
                {
                    "item_id": p.product_id,
                    "name": p.name,
                    "price": p.price,
                    "quantity": p.quantity,
                }
                for p in unified.products
            ],
        }


class XhsAdapter:
    @staticmethod
    def to_unified_order(platform_data: Dict[str, Any]) -> UnifiedOrder:
        order_data = platform_data.get("order", platform_data)

        receiver_info = order_data.get("receiver", {})
        address_parts = [
            receiver_info.get("province", ""),
            receiver_info.get("city", ""),
            receiver_info.get("district", ""),
            receiver_info.get("address", ""),
        ]
        full_address = receiver_info.get("fullAddress", " ".join(address_parts).strip())

        receiver = UnifiedAddress(
            name=receiver_info.get("name", ""),
            phone=receiver_info.get("phone", ""),
            address=full_address,
        )

        items = order_data.get("productItems", order_data.get("items", []))
        products = [
            UnifiedProduct(
                product_id=str(item.get("itemId", "") or item.get("skuId", "") or item.get("item_id", "")),
                name=item.get("itemName", "") or item.get("skuName", ""),
                price=_amount_from_minor_units(item.get("price", 0)),
                quantity=item.get("itemCount", item.get("quantity", 1)) or item.get("num", 1),
            )
            for item in items
        ]

        status_map = {
            "created": OrderStatus.WAIT_PAY,
            "pending": OrderStatus.WAIT_PAY,
            "paid": OrderStatus.PAID,
            "delivering": OrderStatus.IN_TRANSIT,
            "delivered": OrderStatus.FINISHED,
            "completed": OrderStatus.FINISHED,
            "cancelled": OrderStatus.TRADE_CLOSED,
        }

        return UnifiedOrder(
            order_id=str(order_data.get("orderId", "") or order_data.get("order_id", "")),
            platform=Platform.XHS,
            status=status_map.get(order_data.get("orderStatus", order_data.get("status", "created")), OrderStatus.WAIT_PAY),
            total_amount=_amount_from_minor_units(order_data.get("totalAmount", order_data.get("total_amount", 0))),
            pay_amount=_amount_from_minor_units(order_data.get("payAmount", order_data.get("pay_amount", 0))),
            freight=_amount_from_minor_units(order_data.get("postAmount", order_data.get("freight", 0))),
            receiver=receiver,
            products=products,
            created_at=_parse_datetime(order_data.get("createTime") or order_data.get("create_time")),
            updated_at=_parse_datetime(order_data.get("updateTime") or order_data.get("update_time") or order_data.get("createTime")),
        )
    
    @staticmethod
    def from_unified_order(unified: UnifiedOrder) -> Dict[str, Any]:
        return {
            "order_id": unified.order_id,
            "status": unified.status.value,
            "total_amount": unified.total_amount,
            "pay_amount": unified.pay_amount,
            "freight": unified.freight,
            "receiver": {
                "name": unified.receiver.name,
                "phone": unified.receiver.phone,
                "address": unified.receiver.address,
            },
            "items": [
                {
                    "item_id": p.product_id,
                    "name": p.name,
                    "price": p.price,
                    "quantity": p.quantity,
                }
                for p in unified.products
            ],
        }


class KuaishouAdapter:
    @staticmethod
    def to_unified_order(platform_data: Dict[str, Any]) -> UnifiedOrder:
        order_data = platform_data.get("order", platform_data)

        receiver_info = order_data.get("receiver", {})
        address_parts = [
            receiver_info.get("province", ""),
            receiver_info.get("city", ""),
            receiver_info.get("district", ""),
            receiver_info.get("address", ""),
        ]

        receiver = UnifiedAddress(
            name=receiver_info.get("name", ""),
            phone=receiver_info.get("phone", ""),
            address=receiver_info.get("address", "") or " ".join(address_parts).strip(),
        )

        items = order_data.get("productItems", order_data.get("products", []))
        products = [
            UnifiedProduct(
                product_id=str(item.get("itemId", "") or item.get("product_id", "")),
                name=item.get("itemName", "") or item.get("name", ""),
                price=_amount_from_minor_units(item.get("price", 0)),
                quantity=item.get("itemCount", item.get("quantity", 1)),
            )
            for item in items
        ]

        status_map = {
            1: OrderStatus.WAIT_PAY,
            2: OrderStatus.PAID,
            3: OrderStatus.WAIT_SHIP,
            4: OrderStatus.SHIPPED,
            5: OrderStatus.IN_TRANSIT,
            6: OrderStatus.FINISHED,
            "pending": OrderStatus.WAIT_PAY,
            "paid": OrderStatus.PAID,
            "delivering": OrderStatus.IN_TRANSIT,
            "delivered": OrderStatus.FINISHED,
            "cancelled": OrderStatus.TRADE_CLOSED,
        }

        return UnifiedOrder(
            order_id=str(order_data.get("orderId", "") or order_data.get("order_id", "")),
            platform=Platform.KUAISHOU,
            status=status_map.get(order_data.get("orderStatus", order_data.get("status", 1)), OrderStatus.WAIT_PAY),
            total_amount=_amount_from_minor_units(order_data.get("totalAmount", order_data.get("total_amount", 0))),
            pay_amount=_amount_from_minor_units(order_data.get("payAmount", order_data.get("pay_amount", 0))),
            freight=_amount_from_minor_units(order_data.get("freightAmount", order_data.get("freight", 0))),
            receiver=receiver,
            products=products,
            created_at=_parse_datetime(order_data.get("createTime") or order_data.get("create_time")),
            updated_at=_parse_datetime(order_data.get("updateTime") or order_data.get("update_time") or order_data.get("createTime")),
        )
    
    @staticmethod
    def from_unified_order(unified: UnifiedOrder) -> Dict[str, Any]:
        return {
            "order_id": unified.order_id,
            "status": unified.status.value,
            "total_amount": unified.total_amount,
            "pay_amount": unified.pay_amount,
            "freight": unified.freight,
            "receiver": {
                "name": unified.receiver.name,
                "phone": unified.receiver.phone,
                "address": unified.receiver.address,
            },
            "products": [
                {
                    "product_id": p.product_id,
                    "name": p.name,
                    "price": p.price,
                    "quantity": p.quantity,
                }
                for p in unified.products
            ],
        }
