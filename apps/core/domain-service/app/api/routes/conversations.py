"""Conversation routes — slim: params + delegate to service + return."""
from typing import Any, Dict, Optional

from app.core.response import success_response
from app.dependencies import get_conversation_service
from app.services.compat_data import list_conversation_recommendations
from app.services.conversation_service import ConversationService
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel


class AssignRequest(BaseModel):
    agent_id: str


class HandoffRequest(BaseModel):
    target_agent: str


class SearchConversationsRequest(BaseModel):
    platform: str
    query: Dict[str, Any]


class StateTransitionRequest(BaseModel):
    target_state: str


router = APIRouter()


def _find_conv_in_search(platform: str, conv_id: str):
    svc = get_conversation_service()
    search = svc.search_conversations("all", {}, skip=0, limit=100)
    for conv in search["items"]:
        if conv["id"] == conv_id:
            return conv
    return None


# ====================================================================
# Agent-console routes (no envelope, flat JSON)
# ====================================================================

@router.get("/{conv_id}")
async def agent_console_get_conversation(conv_id: str, official_run_id: Optional[str] = None):
    conv = _find_conv_in_search("all", conv_id)
    if not conv:
        return {}
    svc = get_conversation_service()
    return svc.get_conversation(platform=conv["platform"], conversation_id=conv_id,
                                official_run_id=official_run_id or conv.get("official_run_id"))


@router.get("/{conv_id}/messages")
async def agent_console_get_messages(conv_id: str, skip: int = 0, limit: int = 50, official_run_id: Optional[str] = None):
    conv = _find_conv_in_search("all", conv_id)
    platform = conv["platform"] if conv else "wecom_kf"
    svc = get_conversation_service()
    result = svc.get_conversation_messages(platform, conv_id, limit=limit,
                                           official_run_id=official_run_id or (conv or {}).get("official_run_id"))
    messages = result.get("messages", [])
    return {"total": len(messages), "items": [{
        "id": m["msg_id"], "direction": "inbound" if m.get("sender_type") == "customer" else "outbound",
        "content": m["content"], "sender": m.get("sender_type", "customer"),
        "create_time": m.get("created_at", ""),
    } for m in messages]}


@router.post("/{conv_id}/assign")
async def agent_console_assign(
    conv_id: str, request: AssignRequest,
    service: ConversationService = Depends(get_conversation_service),
):
    conv = _find_conv_in_search("all", conv_id)
    platform = conv["platform"] if conv else "wecom_kf"
    service.state_transition(platform, conv_id, "assigned")
    return {"status": "ok", "conversation_id": conv_id, "assigned_agent": request.agent_id}


@router.post("/{conv_id}/handoff")
async def agent_console_handoff(
    conv_id: str, request: HandoffRequest,
    service: ConversationService = Depends(get_conversation_service),
):
    conv = _find_conv_in_search("all", conv_id)
    platform = conv["platform"] if conv else "wecom_kf"
    service.state_transition(platform, conv_id, "handed_off")
    return {"status": "ok", "conversation_id": conv_id, "handoff_to": request.target_agent}


@router.get("/{conv_id}/recommendations")
async def agent_console_get_recommendations(conv_id: str):
    conv = _find_conv_in_search("all", conv_id)
    conversation_pk = conv.get("conversation_pk") if conv else 0
    return list_conversation_recommendations(int(conversation_pk or 0))


# ====================================================================
# Standard routes (envelope wrapper)
# ====================================================================

@router.get("/")
async def list_conversations(
    platform: Optional[str] = None, status: Optional[str] = None, skip: int = 0, limit: int = 100,
    service: ConversationService = Depends(get_conversation_service),
):
    try:
        query: Dict[str, Any] = {}
        if platform:
            query["platform"] = platform
        if status:
            query["status"] = status
        result = service.search_conversations("all", query, skip, limit)
        return success_response(result)
    except Exception:
        return success_response({"items": [], "total": 0})


@router.get("/{platform}/{conversation_id}")
async def get_conversation(
    platform: str, conversation_id: str, official_run_id: Optional[str] = None,
    service: ConversationService = Depends(get_conversation_service),
):
    conversation = service.get_conversation(platform, conversation_id, official_run_id=official_run_id)
    return success_response({"conversation": conversation})


@router.get("/{platform}/{conversation_id}/messages")
async def get_conversation_messages(
    platform: str, conversation_id: str, limit: int = 100, official_run_id: Optional[str] = None,
    service: ConversationService = Depends(get_conversation_service),
):
    result = service.get_conversation_messages(platform, conversation_id, limit, official_run_id=official_run_id)
    return success_response(result)


@router.post("/search")
async def search_conversations(
    request: SearchConversationsRequest,
    service: ConversationService = Depends(get_conversation_service),
):
    result = service.search_conversations(request.platform, request.query)
    return success_response(result)


@router.post("/{platform}/{conversation_id}/state-transition")
async def state_transition(
    platform: str, conversation_id: str, request: StateTransitionRequest,
    service: ConversationService = Depends(get_conversation_service),
):
    result = service.state_transition(platform, conversation_id, request.target_state)
    return success_response(result)
