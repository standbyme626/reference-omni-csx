from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional, List
from pydantic import BaseModel

from app.core.response import success_response
from app.adapters.registry import PlatformRegistry
from app.services.platform_gateway_service import PlatformGatewayService
from app.services.order_domain_service import OrderDomainService
from app.services.shipment_domain_service import ShipmentDomainService
from app.services.after_sale_domain_service import AfterSaleDomainService
from app.services.conversation_domain_service import ConversationDomainService
from app.services.business_context_service import BusinessContextService
from app.services.recommendation_service import RecommendationService

router = APIRouter()


class ReplyRecommendationRequest(BaseModel):
    platform: str
    biz_id: str
    biz_type: str = "order"
    intent: Optional[str] = None
    max_candidates: int = 5


class ActionRecommendationRequest(BaseModel):
    platform: str
    biz_id: str
    biz_type: str = "order"
    max_candidates: int = 10


class EscalationRecommendationRequest(BaseModel):
    platform: str
    biz_id: str
    biz_type: str = "order"
    reason: Optional[str] = None


def get_recommendation_service() -> RecommendationService:
    registry = PlatformRegistry()
    gateway = PlatformGatewayService(registry)
    order_service = OrderDomainService(gateway, registry)
    shipment_service = ShipmentDomainService(gateway)
    after_sale_service = AfterSaleDomainService(gateway)
    conversation_service = ConversationDomainService(gateway)
    context_service = BusinessContextService(
        gateway,
        order_service,
        shipment_service,
        after_sale_service,
        conversation_service,
    )
    return RecommendationService(context_service)


@router.post("/reply")
async def get_reply_recommendations(request: ReplyRecommendationRequest):
    try:
        service = get_recommendation_service()
        result = service.get_reply_recommendations(
            request.platform,
            request.biz_id,
            request.biz_type,
            request.intent,
            request.max_candidates,
        )
        return success_response(result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/action")
async def get_action_recommendations(request: ActionRecommendationRequest):
    try:
        service = get_recommendation_service()
        result = service.get_action_recommendations(
            request.platform,
            request.biz_id,
            request.biz_type,
            request.max_candidates,
        )
        return success_response(result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/escalation")
async def get_escalation_recommendation(request: EscalationRecommendationRequest):
    try:
        service = get_recommendation_service()
        result = service.get_escalation_recommendation(
            request.platform,
            request.biz_id,
            request.biz_type,
            request.reason,
        )
        return success_response(result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
