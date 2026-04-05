"""Risk evaluator — calculates risk flags from a context snapshot.

Extracted from BusinessContextService._calculate_risk_flags.
"""
from __future__ import annotations

from typing import Any, Dict

__all__ = ["RiskEvaluator"]


class RiskEvaluator:
    """Evaluate risk level from an aggregated context dict."""

    def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        risk_level = "low"
        tags: list[str] = []
        score = 0

        after_sale = context.get("after_sale_snapshot")
        exceptions = context.get("order_exception_snapshots", [])
        order_status = (context.get("order_snapshot") or {}).get("status")

        if after_sale:
            risk_level = "medium"
            tags.append("has_after_sale")
            score += 20

        if exceptions:
            risk_level = "high" if risk_level == "low" else "critical"
            tags.append("has_exceptions")
            score += len(exceptions) * 15

        if order_status in ("refunding", "refunded"):
            risk_level = "high"
            tags.append("refund_involved")
            score += 30

        return {"level": risk_level, "tags": tags, "score": score, "reasons": []}

    def check_order(
        self, order_data: Dict[str, Any], context: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        tags: list[str] = []
        reasons: list[str] = []
        score = 0

        total_amount = float(order_data.get("total_amount", 0))
        if total_amount > 10000:
            tags.append("high_value")
            score += 10
            reasons.append("高金额订单")

        if order_data.get("status") in ("refunding", "refunded"):
            tags.append("refund_involved")
            score += 20
            reasons.append("涉及退款")

        after_sale = order_data.get("after_sale") or (context.get("after_sale_snapshot") if context else None)
        if after_sale:
            tags.append("has_after_sale")
            score += 15
            reasons.append("存在售后申请")

        level = "low"
        if score >= 50:
            level = "high"
        elif score >= 30:
            level = "medium"

        return {"level": level, "tags": tags, "score": score, "reasons": reasons}

    def check_conversation(
        self, messages: list[Dict[str, Any]], context: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        tags: list[str] = []
        reasons: list[str] = []
        score = 0
        risk_keywords = {"投诉", "举报", "差评", "退款", "赔偿", "法律", "律师"}

        for msg in messages:
            content = msg.get("content", "")
            for kw in risk_keywords:
                if kw in content and kw not in tags:
                    tags.append(kw)
                    score += 10
                    reasons.append(f"消息包含风险词：{kw}")

        level = "low"
        if score >= 30:
            level = "high"
        elif score >= 15:
            level = "medium"

        return {"level": level, "tags": tags, "score": score, "reasons": reasons}
