from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


_CUSTOMER_TAGS: list[dict[str, Any]] = [
    {
        "id": 1001,
        "customer_id": 1,
        "tag_type": "intent",
        "tag_value": "物流咨询",
        "source": "system",
        "extra_json": None,
        "created_at": "2026-04-01T09:00:00+00:00",
        "updated_at": "2026-04-01T09:00:00+00:00",
    },
    {
        "id": 1002,
        "customer_id": 2,
        "tag_type": "risk",
        "tag_value": "退款关注",
        "source": "system",
        "extra_json": None,
        "created_at": "2026-04-01T10:00:00+00:00",
        "updated_at": "2026-04-01T10:00:00+00:00",
    },
]

_CONVERSATION_RECOMMENDATIONS: list[dict[str, Any]] = [
    {
        "id": 2001,
        "conversation_id": 1,
        "customer_id": 1,
        "product_id": "JD_RECO_001",
        "product_name": "延保服务包",
        "reason": "客户正在咨询物流，可顺带推荐售后保障服务。",
        "suggested_copy": "如果您后续担心使用问题，也可以了解一下我们的延保服务。",
        "status": "pending",
        "extra_json": None,
        "created_at": "2026-04-01T11:00:00+00:00",
        "updated_at": "2026-04-01T11:00:00+00:00",
    },
    {
        "id": 2002,
        "conversation_id": 2,
        "customer_id": 1,
        "product_id": "JD_RECO_002",
        "product_name": "极速退款权益",
        "reason": "客户关注退款进度，适合推荐售后保障权益。",
        "suggested_copy": "如果您后续售后需求较多，可以考虑极速退款权益，处理会更快。",
        "status": "pending",
        "extra_json": None,
        "created_at": "2026-04-01T11:05:00+00:00",
        "updated_at": "2026-04-01T11:05:00+00:00",
    },
]

_KNOWLEDGE_DOCUMENTS: list[dict[str, Any]] = [
    {
        "document_id": "DOC_FAQ_001",
        "title": "退款流程 FAQ",
        "doc_type": "faq",
        "chunk_count": 8,
        "created_at": "2026-04-01T12:00:00+00:00",
    },
    {
        "document_id": "DOC_SOP_001",
        "title": "物流异常处理 SOP",
        "doc_type": "sop",
        "chunk_count": 12,
        "created_at": "2026-04-01T12:30:00+00:00",
    },
]


def build_customer_profile(customer_id: int) -> dict[str, Any]:
    total_orders = customer_id + 2
    total_spent = f"{customer_id * 188 + 399:.2f}"
    avg_order_value = f"{(float(total_spent) / total_orders):.2f}"
    return {
        "id": customer_id,
        "customer_id": customer_id,
        "total_orders": total_orders,
        "total_spent": total_spent,
        "avg_order_value": avg_order_value,
        "extra_json": {"segment": "simulated"},
        "created_at": "2026-04-01T08:00:00+00:00",
        "updated_at": _utcnow_iso(),
    }


def list_customer_tags(customer_id: int) -> list[dict[str, Any]]:
    return [deepcopy(item) for item in _CUSTOMER_TAGS if item["customer_id"] == customer_id]


def create_customer_tag(customer_id: int, tag_type: str, tag_value: str) -> dict[str, Any]:
    next_id = max((item["id"] for item in _CUSTOMER_TAGS), default=1000) + 1
    now = _utcnow_iso()
    tag = {
        "id": next_id,
        "customer_id": customer_id,
        "tag_type": tag_type,
        "tag_value": tag_value,
        "source": "manual",
        "extra_json": None,
        "created_at": now,
        "updated_at": now,
    }
    _CUSTOMER_TAGS.append(tag)
    return deepcopy(tag)


def delete_customer_tag(tag_id: int) -> bool:
    for index, tag in enumerate(_CUSTOMER_TAGS):
        if tag["id"] == tag_id:
            del _CUSTOMER_TAGS[index]
            return True
    return False


def list_conversation_recommendations(conversation_id: int) -> list[dict[str, Any]]:
    return [
        deepcopy(item)
        for item in _CONVERSATION_RECOMMENDATIONS
        if item["conversation_id"] == conversation_id
    ]


def update_recommendation_status(recommendation_id: int, status: str) -> dict[str, Any] | None:
    for item in _CONVERSATION_RECOMMENDATIONS:
        if item["id"] == recommendation_id:
            item["status"] = status
            item["updated_at"] = _utcnow_iso()
            return deepcopy(item)
    return None


def list_quality_results() -> list[dict[str, Any]]:
    return [
        {
            "id": 3001,
            "conversation_id": 1,
            "quality_rule_id": 1,
            "hit": True,
            "severity": "high",
            "evidence_json": {"issue": "首响超过 30 秒"},
            "inspected_at": "2026-04-02T09:10:00+00:00",
            "created_at": "2026-04-02T09:10:00+00:00",
            "updated_at": "2026-04-02T09:10:00+00:00",
        },
        {
            "id": 3002,
            "conversation_id": 3,
            "quality_rule_id": 2,
            "hit": False,
            "severity": "low",
            "evidence_json": {"issue": "会话处理正常"},
            "inspected_at": "2026-04-02T09:20:00+00:00",
            "created_at": "2026-04-02T09:20:00+00:00",
            "updated_at": "2026-04-02T09:20:00+00:00",
        },
    ]


def list_quality_alerts() -> list[dict[str, Any]]:
    return [
        {
            "id": 3101,
            "quality_inspection_result_id": 3001,
            "alert_level": "high",
            "created_at": "2026-04-02T09:15:00+00:00",
            "updated_at": "2026-04-02T09:15:00+00:00",
        }
    ]


def list_risk_cases() -> list[dict[str, Any]]:
    return [
        {
            "id": 4001,
            "conversation_id": 2,
            "customer_id": 1,
            "risk_type": "complaint_tendency",
            "severity": "medium",
            "status": "open",
            "evidence_json": {"keywords": ["退款", "投诉"]},
            "created_at": "2026-04-02T08:45:00+00:00",
            "updated_at": "2026-04-02T08:45:00+00:00",
        },
        {
            "id": 4002,
            "conversation_id": 4,
            "customer_id": 3,
            "risk_type": "negative_emotion",
            "severity": "high",
            "status": "escalated",
            "evidence_json": {"keywords": ["坏了", "退款"]},
            "created_at": "2026-04-02T08:55:00+00:00",
            "updated_at": "2026-04-02T08:55:00+00:00",
        },
    ]


def list_blacklist_customers() -> list[dict[str, Any]]:
    return [
        {
            "id": 4101,
            "customer_id": 3,
            "reason": "连续多次高风险售后",
            "source": "system",
            "created_at": "2026-04-01T16:00:00+00:00",
            "updated_at": "2026-04-01T16:00:00+00:00",
        }
    ]


def list_voc_topics() -> list[dict[str, Any]]:
    return [
        {
            "id": 5001,
            "topic_name": "退款到账慢",
            "topic_type": "complaint",
            "source": "conversation",
            "occurrence_count": 12,
            "summary": "退款处理时效仍是近期高频投诉点。",
            "created_at": "2026-04-02T07:30:00+00:00",
        },
        {
            "id": 5002,
            "topic_name": "物流轨迹不清晰",
            "topic_type": "feedback",
            "source": "conversation",
            "occurrence_count": 8,
            "summary": "用户更希望在会话中直接看到物流节点解释。",
            "created_at": "2026-04-02T07:40:00+00:00",
        },
    ]


def list_training_cases() -> list[dict[str, Any]]:
    return [
        {
            "id": 5101,
            "title": "退款安抚标准案例",
            "scenario": "after_sale",
            "difficulty": "medium",
            "status": "published",
            "score": 92,
            "created_at": "2026-04-01T13:00:00+00:00",
        },
        {
            "id": 5102,
            "title": "物流异常升级案例",
            "scenario": "shipment",
            "difficulty": "high",
            "status": "draft",
            "score": 88,
            "created_at": "2026-04-01T14:00:00+00:00",
        },
    ]


def list_training_tasks() -> list[dict[str, Any]]:
    return [
        {
            "id": 5201,
            "task_name": "本周售后质检复盘",
            "task_type": "quality_review",
            "status": "running",
            "assignee": "qa_lead",
            "progress": 60,
            "created_at": "2026-04-02T06:30:00+00:00",
        },
        {
            "id": 5202,
            "task_name": "新客服退款话术训练",
            "task_type": "training",
            "status": "pending",
            "assignee": "ops_manager",
            "progress": 0,
            "created_at": "2026-04-02T06:45:00+00:00",
        },
    ]


def list_dashboard_snapshots() -> list[dict[str, Any]]:
    return [
        {
            "id": 5301,
            "snapshot_date": "2026-04-02",
            "total_conversations": 4,
            "active_conversations": 2,
            "risk_alerts": 2,
            "pending_followups": 2,
            "service_score": 91.5,
            "created_at": "2026-04-02T09:30:00+00:00",
        }
    ]


def list_kb_documents() -> list[dict[str, Any]]:
    return [deepcopy(item) for item in _KNOWLEDGE_DOCUMENTS]


def create_kb_document(title: str, content: str, doc_type: str) -> dict[str, Any]:
    next_no = len(_KNOWLEDGE_DOCUMENTS) + 1
    document = {
        "document_id": f"DOC_{doc_type.upper()}_{next_no:03d}",
        "title": title,
        "doc_type": doc_type,
        "chunk_count": max(1, len(content) // 80),
        "created_at": _utcnow_iso(),
    }
    _KNOWLEDGE_DOCUMENTS.append(document)
    return deepcopy(document)


def reindex_knowledge_base() -> dict[str, Any]:
    return {
        "status": "ok",
        "document_count": len(_KNOWLEDGE_DOCUMENTS),
        "reindexed_at": _utcnow_iso(),
    }
