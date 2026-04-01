from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from app.core.response import success_response
from app.adapters.registry import PlatformRegistry
from app.services.platform_gateway_service import PlatformGatewayService
from app.services.conversation_domain_service import ConversationDomainService

router = APIRouter()


class SearchConversationsRequest(BaseModel):
    platform: str
    query: Dict[str, Any]


class StateTransitionRequest(BaseModel):
    target_state: str


def get_conversation_service() -> ConversationDomainService:
    registry = PlatformRegistry()
    gateway = PlatformGatewayService(registry)
    return ConversationDomainService(gateway)


@router.get("/")
async def list_conversations(
    platform: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
):
    try:
        service = get_conversation_service()
        query = {}
        if platform:
            query["platform"] = platform
        if status:
            query["status"] = status
        result = service.search_conversations("all", query, skip, limit)
        return success_response(result)
    except Exception as e:
        return success_response({"items": [], "total": 0})


@router.get("/{platform}/{conversation_id}")
async def get_conversation(
    platform: str,
    conversation_id: str,
):
    try:
        service = get_conversation_service()
        conversation = service.get_conversation(platform, conversation_id)
        return success_response({"conversation": conversation})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Conversation not found: {conversation_id}")


@router.get("/{platform}/{conversation_id}/messages")
async def get_conversation_messages(
    platform: str,
    conversation_id: str,
    limit: int = 100,
):
    try:
        service = get_conversation_service()
        result = service.get_conversation_messages(platform, conversation_id, limit)
        return success_response(result)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Conversation not found: {conversation_id}")


@router.post("/search")
async def search_conversations(request: SearchConversationsRequest):
    service = get_conversation_service()
    result = service.search_conversations(request.platform, request.query)
    return success_response(result)


@router.post("/{platform}/{conversation_id}/state-transition")
async def state_transition(
    platform: str,
    conversation_id: str,
    request: StateTransitionRequest,
):
    try:
        service = get_conversation_service()
        result = service.state_transition(platform, conversation_id, request.target_state)
        return success_response(result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
