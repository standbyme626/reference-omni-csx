from enum import Enum
from typing import Optional

from pydantic import BaseModel


class ConversationStatus(str, Enum):
    PENDING = "pending"
    IN_SESSION = "in_session"
    CLOSED = "closed"


class Message(BaseModel):
    msg_id: str = ""
    conversation_id: str = ""
    platform: str = ""
    msg_type: str = "text"
    content: str = ""
    sender: str = ""
    sender_type: str = "customer"
    created_at: str = ""


class Conversation(BaseModel):
    conversation_id: str
    platform: str
    status: ConversationStatus = ConversationStatus.PENDING
    status_text: str = ""
    customer_id: Optional[str] = None
    customer_pk: Optional[int] = None
    customer_nick: Optional[str] = None
    conversation_pk: Optional[int] = None
    openid: Optional[str] = None
    scene: Optional[str] = None
    message_count: Optional[int] = None
    assigned_agent: Optional[str] = None
    unread_count: int = 0
    last_message_time: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""
    biz_id: Optional[str] = None
    biz_type: str = "conversation"
    biz_platform: Optional[str] = None
    external_biz_id: Optional[str] = None
    official_run_id: Optional[str] = None
