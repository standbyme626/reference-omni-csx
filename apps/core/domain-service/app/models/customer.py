from typing import Optional

from pydantic import BaseModel


class CustomerTag(BaseModel):
    """Customer tag with label and priority for display."""
    tag: str
    label: str
    priority: int = 0


class Customer(BaseModel):
    """Unified customer representation across all platforms."""
    customer_id: str = ""
    platform: str = ""
    nick: Optional[str] = None
    openid: Optional[str] = None
    customer_pk: Optional[int] = None
    tags: list[CustomerTag] = []
    total_orders: int = 0
    total_after_sales: int = 0
    lifetime_value: str = "0"
