from datetime import datetime
from typing import Any, Dict, List, Optional

from app.services.context_resolver import ContextResolver
from app.services.reply_generator import ReplyGenerator


class RecommendationService:
    def __init__(self, context_resolver: ContextResolver, reply_generator: ReplyGenerator):
        self.context_resolver = context_resolver
        self.reply_generator = reply_generator
    
    def get_reply_recommendations(
        self,
        platform: str,
        biz_id: str,
        biz_type: str = "order",
        intent: Optional[str] = None,
        max_candidates: int = 5,
        official_run_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        context = self.context_resolver.get_context(
            platform,
            biz_id,
            official_run_id=official_run_id,
        )

        candidates = self.reply_generator.generate_replies(context, intent)

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
        official_run_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        context = self.context_resolver.get_context(
            platform,
            biz_id,
            official_run_id=official_run_id,
        )

        candidates = self.reply_generator.generate_actions(context)

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
        official_run_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        context = self.context_resolver.get_context(
            platform,
            biz_id,
            official_run_id=official_run_id,
        )

        return self.reply_generator.evaluate_escalation(context, reason)
