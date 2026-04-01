from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ReplyRecommendationRequest(BaseModel):
    platform: str
    biz_id: str
    biz_type: str = "order"
    context: Optional[Dict[str, Any]] = None
    intent: Optional[str] = None
    max_candidates: int = 5


class ReplyCandidateResponse(BaseModel):
    reply_type: str
    content: str
    confidence: float = 0.0
    source: str = "rule"
    tags: List[str] = Field(default_factory=list)


class ReplyRecommendationResponse(BaseModel):
    candidates: List[ReplyCandidateResponse]
    context_id: Optional[str] = None
    generated_at: str


class ActionRecommendationRequest(BaseModel):
    platform: str
    biz_id: str
    biz_type: str = "order"
    context: Optional[Dict[str, Any]] = None
    max_candidates: int = 10


class ActionCandidateResponse(BaseModel):
    action_type: str
    priority: int = 0
    description: str
    params: Dict[str, Any] = Field(default_factory=dict)
    auto_executable: bool = False


class ActionRecommendationResponse(BaseModel):
    candidates: List[ActionCandidateResponse]
    context_id: Optional[str] = None
    generated_at: str


class EscalationRecommendationRequest(BaseModel):
    platform: str
    biz_id: str
    biz_type: str = "order"
    context: Optional[Dict[str, Any]] = None
    reason: Optional[str] = None


class EscalationRecommendationResponse(BaseModel):
    should_escalate: bool
    escalation_level: str = "none"
    reason: Optional[str] = None
    suggested_handler: Optional[str] = None
    suggested_notes: Optional[str] = None
