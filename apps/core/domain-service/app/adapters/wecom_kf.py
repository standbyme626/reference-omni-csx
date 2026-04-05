"""WeCom KF adapter: Conversation-only capability."""

from __future__ import annotations

from typing import Any

from app.models import Conversation, ConversationStatus, Message
from app.adapters.utils import parse_datetime

from .protocols import ConversationAdapter


class WeComKfConversationAdapter(ConversationAdapter):
    """Converts WeCom KF raw conversation data to unified Conversation / Message models."""

    def to_unified_conversation(self, platform_data: dict) -> Conversation:
        raw_status = platform_data.get("status", "")
        if raw_status == "in_session":
            status = ConversationStatus.IN_SESSION
        elif raw_status == "closed":
            status = ConversationStatus.CLOSED
        else:
            status = ConversationStatus.PENDING

        status_text_map = {
            ConversationStatus.PENDING: "待接入",
            ConversationStatus.IN_SESSION: "会话中",
            ConversationStatus.CLOSED: "已结束",
        }

        created_at = parse_datetime(platform_data.get("created_at"))
        updated_at = parse_datetime(platform_data.get("updated_at"))

        return Conversation(
            conversation_id=platform_data.get("conversation_id", ""),
            platform="wecom_kf",
            status=status,
            status_text=status_text_map.get(status, ""),
            openid=platform_data.get("openid"),
            scene=platform_data.get("scene"),
            created_at=created_at.isoformat(),
            updated_at=updated_at.isoformat(),
        )

    def to_unified_messages(self, platform_data: dict, limit: int = 100) -> list[Message]:
        raw_list: list[Any] = []
        if isinstance(platform_data, dict):
            raw_list = platform_data.get("messages") or platform_data.get("msg_list") or []
        elif isinstance(platform_data, list):
            raw_list = platform_data

        messages: list[Message] = []
        for msg in raw_list[:limit]:
            if not isinstance(msg, dict):
                continue

            sender_type = msg.get("sender_type")
            if not sender_type:
                role = msg.get("role", "")
                if role == "customer":
                    sender_type = "customer"
                elif role in {"servicer", "agent"}:
                    sender_type = "agent"
                else:
                    sender_type = "customer" if msg.get("origin") == 3 else "agent"

            created_at = parse_datetime(
                msg.get("created_at")
                or msg.get("create_time")
                or msg.get("send_time")
                or msg.get("time")
            )

            messages.append(Message(
                msg_id=msg.get("msg_id") or msg.get("msgid", ""),
                conversation_id=msg.get("conversation_id", ""),
                platform="wecom_kf",
                msg_type=msg.get("msg_type") or msg.get("msgtype", "text"),
                content=msg.get("content") or msg.get("text", ""),
                sender=msg.get("from_userid") or msg.get("sender", ""),
                sender_type=sender_type,
                created_at=created_at.isoformat(),
            ))

        return messages
