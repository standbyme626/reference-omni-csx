"""Reply and action candidate generator.

Extracted from RecommendationService._generate_replies / _generate_actions
and BusinessContextService._generate_reply_candidates / _generate_action_candidates.
Eliminates duplication between the two.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

__all__ = ["ReplyGenerator"]


class ReplyGenerator:
    """Generate rule-based reply and action candidates from a context dict."""

    # -- replies -----------------------------------------------------------

    def generate_replies(
        self,
        context: Dict[str, Any],
        intent: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        candidates: List[Dict[str, Any]] = []
        normalized_intent = (intent or "").strip().lower()
        refund_intents = {"ask_refund", "refund_progress", "query_refund"}

        order_snapshot = context.get("order_snapshot", {})
        after_sale_snapshot = context.get("after_sale_snapshot")
        risk_flags = context.get("risk_flags", {})

        if normalized_intent in {"query_order", "ask_order_status", "order_status", "ask_order"}:
            candidates.append({
                "reply_type": "order_status",
                "content": f"您好，您的订单状态为：{order_snapshot.get('status', '未知')}。如有其他问题请随时联系。",
                "confidence": 0.95,
                "source": "rule",
                "tags": ["order", "status"],
            })

        if normalized_intent in {"query_shipment", "ask_shipment", "shipment_status"}:
            shipment = context.get("shipment_snapshot", {})
            if shipment.get("tracking_no"):
                candidates.append({
                    "reply_type": "shipment_info",
                    "content": f"您好，您的订单物流单号为：{shipment.get('tracking_no')}，"
                               f"物流公司：{shipment.get('company', '未知')}。",
                    "confidence": 0.9,
                    "source": "rule",
                    "tags": ["shipment", "tracking"],
                })

        if normalized_intent in refund_intents or (not normalized_intent and after_sale_snapshot):
            status_text = (after_sale_snapshot or {}).get("status_text") or "未知"
            candidates.append({
                "reply_type": "after_sale_status",
                "content": f"您好，您的售后申请状态为：{status_text}，我们正在处理中。",
                "confidence": 0.85,
                "source": "rule",
                "tags": ["after_sale", "status"],
            })

        if risk_flags.get("level") == "high":
            candidates.append({
                "reply_type": "escalation_notice",
                "content": "您好，您的问题已记录并转交专人处理，我们会尽快给您回复。",
                "confidence": 0.8,
                "source": "rule",
                "tags": ["escalation", "high_risk"],
            })

        if not candidates:
            candidates.append({
                "reply_type": "general_greeting",
                "content": "您好，请问有什么可以帮您的？",
                "confidence": 0.7,
                "source": "rule",
                "tags": ["general"],
            })

        return sorted(candidates, key=lambda x: x["confidence"], reverse=True)

    # -- actions -----------------------------------------------------------

    def generate_actions(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        candidates: List[Dict[str, Any]] = []
        order_snapshot = context.get("order_snapshot", {})
        after_sale_snapshot = context.get("after_sale_snapshot")
        risk_flags = context.get("risk_flags", {})

        if order_snapshot.get("status") == "wait_ship":
            candidates.append({
                "action_type": "ship_order", "priority": 10,
                "description": "订单待发货，建议安排发货",
                "params": {"order_id": order_snapshot.get("order_id")},
                "auto_executable": False,
            })

        if after_sale_snapshot:
            candidates.append({
                "action_type": "review_after_sale", "priority": 20,
                "description": "存在售后申请需要审核",
                "params": {"after_sale_id": after_sale_snapshot.get("after_sale_id"),
                           "status": after_sale_snapshot.get("status")},
                "auto_executable": False,
            })

        if risk_flags.get("level") == "high":
            candidates.append({
                "action_type": "escalate_case", "priority": 30,
                "description": "高风险订单，建议升级处理",
                "params": {"risk_score": risk_flags.get("score"),
                           "risk_tags": risk_flags.get("tags")},
                "auto_executable": False,
            })

        return sorted(candidates, key=lambda x: x["priority"], reverse=True)

    # -- escalation --------------------------------------------------------

    def evaluate_escalation(
        self,
        context: Dict[str, Any],
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        risk_flags = context.get("risk_flags", {})
        after_sale = context.get("after_sale_snapshot")

        should_escalate = False
        escalation_level = "none"
        suggested_handler = None
        suggested_notes = None

        if risk_flags.get("level") == "high":
            should_escalate = True
            escalation_level = "supervisor"
            suggested_handler = "senior_agent"
            suggested_notes = "高风险订单，建议升级处理"

        if after_sale and after_sale.get("status") == "rejected":
            should_escalate = True
            escalation_level = "manager"
            suggested_handler = "after_sale_specialist"
            suggested_notes = "售后申请被拒绝，可能需要人工介入"

        if reason and "投诉" in reason:
            should_escalate = True
            escalation_level = "supervisor"
            suggested_notes = f"客户投诉：{reason}"

        return {
            "should_escalate": should_escalate,
            "escalation_level": escalation_level,
            "reason": reason,
            "suggested_handler": suggested_handler,
            "suggested_notes": suggested_notes,
        }
