from fastapi import APIRouter
from typing import List, Dict, Any
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


@router.get("/operation-campaigns")
async def list_operation_campaigns():
    campaigns = [
        {
            "id": "CAMP_001",
            "name": "618 大促活动",
            "type": "promotion",
            "status": "active",
            "start_time": "2026-06-01T00:00:00",
            "end_time": "2026-06-20T23:59:59",
            "target_platforms": ["taobao", "douyin_shop", "jd"],
            "description": "618 年中大促活动",
        },
        {
            "id": "CAMP_002",
            "name": "双十一预热",
            "type": "promotion",
            "status": "preparing",
            "start_time": "2026-11-01T00:00:00",
            "end_time": "2026-11-11T23:59:59",
            "target_platforms": ["taobao", "jd", "xhs"],
            "description": "双十一购物节预热活动",
        },
        {
            "id": "CAMP_003",
            "name": "新品上市推广",
            "type": "launch",
            "status": "active",
            "start_time": "2026-04-01T00:00:00",
            "end_time": "2026-04-30T23:59:59",
            "target_platforms": ["douyin_shop", "kuaishou"],
            "description": "春季新品上市推广活动",
        },
    ]
    return success_response({"items": campaigns, "total": len(campaigns)})


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


@router.get("/tags")
async def list_tags(
    category: str = None,
):
    tags = [
        {"id": "TAG_001", "name": "VIP 客户", "category": "customer", "color": "gold"},
        {"id": "TAG_002", "name": "新客户", "category": "customer", "color": "green"},
        {"id": "TAG_003", "name": "高价值", "category": "order", "color": "red"},
        {"id": "TAG_004", "name": "敏感商品", "category": "product", "color": "orange"},
        {"id": "TAG_005", "name": "活动用户", "category": "customer", "color": "blue"},
    ]
    
    filtered = tags
    if category:
        filtered = [t for t in filtered if t["category"] == category]
    
    return success_response({"items": filtered, "total": len(filtered)})


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
    
    return success_response({
        "items": items,
        "total": total,
        "page": page,
        "size": size,
    })


@router.post("/follow-up/tasks/{task_id}/close")
async def close_followup_task(task_id: str):
    for task in _FOLLOWUP_TASKS:
        if task["id"] == task_id:
            task["status"] = "closed"
            task["updated_at"] = datetime.now().isoformat()
            break
    return success_response({
        "id": task_id,
        "status": "closed",
        "closed_at": datetime.now().isoformat(),
    })


@router.post("/follow-up/tasks/{task_id}/execute")
async def execute_followup_task(task_id: str):
    for task in _FOLLOWUP_TASKS:
        if task["id"] == task_id:
            task["status"] = "completed"
            task["updated_at"] = datetime.now().isoformat()
            break
    return success_response({
        "id": task_id,
        "status": "completed",
        "executed_at": datetime.now().isoformat(),
    })
