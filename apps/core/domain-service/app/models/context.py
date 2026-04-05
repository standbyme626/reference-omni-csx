from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.order import Order
from app.models.shipment import Shipment
from app.models.after_sale import AfterSale
from app.models.conversation import Conversation, Message
from app.models.customer import Customer


class RiskFlags(BaseModel):
    level: str = "low"
    tags: list[str] = []
    score: int = 0
    reasons: list[str] = []


class QualityFlags(BaseModel):
    score: int = 100
    issues: list[str] = []
    suggestions: list[str] = []


class ReplyCandidate(BaseModel):
    reply_type: str = ""
    content: str = ""
    confidence: float = 0.0
    source: str = "rule"
    tags: list[str] = []


class ActionCandidate(BaseModel):
    action_type: str = ""
    priority: int = 10
    description: str = ""
    params: dict = {}
    auto_executable: bool = False


class PushEvent(BaseModel):
    event_type: str = ""
    timestamp: str = ""
    data: dict = {}


class ResolvedBizReference(BaseModel):
    biz_type: str = ""
    biz_id: str = ""
    platform: str = ""
    details: dict = {}


class BizContext(BaseModel):
    """Aggregated business context snapshot for AI agent consumption."""
    context_id: str = ""
    platform: str = ""
    biz_id: str = ""
    biz_type: str = "order"
    official_run_id: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""
    data_sources: dict[str, str] = {}
    source_errors: list[dict] = []

    # Typed snapshots (populated from domain services)
    order: Optional[Order] = None
    shipment: Optional[Shipment] = None
    after_sale: Optional[AfterSale] = None
    conversation: Optional[Conversation] = None
    messages: list[Message] = []
    customer: Optional[Customer] = None

    # Derived data
    risk_flags: RiskFlags = RiskFlags()
    quality_flags: QualityFlags = QualityFlags()
    action_candidates: list[ActionCandidate] = []
    reply_candidates: list[ReplyCandidate] = []
    push_events: list[PushEvent] = []
    resolved_biz_reference: Optional[ResolvedBizReference] = None

    # Fallback for data that doesn't fit typed models
    extra: dict = {}

    @classmethod
    def new(cls, platform: str, biz_id: str, biz_type: str = "order",
            official_run_id: Optional[str] = None) -> "BizContext":
        now = datetime.now()
        return cls(
            context_id=str(now),
            platform=platform,
            biz_id=biz_id,
            biz_type=biz_type,
            official_run_id=official_run_id,
            created_at=now.isoformat(),
            updated_at=now.isoformat(),
        )
