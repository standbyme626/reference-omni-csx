from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class OrderStatus(str, Enum):
    WAIT_PAY = "wait_pay"
    PAID = "paid"
    WAIT_SHIP = "wait_ship"
    SHIPPED = "shipped"
    IN_TRANSIT = "in_transit"
    FINISHED = "finished"
    TRADE_CLOSED = "trade_closed"
    REFUNDING = "refunding"
    REFUNDED = "refunded"

STATUS_TEXT: dict[OrderStatus, str] = {
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


class Address(BaseModel):
    name: str = ""
    phone: str = ""
    province: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    address: str = ""


class OrderProduct(BaseModel):
    product_id: str
    name: str
    price: str = "0"
    quantity: int = 1


class Order(BaseModel):
    order_id: str
    platform: str
    status: OrderStatus = OrderStatus.WAIT_PAY
    status_text: str = ""
    total_amount: str = "0"
    pay_amount: str = "0"
    freight: str = "0"
    receiver: Address = Address()
    products: list[OrderProduct] = []
    created_at: str = ""
    updated_at: str = ""
    external_order_id: Optional[str] = None
    requested_order_id: Optional[str] = None
    canonical_order_id: Optional[str] = None
