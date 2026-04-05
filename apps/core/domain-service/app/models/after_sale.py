from enum import Enum
from typing import Optional

from pydantic import BaseModel


class AfterSaleStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REFUNDING = "refunding"
    COMPLETED = "completed"


class AfterSale(BaseModel):
    after_sale_id: str = ""
    order_id: str = ""
    platform: str
    status: AfterSaleStatus = AfterSaleStatus.PENDING
    status_text: str = ""
    reason: str = ""
    description: str = ""
    refund_amount: str = "0"
    created_at: str = ""
    updated_at: str = ""
    external_after_sale_id: Optional[str] = None
    canonical_after_sale_id: Optional[str] = None
    requested_order_id: Optional[str] = None
    external_order_id: Optional[str] = None
    canonical_order_id: Optional[str] = None
