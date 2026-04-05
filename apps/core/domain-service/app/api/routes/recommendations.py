from fastapi import APIRouter, HTTPException
from typing import Optional
from pydantic import BaseModel
import logging

from app.core.response import success_response
from app.dependencies import get_business_context_service
from app.services.compat_data import update_recommendation_status
from app.services.recommendation_service import RecommendationService

router = APIRouter()
logger = logging.getLogger(__name__)


class ReplyRecommendationRequest(BaseModel):
    platform: str
    biz_id: str
    biz_type: str = "order"
    official_run_id: Optional[str] = None
    intent: Optional[str] = None
    max_candidates: int = 5


class ActionRecommendationRequest(BaseModel):
    platform: str
    biz_id: str
    biz_type: str = "order"
    official_run_id: Optional[str] = None
    max_candidates: int = 10


class EscalationRecommendationRequest(BaseModel):
    platform: str
    biz_id: str
    biz_type: str = "order"
    official_run_id: Optional[str] = None
    reason: Optional[str] = None


@router.post("/reply")
async def get_reply_recommendations(request: ReplyRecommendationRequest):
    try:
        service = RecommendationService(get_business_context_service())
        result = service.get_reply_recommendations(
            request.platform,
            request.biz_id,
            request.biz_type,
            request.intent,
            request.max_candidates,
            official_run_id=request.official_run_id,
        )
        logger.info(
            "reply recommendation generated official_run_id=%s platform=%s biz_id=%s biz_type=%s",
            request.official_run_id,
            request.platform,
            request.biz_id,
            request.biz_type,
        )
        return success_response(result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/action")
async def get_action_recommendations(request: ActionRecommendationRequest):
    try:
        service = RecommendationService(get_business_context_service())
        result = service.get_action_recommendations(
            request.platform,
            request.biz_id,
            request.biz_type,
            request.max_candidates,
            official_run_id=request.official_run_id,
        )
        logger.info(
            "action recommendation generated official_run_id=%s platform=%s biz_id=%s biz_type=%s",
            request.official_run_id,
            request.platform,
            request.biz_id,
            request.biz_type,
        )
        return success_response(result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/escalation")
async def get_escalation_recommendation(request: EscalationRecommendationRequest):
    try:
        service = RecommendationService(get_business_context_service())
        result = service.get_escalation_recommendation(
            request.platform,
            request.biz_id,
            request.biz_type,
            request.reason,
            official_run_id=request.official_run_id,
        )
        logger.info(
            "escalation recommendation generated official_run_id=%s platform=%s biz_id=%s biz_type=%s",
            request.official_run_id,
            request.platform,
            request.biz_id,
            request.biz_type,
        )
        return success_response(result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{recommendation_id}/accept")
async def accept_recommendation(recommendation_id: int):
    item = update_recommendation_status(recommendation_id, "accepted")
    if not item:
        raise HTTPException(status_code=404, detail=f"Recommendation not found: {recommendation_id}")
    return success_response(item)


@router.post("/{recommendation_id}/reject")
async def reject_recommendation(recommendation_id: int):
    item = update_recommendation_status(recommendation_id, "rejected")
    if not item:
        raise HTTPException(status_code=404, detail=f"Recommendation not found: {recommendation_id}")
    return success_response(item)
