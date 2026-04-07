from fastapi import APIRouter
from typing import Dict, Any
from datetime import datetime

from app.core.response import success_response


router = APIRouter()


_AUDIT_LOGS = [
    {
        "id": 1,
        "action": "provider_mode_switched",
        "actor_type": "admin",
        "actor_id": "admin_user",
        "target_type": "platform",
        "target_id": "jd",
        "detail": "Switched 京东旗舰店 from mock to real",
        "detail_json": {"old_mode": "mock", "new_mode": "real"},
        "created_at": "2026-04-02T08:30:00+00:00",
    },
    {
        "id": 2,
        "action": "message_sent",
        "actor_type": "agent",
        "actor_id": "agent_001",
        "target_type": "message",
        "target_id": "msg_demo_001",
        "detail": "Sent message in conversation: CONV_WK_001",
        "detail_json": {"conversation_id": "CONV_WK_001"},
        "created_at": "2026-04-02T08:35:00+00:00",
    },
]


@router.get("/audit-logs")
async def list_audit_logs(
    entity_type: str = None,
    entity_id: str = None,
):
    filtered = list(_AUDIT_LOGS)
    if entity_type:
        filtered = [l for l in filtered if l.get("target_type") == entity_type]
    if entity_id:
        filtered = [l for l in filtered if l.get("target_id") == entity_id]

    return success_response({"items": filtered, "total": len(filtered)})


@router.post("/audit-logs")
async def create_audit_log(payload: Dict[str, Any]):
    next_id = max((item["id"] for item in _AUDIT_LOGS), default=0) + 1
    item = {
        "id": next_id,
        "action": payload.get("action", "unknown"),
        "actor_type": payload.get("actor_type", "system"),
        "actor_id": payload.get("actor_id"),
        "target_type": payload.get("target_type"),
        "target_id": payload.get("target_id"),
        "detail": payload.get("detail"),
        "detail_json": payload.get("detail_json"),
        "created_at": datetime.now().isoformat(),
    }
    _AUDIT_LOGS.append(item)
    return success_response(item)
