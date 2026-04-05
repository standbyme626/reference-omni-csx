from enum import Enum
from typing import Optional

from pydantic import BaseModel


class ShipmentStatus(str, Enum):
    PENDING = "pending"
    SHIPPED = "shipped"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    SIGNED = "signed"
    RETURNED = "returned"
    UNKNOWN = "unknown"


class ShipmentNode(BaseModel):
    node: str = ""
    time: str = ""
    description: str = ""


class Shipment(BaseModel):
    shipment_id: str = ""
    order_id: str
    platform: str
    status: ShipmentStatus = ShipmentStatus.UNKNOWN
    status_text: str = ""
    company: Optional[str] = None
    tracking_no: Optional[str] = None
    nodes: list[ShipmentNode] = []
    created_at: str = ""
    updated_at: str = ""
    requested_order_id: Optional[str] = None
    external_order_id: Optional[str] = None
    canonical_order_id: Optional[str] = None
    canonical_shipment_id: Optional[str] = None

SHIPMENT_STATUS_TEXT: dict[str, str] = {
    "pending": "待发货",
    "shipped": "已发货",
    "in_transit": "运输中",
    "delivered": "已签收",
    "signed": "已签收",
    "returned": "已退回",
    "unknown": "未知",
}
