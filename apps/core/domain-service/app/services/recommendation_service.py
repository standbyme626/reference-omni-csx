from typing import Dict, Any, Optional, List
from datetime import datetime

from app.services.business_context_service import BusinessContextService


class RecommendationService:
    def __init__(self, context_service: BusinessContextService):
        self.context_service = context_service
    
    def get_reply_recommendations(
        self,
        platform: str,
        biz_id: str,
        biz_type: str = "order",
        intent: Optional[str] = None,
        max_candidates: int = 5,
    ) -> Dict[str, Any]:
        context = self.context_service.get_context(platform, biz_id)
        
        candidates = self._generate_replies(context, intent)
        
        return {
            "candidates": candidates[:max_candidates],
            "context_id": context.get("context_id"),
            "generated_at": datetime.now().isoformat(),
        }
    
    def get_action_recommendations(
        self,
        platform: str,
        biz_id: str,
        biz_type: str = "order",
        max_candidates: int = 10,
    ) -> Dict[str, Any]:
        context = self.context_service.get_context(platform, biz_id)
        
        candidates = self._generate_actions(context)
        
        return {
            "candidates": candidates[:max_candidates],
            "context_id": context.get("context_id"),
            "generated_at": datetime.now().isoformat(),
        }
    
    def get_escalation_recommendation(
        self,
        platform: str,
        biz_id: str,
        biz_type: str = "order",
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        context = self.context_service.get_context(platform, biz_id)
        
        return self._evaluate_escalation(context, reason)
    
    def _generate_replies(
        self,
        context: Dict[str, Any],
        intent: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        candidates = []
        
        order_snapshot = context.get("order_snapshot", {})
        after_sale_snapshot = context.get("after_sale_snapshot")
        risk_flags = context.get("risk_flags", {})
        
        if intent == "query_order":
            candidates.append({
                "reply_type": "order_status",
                "content": f"您好，您的订单状态为：{order_snapshot.get('status', '未知')}。如有其他问题请随时联系。",
                "confidence": 0.95,
                "source": "rule",
                "tags": ["order", "status"],
            })
        
        if intent == "query_shipment":
            shipment_snapshot = context.get("shipment_snapshot", {})
            if shipment_snapshot.get("tracking_no"):
                candidates.append({
                    "reply_type": "shipment_info",
                    "content": f"您好，您的订单物流单号为：{shipment_snapshot.get('tracking_no')}，物流公司：{shipment_snapshot.get('company', '未知')}。",
                    "confidence": 0.9,
                    "source": "rule",
                    "tags": ["shipment", "tracking"],
                })
        
        if after_sale_snapshot:
            candidates.append({
                "reply_type": "after_sale_status",
                "content": f"您好，您的售后申请状态为：{after_sale_snapshot.get('status', '未知')}，我们正在处理中。",
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
    
    def _generate_actions(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        candidates = []
        
        order_snapshot = context.get("order_snapshot", {})
        after_sale_snapshot = context.get("after_sale_snapshot")
        risk_flags = context.get("risk_flags", {})
        
        if order_snapshot.get("status") == "wait_ship":
            candidates.append({
                "action_type": "ship_order",
                "priority": 10,
                "description": "订单待发货，建议安排发货",
                "params": {"order_id": order_snapshot.get("order_id")},
                "auto_executable": False,
            })
        
        if after_sale_snapshot:
            candidates.append({
                "action_type": "review_after_sale",
                "priority": 20,
                "description": "存在售后申请需要审核",
                "params": {
                    "after_sale_id": after_sale_snapshot.get("after_sale_id"),
                    "status": after_sale_snapshot.get("status"),
                },
                "auto_executable": False,
            })
        
        if risk_flags.get("level") == "high":
            candidates.append({
                "action_type": "escalate_case",
                "priority": 30,
                "description": "高风险订单，建议升级处理",
                "params": {
                    "risk_score": risk_flags.get("score"),
                    "risk_tags": risk_flags.get("tags"),
                },
                "auto_executable": False,
            })
        
        return sorted(candidates, key=lambda x: x["priority"], reverse=True)
    
    def _evaluate_escalation(
        self,
        context: Dict[str, Any],
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        risk_flags = context.get("risk_flags", {})
        after_sale_snapshot = context.get("after_sale_snapshot")
        
        should_escalate = False
        escalation_level = "none"
        suggested_handler = None
        suggested_notes = None
        
        if risk_flags.get("level") == "high":
            should_escalate = True
            escalation_level = "supervisor"
            suggested_handler = "senior_agent"
            suggested_notes = "高风险订单，建议升级处理"
        
        if after_sale_snapshot and after_sale_snapshot.get("status") == "rejected":
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
