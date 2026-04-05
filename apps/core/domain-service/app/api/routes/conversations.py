from typing import Any, Dict, Optional

from app.core.response import success_response
from app.dependencies import get_conversation_service
from app.services.compat_data import list_conversation_recommendations
from app.services.conversation_domain_service import ConversationDomainService
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
    """Helper to find a conversation by ID from the mock search data."""
    svc = get_conversation_service()
    search = svc.search_conversations("all", {}, skip=0, limit=100)
    for conv in search["items"]:
        if conv["id"] == conv_id:
            return conv
    return None


# ====================================================================
# Agent-console compatible routes (no envelope, flat JSON)
# ====================================================================
# These serve the Next.js agent-console frontend directly.

@router.get("/{conv_id}")
async def agent_console_get_conversation(conv_id: str, official_run_id: Optional[str] = None):
    """GET /api/conversations/{conv_id} - Agent console conversation detail."""
    conv = _find_conv_in_search("all", conv_id)
    if not conv:
        return {}

    platform = conv["platform"]
    svc = get_conversation_service()
    return svc.get_conversation(
        platform,
        conv_id,
        official_run_id=official_run_id or conv.get("official_run_id"),
    )


@router.get("/{conv_id}/messages")
async def agent_console_get_messages(
    conv_id: str,
    skip: int = 0,
    limit: int = 50,
    official_run_id: Optional[str] = None,
):
    """GET /api/conversations/{conv_id}/messages - Messages for a conversation."""
    conv = _find_conv_in_search("all", conv_id)
    platform = conv["platform"] if conv else "wecom_kf"

    svc = get_conversation_service()
    result = svc.get_conversation_messages(
        platform,
        conv_id,
        limit=limit,
        official_run_id=official_run_id or (conv or {}).get("official_run_id"),
    )
    messages = result.get("messages", [])
    formatted = []
    for msg in messages:
        direction = "inbound" if msg.get("sender_type") == "customer" else "outbound"
        formatted.append({
            "id": msg["msg_id"],
            "direction": direction,
            "content": msg["content"],
            "sender": msg.get("sender_type", "customer"),
            "create_time": msg.get("created_at", ""),
        })
    return {"total": len(formatted), "items": formatted}


@router.post("/{conv_id}/assign")
async def agent_console_assign(
    conv_id: str,
    request: AssignRequest,
    service: ConversationDomainService = Depends(get_conversation_service),
):
    """POST /api/conversations/{conv_id}/assign - Assign an agent to a conversation."""
    conv = _find_conv_in_search("all", conv_id)
    platform = conv["platform"] if conv else "wecom_kf"
    service.state_transition(platform, conv_id, "assigned")
    return {
        "status": "ok",
        "conversation_id": conv_id,
        "assigned_agent": request.agent_id,
    }


@router.post("/{conv_id}/handoff")
async def agent_console_handoff(
    conv_id: str,
    request: HandoffRequest,
    service: ConversationDomainService = Depends(get_conversation_service),
):
    """POST /api/conversations/{conv_id}/handoff - Handoff a conversation to another agent."""
    conv = _find_conv_in_search("all", conv_id)
    platform = conv["platform"] if conv else "wecom_kf"
    service.state_transition(platform, conv_id, "handed_off")
    return {
        "status": "ok",
        "conversation_id": conv_id,
        "handoff_to": request.target_agent,
    }


@router.get("/{conv_id}/recommendations")
async def agent_console_get_recommendations(conv_id: str):
    conv = _find_conv_in_search("all", conv_id)
    conversation_pk = conv.get("conversation_pk") if conv else 0
    return list_conversation_recommendations(int(conversation_pk or 0))


# ====================================================================
# Existing routes with envelope wrapper
# ====================================================================

@router.get("/")
async def list_conversations(
    platform: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    service: ConversationDomainService = Depends(get_conversation_service),
):
    try:
        query = {}
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
    platform: str,
    conversation_id: str,
    official_run_id: Optional[str] = None,
    service: ConversationDomainService = Depends(get_conversation_service),
):
    try:
        conversation = service.get_conversation(
            platform,
            conversation_id,
            official_run_id=official_run_id,
        )
        return success_response({"conversation": conversation})
    except ValueError as e:
        status_code = 404 if "not found" in str(e).lower() else 400
        raise HTTPException(status_code=status_code, detail=str(e))
    except Exception:
        raise HTTPException(status_code=404, detail=f"Conversation not found: {conversation_id}")


@router.get("/{platform}/{conversation_id}/messages")
async def get_conversation_messages(
    platform: str,
    conversation_id: str,
    limit: int = 100,
    official_run_id: Optional[str] = None,
    service: ConversationDomainService = Depends(get_conversation_service),
):
    try:
        result = service.get_conversation_messages(
            platform,
            conversation_id,
            limit,
            official_run_id=official_run_id,
        )
        return success_response(result)
    except Exception:
        raise HTTPException(status_code=404, detail=f"Conversation not found: {conversation_id}")


@router.post("/search")
async def search_conversations(
    request: SearchConversationsRequest,
    service: ConversationDomainService = Depends(get_conversation_service),
):
    result = service.search_conversations(request.platform, request.query)
    return success_response(result)


@router.post("/{platform}/{conversation_id}/state-transition")
async def state_transition(
    platform: str,
    conversation_id: str,
    request: StateTransitionRequest,
    service: ConversationDomainService = Depends(get_conversation_service),
):
    try:
        result = service.state_transition(platform, conversation_id, request.target_state)
        return success_response(result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
