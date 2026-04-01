from typing import Dict, Any, Optional, List
from datetime import datetime


class QualityService:
    def __init__(self):
        self._rules: List[Dict[str, Any]] = []
        self._init_rules()
    
    def _init_rules(self):
        self._rules = [
            {
                "rule_id": "response_time",
                "name": "响应时效",
                "description": "首次响应时间应在30秒内",
                "threshold_seconds": 30,
                "weight": 20,
            },
            {
                "rule_id": "resolution_time",
                "name": "解决时效",
                "description": "问题解决时间应在5分钟内",
                "threshold_seconds": 300,
                "weight": 30,
            },
            {
                "rule_id": "politeness",
                "name": "礼貌用语",
                "description": "回复应包含礼貌用语",
                "weight": 20,
            },
        ]
    
    def check_reply(
        self,
        reply_content: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        issues = []
        suggestions = []
        score = 100
        
        polite_words = ["您好", "请", "谢谢", "抱歉", "不好意思"]
        has_polite = any(word in reply_content for word in polite_words)
        
        if not has_polite:
            issues.append("回复缺少礼貌用语")
            suggestions.append("建议添加'您好'、'请'等礼貌用语")
            score -= 10
        
        if len(reply_content) < 10:
            issues.append("回复内容过短")
            suggestions.append("建议提供更详细的回复")
            score -= 15
        
        if len(reply_content) > 500:
            issues.append("回复内容过长")
            suggestions.append("建议精简回复内容")
            score -= 5
        
        return {
            "score": max(0, score),
            "issues": issues,
            "suggestions": suggestions,
            "checked_at": datetime.now().isoformat(),
        }
    
    def check_conversation(
        self,
        messages: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        issues = []
        suggestions = []
        score = 100
        
        if not messages:
            return {
                "score": 0,
                "issues": ["会话无消息"],
                "suggestions": [],
                "checked_at": datetime.now().isoformat(),
            }
        
        agent_messages = [m for m in messages if m.get("sender_type") == "agent"]
        if not agent_messages:
            issues.append("会话中无客服回复")
            suggestions.append("客服应及时回复客户消息")
            score -= 30
        
        first_agent_msg = None
        first_customer_msg = None
        for m in messages:
            if m.get("sender_type") == "customer" and not first_customer_msg:
                first_customer_msg = m
            if m.get("sender_type") == "agent" and not first_agent_msg:
                first_agent_msg = m
        
        if first_customer_msg and first_agent_msg:
            first_response_time = self._calculate_response_time(
                first_customer_msg,
                first_agent_msg,
            )
            if first_response_time and first_response_time > 30:
                issues.append(f"首次响应时间过长：{first_response_time}秒")
                suggestions.append("建议在30秒内响应客户消息")
                score -= 20
        
        return {
            "score": max(0, score),
            "issues": issues,
            "suggestions": suggestions,
            "message_count": len(messages),
            "agent_message_count": len(agent_messages),
            "checked_at": datetime.now().isoformat(),
        }
    
    def get_rules(self) -> List[Dict[str, Any]]:
        return self._rules
    
    def _calculate_response_time(
        self,
        customer_msg: Dict[str, Any],
        agent_msg: Dict[str, Any],
    ) -> Optional[int]:
        try:
            customer_time = datetime.fromisoformat(customer_msg.get("created_at", ""))
            agent_time = datetime.fromisoformat(agent_msg.get("created_at", ""))
            return int((agent_time - customer_time).total_seconds())
        except Exception:
            return None
