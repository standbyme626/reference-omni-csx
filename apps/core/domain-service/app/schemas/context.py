from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class CustomerProfileSnapshot(BaseModel):
    user_id: str
    platform: str
    name: Optional[str] = None
    phone: Optional[str] = None
    member_level: Optional[str] = None
    total_orders: int = 0
    total_spent: str = "0.00"


class OrderSnapshot(BaseModel):
    order_id: str
    status: str
    total_amount: str
    created_at: datetime


class ShipmentSnapshot(BaseModel):
    shipment_id: str
    status: str
    company: Optional[str] = None
    tracking_no: Optional[str] = None


class AfterSaleSnapshot(BaseModel):
    after_sale_id: str
    status: str
    reason: Optional[str] = None


class InventorySnapshot(BaseModel):
    product_id: str
    sku_id: Optional[str] = None
    quantity: int = 0
    reserved_quantity: int = 0
    available_quantity: int = 0
    warehouse: Optional[str] = None
    location: Optional[str] = None
    updated_at: Optional[datetime] = None


class OrderAuditSnapshot(BaseModel):
    order_id: str
    audit_status: str
    audit_notes: Optional[str] = None
    audited_by: Optional[str] = None
    audited_at: Optional[datetime] = None


class OrderExceptionSnapshot(BaseModel):
    exception_id: str
    order_id: str
    exception_type: str
    severity: str
    description: str
    status: str
    created_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None


class FulfillmentSnapshot(BaseModel):
    order_id: str
    status: str
    warehouse: Optional[str] = None
    picking_id: Optional[str] = None
    scheduled_date: Optional[datetime] = None
    actual_date: Optional[datetime] = None


class RiskFlags(BaseModel):
    level: str = "low"
    tags: List[str] = Field(default_factory=list)
    score: int = 0
    reasons: List[str] = Field(default_factory=list)


class QualityFlags(BaseModel):
    score: int = 100
    issues: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)


class ActionCandidate(BaseModel):
    action_type: str
    priority: int = 0
    description: str
    params: Dict[str, Any] = Field(default_factory=dict)


class ReplyCandidate(BaseModel):
    reply_type: str
    content: str
    confidence: float = 0.0
    source: str = "rule"


class BusinessContextResponse(BaseModel):
    context_id: str
    platform: str
    biz_id: str
    biz_type: str
    
    customer_profile: Optional[CustomerProfileSnapshot] = None
    order_snapshot: Optional[OrderSnapshot] = None
    shipment_snapshot: Optional[ShipmentSnapshot] = None
    after_sale_snapshot: Optional[AfterSaleSnapshot] = None
    conversation_snapshot: Optional[Dict[str, Any]] = None
    
    inventory_snapshot: Optional[InventorySnapshot] = None
    order_audit_snapshot: Optional[OrderAuditSnapshot] = None
    order_exception_snapshots: List[OrderExceptionSnapshot] = Field(default_factory=list)
    fulfillment_snapshot: Optional[FulfillmentSnapshot] = None
    
    risk_flags: Optional[RiskFlags] = None
    quality_flags: Optional[QualityFlags] = None
    
    action_candidates: List[ActionCandidate] = Field(default_factory=list)
    reply_candidates: List[ReplyCandidate] = Field(default_factory=list)
    
    knowledge_refs: List[Dict[str, Any]] = Field(default_factory=list)
    
    created_at: datetime
    updated_at: datetime


class BusinessContextBuildRequest(BaseModel):
    platform: str
    biz_id: str
    biz_type: str = "order"
    include_inventory: bool = False
    include_risk: bool = True
    include_quality: bool = True
    include_recommendations: bool = True
