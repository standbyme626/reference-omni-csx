"""Operations service — CRUD for risk flags, audit logs, follow-up tasks, tags, and campaigns.

Extracted from the operations.py route so the route layer becomes thin.
Uses thread-safe mutable stores with a lock.
"""
from __future__ import annotations

import threading
from datetime import datetime
from typing import Any, Dict, List, Optional

__all__ = ["OperationsService"]


class OperationsService:
    """Thread-safe in-memory CRUD for operational entities."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._risk_flags: List[Dict[str, Any]] = [
            {"id": 1, "customer_id": 1, "conversation_id": 1, "risk_type": "complaint_tendency",
             "risk_level": "medium", "description": "退款会话存在投诉倾向",
             "extra_json": None, "status": "active",
             "created_at": "2026-04-02T08:45:00+00:00", "updated_at": "2026-04-02T08:45:00+00:00"},
            {"id": 2, "customer_id": 3, "conversation_id": 4, "risk_type": "negative_sentiment",
             "risk_level": "high", "description": "售后会话情绪激烈",
             "extra_json": None, "status": "resolved",
             "created_at": "2026-04-02T08:55:00+00:00", "updated_at": "2026-04-02T09:10:00+00:00"},
        ]
        self._audit_logs: List[Dict[str, Any]] = [
            {"id": 1, "action": "provider_mode_switched", "actor_type": "admin", "actor_id": "admin_user",
             "target_type": "platform", "target_id": "jd",
             "detail": "Switched 京东旗舰店 from mock to real", "detail_json": {"old_mode": "mock", "new_mode": "real"},
             "created_at": "2026-04-02T08:30:00+00:00"},
            {"id": 2, "action": "message_sent", "actor_type": "agent", "actor_id": "agent_001",
             "target_type": "message", "target_id": "msg_demo_001",
             "detail": "Sent message in conversation: CONV_WK_001", "detail_json": {"conversation_id": "CONV_WK_001"},
             "created_at": "2026-04-02T08:35:00+00:00"},
        ]
        self._followup_tasks: List[Dict[str, Any]] = [
            {"id": "FOLLOW_001", "conversation_id": "CONV_WK_001", "type": "shipment_followup",
             "status": "pending", "assignee": "agent_001", "due_time": "2026-04-02T18:00:00",
             "description": "跟进客户物流状态咨询", "created_at": "2026-04-02T08:20:00+00:00"},
            {"id": "FOLLOW_002", "conversation_id": "CONV_WK_002", "type": "return_followup",
             "status": "pending", "assignee": "agent_002", "due_time": "2026-04-02T20:00:00",
             "description": "跟进退款处理进度", "created_at": "2026-04-02T08:25:00+00:00"},
            {"id": "FOLLOW_003", "conversation_id": "CONV_WK_004", "type": "review_followup",
             "status": "completed", "assignee": "agent_001", "due_time": "2026-04-01T12:00:00",
             "description": "回访客户确认售后处理结果", "created_at": "2026-04-01T08:25:00+00:00"},
        ]
        self._tags: List[Dict[str, Any]] = [
            {"id": "TAG_001", "name": "VIP 客户", "category": "customer", "color": "gold"},
            {"id": "TAG_002", "name": "新客户", "category": "customer", "color": "green"},
            {"id": "TAG_003", "name": "高价值", "category": "order", "color": "red"},
            {"id": "TAG_004", "name": "敏感商品", "category": "product", "color": "orange"},
            {"id": "TAG_005", "name": "活动用户", "category": "customer", "color": "blue"},
        ]
        self._campaigns: List[Dict[str, Any]] = [
            {"id": "CAMP_001", "name": "618 大促活动", "type": "promotion", "status": "active",
             "start_time": "2026-06-01T00:00:00", "end_time": "2026-06-20T23:59:59",
             "target_platforms": ["taobao", "douyin_shop", "jd"], "description": "618 年中大促活动"},
            {"id": "CAMP_002", "name": "双十一预热", "type": "promotion", "status": "preparing",
             "start_time": "2026-11-01T00:00:00", "end_time": "2026-11-11T23:59:59",
             "target_platforms": ["taobao", "jd", "xhs"], "description": "双十一购物节预热活动"},
            {"id": "CAMP_003", "name": "新品上市推广", "type": "launch", "status": "active",
             "start_time": "2026-04-01T00:00:00", "end_time": "2026-04-30T23:59:59",
             "target_platforms": ["douyin_shop", "kuaishou"], "description": "春季新品上市推广活动"},
        ]

    # -- risk flags --------------------------------------------------------

    def list_risk_flags(
        self, status: Optional[str] = None, customer_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        with self._lock:
            filtered = list(self._risk_flags)
        if status:
            filtered = [f for f in filtered if f["status"] == status]
        if customer_id is not None:
            filtered = [f for f in filtered if f["customer_id"] == customer_id]
        return {"items": filtered, "total": len(filtered)}

    def create_risk_flag(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        now = datetime.now().isoformat()
        with self._lock:
            next_id = max((i["id"] for i in self._risk_flags), default=0) + 1
            item = {
                "id": next_id, "customer_id": int(payload.get("customer_id") or 0),
                "conversation_id": payload.get("conversation_id"),
                "risk_type": payload.get("risk_type", "negative_sentiment"),
                "risk_level": payload.get("risk_level", "low"),
                "description": payload.get("description"), "extra_json": None,
                "status": "active", "created_at": now, "updated_at": now,
            }
            self._risk_flags.append(item)
            return dict(item)

    def resolve_risk_flag(self, risk_flag_id: int) -> Dict[str, Any]:
        with self._lock:
            for item in self._risk_flags:
                if item["id"] == risk_flag_id:
                    item["status"] = "resolved"
                    item["updated_at"] = datetime.now().isoformat()
                    return dict(item)
        return {"id": risk_flag_id, "status": "resolved"}

    def dismiss_risk_flag(self, risk_flag_id: int) -> Dict[str, Any]:
        with self._lock:
            for item in self._risk_flags:
                if item["id"] == risk_flag_id:
                    item["status"] = "dismissed"
                    item["updated_at"] = datetime.now().isoformat()
                    return dict(item)
        return {"id": risk_flag_id, "status": "dismissed"}

    # -- audit logs --------------------------------------------------------

    def list_audit_logs(self, entity_type: Optional[str] = None, entity_id: Optional[str] = None) -> Dict[str, Any]:
        with self._lock:
            filtered = list(self._audit_logs)
        if entity_type:
            filtered = [l for l in filtered if l.get("target_type") == entity_type]
        if entity_id:
            filtered = [l for l in filtered if l.get("target_id") == entity_id]
        return {"items": filtered, "total": len(filtered)}

    def create_audit_log(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            next_id = max((i["id"] for i in self._audit_logs), default=0) + 1
            item = {
                "id": next_id, "action": payload.get("action", "unknown"),
                "actor_type": payload.get("actor_type", "system"), "actor_id": payload.get("actor_id"),
                "target_type": payload.get("target_type"), "target_id": payload.get("target_id"),
                "detail": payload.get("detail"), "detail_json": payload.get("detail_json"),
                "created_at": datetime.now().isoformat(),
            }
            self._audit_logs.append(item)
            return dict(item)

    # -- follow-up tasks ---------------------------------------------------

    def list_followup_tasks(
        self, status: Optional[str] = None, conversation_id: Optional[str] = None,
        page: int = 1, size: int = 50,
    ) -> Dict[str, Any]:
        with self._lock:
            filtered = list(self._followup_tasks)
        if status:
            filtered = [t for t in filtered if t["status"] == status]
        if conversation_id:
            filtered = [t for t in filtered if t["conversation_id"] == conversation_id]
        total = len(filtered)
        start = (page - 1) * size
        return {"items": filtered[start:start + size], "total": total, "page": page, "size": size}

    def close_followup_task(self, task_id: str) -> Dict[str, Any]:
        with self._lock:
            for task in self._followup_tasks:
                if task["id"] == task_id:
                    task["status"] = "closed"
                    task["updated_at"] = datetime.now().isoformat()
                    break
        return {"id": task_id, "status": "closed", "closed_at": datetime.now().isoformat()}

    def execute_followup_task(self, task_id: str) -> Dict[str, Any]:
        with self._lock:
            for task in self._followup_tasks:
                if task["id"] == task_id:
                    task["status"] = "completed"
                    task["updated_at"] = datetime.now().isoformat()
                    break
        return {"id": task_id, "status": "completed", "executed_at": datetime.now().isoformat()}

    # -- tags --------------------------------------------------------------

    def list_tags(self, category: Optional[str] = None) -> Dict[str, Any]:
        with self._lock:
            filtered = list(self._tags)
        if category:
            filtered = [t for t in filtered if t["category"] == category]
        return {"items": filtered, "total": len(filtered)}

    # -- campaigns ---------------------------------------------------------

    def list_campaigns(self) -> Dict[str, Any]:
        with self._lock:
            return {"items": list(self._campaigns), "total": len(self._campaigns)}
