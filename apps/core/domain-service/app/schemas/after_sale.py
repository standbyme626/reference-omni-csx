from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class AfterSaleResponse(BaseModel):
    after_sale_id: str
    order_id: str
    platform: str
    status: str
    status_text: Optional[str] = None
    type: Optional[str] = None
    reason: str
    description: Optional[str] = None
    refund_amount: str
    created_at: datetime
    updated_at: datetime


class AfterSaleListResponse(BaseModel):
    after_sales: List[AfterSaleResponse]
    total: int
