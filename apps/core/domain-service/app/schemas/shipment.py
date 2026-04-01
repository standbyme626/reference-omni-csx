from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class ShipmentNodeResponse(BaseModel):
    node: str
    time: datetime
    description: Optional[str] = None


class ShipmentResponse(BaseModel):
    shipment_id: str
    order_id: str
    platform: str
    status: str
    status_text: Optional[str] = None
    company: Optional[str] = None
    tracking_no: Optional[str] = None
    nodes: List[ShipmentNodeResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class ShipmentListResponse(BaseModel):
    shipments: List[ShipmentResponse]
    total: int
