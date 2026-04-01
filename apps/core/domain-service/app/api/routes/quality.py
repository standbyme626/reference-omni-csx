from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from app.core.response import success_response
from app.services.quality_service import QualityService

router = APIRouter()


class CheckReplyRequest(BaseModel):
    reply_content: str
    context: Optional[Dict[str, Any]] = None


class CheckConversationRequest(BaseModel):
    messages: List[Dict[str, Any]]
    context: Optional[Dict[str, Any]] = None


def get_quality_service() -> QualityService:
    return QualityService()


@router.post("/check-reply")
async def check_reply(request: CheckReplyRequest):
    service = get_quality_service()
    result = service.check_reply(request.reply_content, request.context)
    return success_response(result)


@router.post("/check-conversation")
async def check_conversation(request: CheckConversationRequest):
    service = get_quality_service()
    result = service.check_conversation(request.messages, request.context)
    return success_response(result)


@router.get("/rules")
async def get_quality_rules():
    service = get_quality_service()
    rules = service.get_rules()
    return success_response({"rules": rules})
