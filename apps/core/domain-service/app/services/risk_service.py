from typing import Dict, Any, Optional, List
from datetime import datetime


class RiskService:
    def __init__(self):
        self._rules: List[Dict[str, Any]] = []
        self._init_rules()
    
    def _init_rules(self):
        self._rules = [
            {
                "rule_id": "high_refund_rate",
                "name": "高退款率",
                "description": "用户退款率超过阈值",
                "threshold": 0.3,
                "weight": 30,
            },
            {
                "rule_id": "frequent_complaint",
                "name": "频繁投诉",
                "description": "用户投诉次数过多",
                "threshold": 3,
                "weight": 40,
            },
            {
                "rule_id": "abnormal_order",
                "name": "异常订单",
                "description": "订单金额或数量异常",
                "weight": 20,
            },
        ]
    
    def check_order(
        self,
        order_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        tags = []
        reasons = []
        score = 0
        
        total_amount = float(order_data.get("total_amount", 0))
        if total_amount > 10000:
            tags.append("high_value")
            score += 10
            reasons.append("高金额订单")
        
        if order_data.get("status") in ["refunding", "refunded"]:
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
        
        return {
            "level": level,
            "tags": tags,
            "score": score,
            "reasons": reasons,
            "checked_at": datetime.now().isoformat(),
        }
    
    def check_conversation(
        self,
        messages: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        tags = []
        reasons = []
        score = 0
        
        risk_keywords = ["投诉", "举报", "差评", "退款", "赔偿", "法律", "律师"]
        
        for msg in messages:
            content = msg.get("content", "")
            for keyword in risk_keywords:
                if keyword in content:
                    if keyword not in tags:
                        tags.append(keyword)
                        score += 10
                        reasons.append(f"消息包含风险词：{keyword}")
        
        level = "low"
        if score >= 30:
            level = "high"
        elif score >= 15:
            level = "medium"
        
        return {
            "level": level,
            "tags": tags,
            "score": score,
            "reasons": reasons,
            "checked_at": datetime.now().isoformat(),
        }
    
    def get_rules(self) -> List[Dict[str, Any]]:
        return self._rules
