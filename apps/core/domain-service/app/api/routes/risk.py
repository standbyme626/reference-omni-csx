from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from app.core.response import success_response
from app.services.risk_service import RiskService

router = APIRouter()


class CheckOrderRequest(BaseModel):
    order_data: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None


class CheckConversationRequest(BaseModel):
    messages: List[Dict[str, Any]]
    context: Optional[Dict[str, Any]] = None


def get_risk_service() -> RiskService:
    return RiskService()


@router.post("/check-order")
async def check_order(request: CheckOrderRequest):
    service = get_risk_service()
    result = service.check_order(request.order_data, request.context)
    return success_response(result)


@router.post("/check-conversation")
async def check_conversation(request: CheckConversationRequest):
    service = get_risk_service()
    result = service.check_conversation(request.messages, request.context)
    return success_response(result)


@router.get("/rules")
async def get_risk_rules():
    service = get_risk_service()
    rules = service.get_rules()
    return success_response({"rules": rules})
