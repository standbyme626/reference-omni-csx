from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class MessageResponse(BaseModel):
    msg_id: str
    conversation_id: str
    platform: str
    msg_type: str
    content: str
    sender: str
    sender_type: str
    created_at: datetime


class ConversationResponse(BaseModel):
    conversation_id: str
    platform: str
    status: str
    status_text: Optional[str] = None
    openid: Optional[str] = None
    scene: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    last_message: Optional[MessageResponse] = None


class ConversationListResponse(BaseModel):
    conversations: List[ConversationResponse]
    total: int


class ConversationDetailResponse(BaseModel):
    conversation: ConversationResponse
    messages: List[MessageResponse] = Field(default_factory=list)
    message_count: int = 0
