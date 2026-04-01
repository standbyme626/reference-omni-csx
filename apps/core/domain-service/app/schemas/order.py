from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime


class PlatformEnum(str):
    TAOBAO = "taobao"
    DOUYIN_SHOP = "douyin_shop"
    JD = "jd"
    XHS = "xhs"
    KUAISHOU = "kuaishou"
    WECOM_KF = "wecom_kf"


class OrderStatusResponse(BaseModel):
    status: str
    status_text: str
    description: Optional[str] = None


class AddressResponse(BaseModel):
    name: str
    phone: str = Field(description="Phone number, masked for privacy")
    province: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    address: str


class ProductResponse(BaseModel):
    product_id: str
    name: str
    price: str
    quantity: int = 1
    image_url: Optional[str] = None


class OrderResponse(BaseModel):
    order_id: str
    platform: str
    status: str
    status_text: Optional[str] = None
    total_amount: str
    pay_amount: str
    freight: str = "0.00"
    receiver: AddressResponse
    products: List[ProductResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    external_order_id: Optional[str] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)


class OrderListResponse(BaseModel):
    orders: List[OrderResponse]
    total: int
    page: int
    page_size: int


class OrderDetailResponse(BaseModel):
    order: OrderResponse
    user: Optional[Dict[str, Any]] = None
    timeline: Optional[List[Dict[str, Any]]] = None
