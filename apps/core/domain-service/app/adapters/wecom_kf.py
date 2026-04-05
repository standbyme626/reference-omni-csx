"""WeCom KF adapter: Conversation-only capability."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from .protocols import ConversationAdapter


class WeComKfConversationAdapter(ConversationAdapter):
    """Converts WeCom KF raw conversation data to unified conversation dict."""

    def to_unified_conversation(self, platform_data: Dict[str, Any]) -> Dict[str, Any]:
        now = datetime.now()
        created_at_raw = platform_data.get("created_at", now.isoformat())
        updated_at_raw = platform_data.get("updated_at", now.isoformat())

        if created_at_raw == now.isoformat():
            created_at = created_at_raw
        elif isinstance(created_at_raw, (int, float)):
            created_at = datetime.fromtimestamp(created_at_raw).isoformat()
        else:
            try:
                created_at = datetime.fromisoformat(str(created_at_raw)).isoformat()
            except (TypeError, ValueError):
                created_at = now.isoformat()

        if updated_at_raw == now.isoformat():
            updated_at = updated_at_raw
        elif isinstance(updated_at_raw, (int, float)):
            updated_at = datetime.fromtimestamp(updated_at_raw).isoformat()
        else:
            try:
                updated_at = datetime.fromisoformat(str(updated_at_raw)).isoformat()
            except (TypeError, ValueError):
                updated_at = now.isoformat()

        status = "in_session" if platform_data.get("status") == "in_session" else "pending"

        return {
            "conversation_id": platform_data.get("conversation_id", ""),
            "platform": "wecom_kf",
            "status": status,
            "status_text": "会话中" if status == "in_session" else "待接入",
            "openid": platform_data.get("openid"),
            "scene": platform_data.get("scene"),
            "created_at": created_at,
            "updated_at": updated_at,
        }

    def to_unified_messages(self, platform_data: Dict[str, Any], limit: int = 100) -> list[Dict[str, Any]]:
        raw_list = []
        if isinstance(platform_data, dict):
            raw_list = platform_data.get("messages") or platform_data.get("msg_list") or []
        elif isinstance(platform_data, list):
            raw_list = platform_data

        messages = []
        for msg in raw_list[:limit]:
            if not isinstance(msg, dict):
                continue

            created_at_raw = (
                msg.get("created_at")
                or msg.get("create_time")
                or msg.get("send_time")
                or msg.get("time")
            )

            if created_at_raw and str(created_at_raw).isdigit() and len(str(created_at_raw)) >= 10:
                created_at = datetime.utcfromtimestamp(int(created_at_raw)).isoformat()
            elif created_at_raw:
                try:
                    created_at = datetime.fromisoformat(str(created_at_raw)).isoformat()
                except (TypeError, ValueError):
                    created_at = datetime.now().isoformat()
            else:
                created_at = datetime.now().isoformat()

            sender_type = msg.get("sender_type")
            if not sender_type:
                if msg.get("role") == "customer":
                    sender_type = "customer"
                elif msg.get("role") in {"servicer", "agent"}:
                    sender_type = "agent"
                else:
                    sender_type = "customer" if msg.get("origin") == 3 else "agent"

            messages.append({
                "msg_id": msg.get("msg_id") or msg.get("msgid", ""),
                "conversation_id": msg.get("conversation_id", ""),
                "platform": "wecom_kf",
                "msg_type": msg.get("msg_type") or msg.get("msgtype", "text"),
                "content": msg.get("content") or msg.get("text", ""),
                "sender": msg.get("from_userid") or msg.get("sender") or msg.get("role") or msg.get("origin", "unknown"),
                "sender_type": sender_type,
                "created_at": created_at,
            })

        return messages
