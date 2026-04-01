from fastapi import APIRouter
from typing import List, Dict, Any
from datetime import datetime

from app.core.response import success_response


router = APIRouter()


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
):
    flags = [
        {
            "id": "RISK_001",
            "order_id": "ORDER_001",
            "platform": "taobao",
            "risk_type": "high_value_order",
            "risk_level": "medium",
            "status": "open",
            "description": "高价值订单需要人工审核",
            "created_at": datetime.now().isoformat(),
        },
        {
            "id": "RISK_002",
            "order_id": "ORDER_002",
            "platform": "douyin_shop",
            "risk_type": "multiple_refund",
            "risk_level": "high",
            "status": "open",
            "description": "多次退款申请，存在欺诈风险",
            "created_at": datetime.now().isoformat(),
        },
        {
            "id": "RISK_003",
            "order_id": "ORDER_003",
            "platform": "jd",
            "risk_type": "address_mismatch",
            "risk_level": "low",
            "status": "resolved",
            "description": "收货地址与常用地址不符",
            "created_at": datetime.now().isoformat(),
        },
    ]
    
    filtered = flags
    if status:
        filtered = [f for f in filtered if f["status"] == status]
    if platform:
        filtered = [f for f in filtered if f["platform"] == platform]
    
    return success_response({"items": filtered, "total": len(filtered)})


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
    logs = [
        {
            "id": "LOG_001",
            "entity_type": "order",
            "entity_id": "ORDER_001",
            "action": "status_change",
            "operator": "system",
            "details": "订单状态从 pending 变更为 paid",
            "created_at": datetime.now().isoformat(),
        },
        {
            "id": "LOG_002",
            "entity_type": "conversation",
            "entity_id": "CONV_001",
            "action": "assign",
            "operator": "agent_001",
            "details": "会话分配给客服 agent_001",
            "created_at": datetime.now().isoformat(),
        },
    ]
    
    filtered = logs
    if entity_type:
        filtered = [l for l in filtered if l["entity_type"] == entity_type]
    if entity_id:
        filtered = [l for l in filtered if l["entity_id"] == entity_id]
    
    return success_response({"items": filtered, "total": len(filtered)})


@router.get("/follow-up/tasks")
async def list_followup_tasks(
    status: str = None,
    page: int = 1,
    size: int = 50,
):
    tasks = [
        {
            "id": "FOLLOW_001",
            "conversation_id": "CONV_001",
            "type": "return_followup",
            "status": "pending",
            "assignee": "agent_001",
            "due_time": "2026-04-02T18:00:00",
            "description": "跟进客户退货请求",
            "created_at": datetime.now().isoformat(),
        },
        {
            "id": "FOLLOW_002",
            "conversation_id": "CONV_002",
            "type": "shipment_followup",
            "status": "pending",
            "assignee": "agent_002",
            "due_time": "2026-04-02T20:00:00",
            "description": "确认发货时间",
            "created_at": datetime.now().isoformat(),
        },
        {
            "id": "FOLLOW_003",
            "conversation_id": "CONV_003",
            "type": "review_followup",
            "status": "completed",
            "assignee": "agent_001",
            "due_time": "2026-04-01T12:00:00",
            "description": "邀请客户评价",
            "created_at": datetime.now().isoformat(),
        },
    ]
    
    filtered = tasks
    if status:
        filtered = [t for t in filtered if t["status"] == status]
    
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
    return success_response({
        "id": task_id,
        "status": "closed",
        "closed_at": datetime.now().isoformat(),
    })


@router.post("/follow-up/tasks/{task_id}/execute")
async def execute_followup_task(task_id: str):
    return success_response({
        "id": task_id,
        "status": "completed",
        "executed_at": datetime.now().isoformat(),
    })
