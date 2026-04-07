from fastapi import APIRouter
from typing import Dict, Any
from datetime import datetime

from app.core.response import success_response


router = APIRouter()


_FOLLOWUP_TASKS = [
    {
        "id": "FOLLOW_001",
        "conversation_id": "CONV_WK_001",
        "type": "shipment_followup",
        "status": "pending",
        "assignee": "agent_001",
        "due_time": "2026-04-02T18:00:00",
        "description": "跟进客户物流状态咨询",
        "created_at": "2026-04-02T08:20:00+00:00",
    },
    {
        "id": "FOLLOW_002",
        "conversation_id": "CONV_WK_002",
        "type": "return_followup",
        "status": "pending",
        "assignee": "agent_002",
        "due_time": "2026-04-02T20:00:00",
        "description": "跟进退款处理进度",
        "created_at": "2026-04-02T08:25:00+00:00",
    },
    {
        "id": "FOLLOW_003",
        "conversation_id": "CONV_WK_004",
        "type": "review_followup",
        "status": "completed",
        "assignee": "agent_001",
        "due_time": "2026-04-01T12:00:00",
        "description": "回访客户确认售后处理结果",
        "created_at": "2026-04-01T08:25:00+00:00",
    },
]


@router.get("/follow-up/tasks")
async def list_followup_tasks(
    status: str = None,
    conversation_id: str = None,
    page: int = 1,
    size: int = 50,
):
    filtered = list(_FOLLOWUP_TASKS)
    if status:
        filtered = [t for t in filtered if t["status"] == status]
    if conversation_id:
        filtered = [t for t in filtered if t["conversation_id"] == conversation_id]

    total = len(filtered)
    start = (page - 1) * size
    end = start + size
    items = filtered[start:end]

    return success_response(
        {
            "items": items,
            "total": total,
            "page": page,
            "size": size,
        }
    )


@router.post("/follow-up/tasks/{task_id}/close")
async def close_followup_task(task_id: str):
    for task in _FOLLOWUP_TASKS:
        if task["id"] == task_id:
            task["status"] = "closed"
            task["updated_at"] = datetime.now().isoformat()
            break
    return success_response(
        {
            "id": task_id,
            "status": "closed",
            "closed_at": datetime.now().isoformat(),
        }
    )


@router.post("/follow-up/tasks/{task_id}/execute")
async def execute_followup_task(task_id: str):
    for task in _FOLLOWUP_TASKS:
        if task["id"] == task_id:
            task["status"] = "completed"
            task["updated_at"] = datetime.now().isoformat()
            break
    return success_response(
        {
            "id": task_id,
            "status": "completed",
            "executed_at": datetime.now().isoformat(),
        }
    )
