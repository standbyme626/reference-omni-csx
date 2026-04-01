from typing import Dict, Any, Optional, List
from datetime import datetime

from app.services.platform_gateway_service import PlatformGatewayService
from models.unified import Platform


class ConversationDomainService:
    def __init__(self, gateway: PlatformGatewayService):
        self.gateway = gateway
    
    def get_conversation(self, platform: str, conversation_id: str) -> Dict[str, Any]:
        platform_enum = Platform(platform)
        
        raw_data = self.gateway.get_conversation(platform_enum, conversation_id)
        
        return self._normalize_conversation(raw_data, platform)
    
    def get_conversation_messages(
        self,
        platform: str,
        conversation_id: str,
        limit: int = 100,
    ) -> Dict[str, Any]:
        platform_enum = Platform(platform)
        
        provider = self.gateway.get_provider(platform_enum)
        if not provider:
            raise ValueError(f"Platform not supported: {platform}")
        
        raw_data = provider.list_messages(conversation_id, limit)
        
        messages = self._normalize_messages(raw_data, platform, conversation_id)
        
        return {
            "conversation_id": conversation_id,
            "platform": platform,
            "messages": messages,
            "total": len(messages),
        }
    
    def search_conversations(
        self,
        platform: str,
        query: Dict[str, Any],
        skip: int = 0,
        limit: int = 100,
    ) -> Dict[str, Any]:
        mock_conversations = [
            {
                "id": "CONV_001",
                "platform": "wecom_kf",
                "customer_id": "CUSTOMER_001",
                "customer_nick": "张三",
                "status": "active",
                "assigned_agent": "agent_001",
                "unread_count": 2,
                "last_message_time": datetime.now().isoformat(),
                "created_at": datetime.now().isoformat(),
            },
            {
                "id": "CONV_002",
                "platform": "taobao",
                "customer_id": "CUSTOMER_002",
                "customer_nick": "李四",
                "status": "waiting",
                "assigned_agent": None,
                "unread_count": 1,
                "last_message_time": datetime.now().isoformat(),
                "created_at": datetime.now().isoformat(),
            },
            {
                "id": "CONV_003",
                "platform": "douyin_shop",
                "customer_id": "CUSTOMER_003",
                "customer_nick": "王五",
                "status": "closed",
                "assigned_agent": "agent_002",
                "unread_count": 0,
                "last_message_time": datetime.now().isoformat(),
                "created_at": datetime.now().isoformat(),
            },
        ]

        filtered = mock_conversations
        if platform and platform != "all":
            filtered = [c for c in filtered if c["platform"] == platform]
        if query.get("status"):
            filtered = [c for c in filtered if c["status"] == query["status"]]

        total = len(filtered)
        items = filtered[skip : skip + limit]

        return {
            "items": items,
            "total": total,
        }
    
    def state_transition(
        self,
        platform: str,
        conversation_id: str,
        target_state: str,
    ) -> Dict[str, Any]:
        return {
            "conversation_id": conversation_id,
            "platform": platform,
            "previous_state": "unknown",
            "current_state": target_state,
            "transitioned_at": datetime.now().isoformat(),
        }
    
    def _normalize_conversation(
        self,
        raw: Dict[str, Any],
        platform: str,
    ) -> Dict[str, Any]:
        return {
            "conversation_id": raw.get("conversation_id") or raw.get("code", ""),
            "platform": platform,
            "status": raw.get("status", "unknown"),
            "status_text": self._get_status_text(raw.get("status", "unknown")),
            "openid": raw.get("openid") or raw.get("open_id") or raw.get("external_userid"),
            "scene": raw.get("scene"),
            "created_at": raw.get("created_at") or datetime.now().isoformat(),
            "updated_at": raw.get("updated_at") or datetime.now().isoformat(),
        }
    
    def _normalize_messages(
        self,
        raw: Dict[str, Any],
        platform: str,
        conversation_id: str,
    ) -> List[Dict[str, Any]]:
        messages = []
        
        raw_list = raw.get("messages") or raw.get("msg_list") or []
        
        for msg in raw_list:
            messages.append({
                "msg_id": msg.get("msg_id") or msg.get("msgid", ""),
                "conversation_id": conversation_id,
                "platform": platform,
                "msg_type": msg.get("msg_type") or msg.get("msgtype", "text"),
                "content": msg.get("content") or msg.get("text", ""),
                "sender": msg.get("sender") or msg.get("origin", "unknown"),
                "sender_type": msg.get("sender_type") or ("customer" if msg.get("origin") == 3 else "agent"),
                "created_at": msg.get("created_at") or msg.get("send_time") or datetime.now().isoformat(),
            })
        
        return messages
    
    def _get_status_text(self, status: str) -> str:
        status_map = {
            "pending": "待接入",
            "in_session": "会话中",
            "closed": "已关闭",
            "waiting": "等待中",
        }
        return status_map.get(status, status)
