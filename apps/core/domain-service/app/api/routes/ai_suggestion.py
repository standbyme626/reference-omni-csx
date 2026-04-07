"""AI suggestion routes for agent-console frontend.

Provides /api/ai/suggest-reply which wraps the domain-service recommendation system
in the format expected by the Next.js agent-console.
"""

from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel

from app.dependencies import get_context_resolver
from app.services.recommendation_service import RecommendationService


router = APIRouter()


class SuggestReplyRequest(BaseModel):
    conversation_id: str
    message: str
    platform: Optional[str] = "taobao"
    order_id: Optional[str] = None


@router.post("/suggest-reply")
async def suggest_reply(request: SuggestReplyRequest):
    """Get AI-generated reply suggestion for a customer message.

    Returns the format expected by agent-console:
    {intent, confidence, suggested_reply, used_tools, risk_level, needs_human_review}
    """
    ctx_resolver = get_context_resolver()

    # Try to get business context using order_id if available
    biz_id = request.order_id or request.conversation_id
    context = {}
    try:
        context = ctx_resolver.get_context(request.platform or "taobao", biz_id)
    except Exception:
        pass

    # Get reply candidates from recommendation service
    reply_candidates = context.get("reply_candidates", [])

    if reply_candidates:
        candidate = reply_candidates[0]
        result = {
            "intent": candidate.get("reply_type", "general"),
            "confidence": candidate.get("confidence", 0.5),
            "suggested_reply": candidate.get("content", "您好，已收到您的消息。"),
            "used_tools": [],
            "risk_level": context.get("risk_flags", {}).get("level", "low"),
            "needs_human_review": False,
        }
    else:
        result = {
            "intent": "general",
            "confidence": 0.3,
            "suggested_reply": "您好，已收到您的消息，我们会尽快处理。",
            "used_tools": [],
            "risk_level": "low",
            "needs_human_review": False,
        }

    return result
