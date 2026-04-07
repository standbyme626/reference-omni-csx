from fastapi import APIRouter
from typing import Dict, Any
from datetime import datetime

from app.core.response import success_response


router = APIRouter()


_RISK_FLAGS = [
    {
        "id": 1,
        "customer_id": 1,
        "conversation_id": 1,
        "risk_type": "complaint_tendency",
        "risk_level": "medium",
        "description": "退款会话存在投诉倾向",
        "extra_json": None,
        "status": "active",
        "created_at": "2026-04-02T08:45:00+00:00",
        "updated_at": "2026-04-02T08:45:00+00:00",
    },
    {
        "id": 2,
        "customer_id": 3,
        "conversation_id": 4,
        "risk_type": "negative_sentiment",
        "risk_level": "high",
        "description": "售后会话情绪激烈",
        "extra_json": None,
        "status": "resolved",
        "created_at": "2026-04-02T08:55:00+00:00",
        "updated_at": "2026-04-02T09:10:00+00:00",
    },
]


@router.get("/risk-flags")
async def list_risk_flags(
    status: str = None,
    platform: str = None,
    customer_id: int = None,
):
    filtered = list(_RISK_FLAGS)
    if status:
        filtered = [f for f in filtered if f["status"] == status]
    if customer_id is not None:
        filtered = [f for f in filtered if f["customer_id"] == customer_id]

    return success_response({"items": filtered, "total": len(filtered)})


@router.post("/risk-flags")
async def create_risk_flag(payload: Dict[str, Any]):
    next_id = max((item["id"] for item in _RISK_FLAGS), default=0) + 1
    now = datetime.now().isoformat()
    item = {
        "id": next_id,
        "customer_id": int(payload.get("customer_id") or 0),
        "conversation_id": payload.get("conversation_id"),
        "risk_type": payload.get("risk_type", "negative_sentiment"),
        "risk_level": payload.get("risk_level", "low"),
        "description": payload.get("description"),
        "extra_json": None,
        "status": "active",
        "created_at": now,
        "updated_at": now,
    }
    _RISK_FLAGS.append(item)
    return success_response(item)


@router.post("/risk-flags/{risk_flag_id}/resolve")
async def resolve_risk_flag(risk_flag_id: int):
    for item in _RISK_FLAGS:
        if item["id"] == risk_flag_id:
            item["status"] = "resolved"
            item["updated_at"] = datetime.now().isoformat()
            return success_response(item)
    return success_response({"id": risk_flag_id, "status": "resolved"})


@router.post("/risk-flags/{risk_flag_id}/dismiss")
async def dismiss_risk_flag(risk_flag_id: int):
    for item in _RISK_FLAGS:
        if item["id"] == risk_flag_id:
            item["status"] = "dismissed"
            item["updated_at"] = datetime.now().isoformat()
            return success_response(item)
    return success_response({"id": risk_flag_id, "status": "dismissed"})
