import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.services.platform_gateway_service import PlatformGatewayService
from models.unified import Platform

from providers.utils.sim_identity import get_primary_order_id

# Conversation scenario fixtures from the sim layer.
_CONVERSATION_SCENARIOS = {
    "wecom_kf": [
        {"scenario_key": "conversation_pending", "status": "pending"},
        {"scenario_key": "conversation_in_session", "status": "in_session"},
        {"scenario_key": "conversation_closed", "status": "closed"},
    ],
}

def _load_conversation_fixture(scenario_key: str, platform: str) -> Dict[str, Any]:
    """Load a conversation fixture from the sim-layer fixture store."""
    from providers.utils.fixture_loader import FixtureLoader

    fixture = FixtureLoader.load(platform, scenario_key, "success")
    response = fixture.get("response", {})
    conv_data = response.get("conversation", response)
    msg_list = response.get("msg_list", [])
    return {
        "conversation_data": conv_data,
        "msg_list": msg_list,
    }


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[5]


def _load_wecom_user_conversations() -> List[Dict[str, Any]]:
    users_dir = _repo_root() / "apps/sim/official-sim-server/fixtures/wecom_kf/users"
    conversations: List[Dict[str, Any]] = []
    if not users_dir.exists():
        return conversations

    for path in sorted(users_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        for index, conversation in enumerate(payload.get("conversations", []), start=1):
            conversation_payload = dict(conversation)
            conversation_payload["customer"] = {
                "user_id": payload.get("user_id"),
                "name": payload.get("name"),
                "phone": payload.get("phone"),
            }
            conversation_payload["customer_pk"] = _extract_int_suffix(payload.get("user_id"), fallback=index)
            conversation_payload["conversation_pk"] = _extract_int_suffix(
                conversation.get("conversation_id"),
                fallback=index,
            )
            related_orders = conversation.get("related_orders") or []
            external_biz_id = related_orders[0] if related_orders else conversation.get("conversation_id")
            biz_platform = _infer_order_platform(external_biz_id) or "wecom_kf"
            conversation_payload["external_biz_id"] = external_biz_id
            conversation_payload["biz_id"] = _resolve_effective_order_id(biz_platform, external_biz_id)
            conversation_payload["biz_type"] = "order" if related_orders else "conversation"
            conversation_payload["biz_platform"] = biz_platform
            conversations.append(conversation_payload)
    return conversations


def _extract_int_suffix(value: Optional[str], fallback: int = 0) -> int:
    if not value:
        return fallback
    digits = "".join(ch for ch in value if ch.isdigit())
    return int(digits[-6:] or fallback)


def _infer_order_platform(order_id: Optional[str]) -> Optional[str]:
    if not order_id:
        return None
    upper = order_id.upper()
    if upper.startswith("JD_") or "JD_ORDER" in upper:
        return "jd"
    if upper.startswith("TB_") or "TAOBAO" in upper:
        return "taobao"
    if upper.startswith("DY_") or upper.startswith("DS_") or "DOUYIN" in upper:
        return "douyin_shop"
    if upper.startswith("XHS_"):
        return "xhs"
    if upper.startswith("KS_") or "KUAISHOU" in upper:
        return "kuaishou"
    return None


def _resolve_effective_order_id(platform: Optional[str], order_id: Optional[str]) -> Optional[str]:
    if not order_id:
        return order_id
    if not platform or platform == "wecom_kf":
        return str(order_id)
    return get_primary_order_id(platform, str(order_id))


def _to_console_status(status: str) -> str:
    mapping = {
        "in_session": "active",
        "pending": "waiting",
        "resolved": "closed",
        "closed": "closed",
    }
    return mapping.get(status, status or "waiting")


class ConversationDomainService:
    def __init__(self, gateway: PlatformGatewayService):
        self.gateway = gateway

    def get_conversation(
        self,
        platform: str,
        conversation_id: str,
        official_run_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        platform_enum = Platform(platform)
        try:
            raw_data = self.gateway.get_conversation(
                platform_enum,
                conversation_id,
                official_run_id=official_run_id or self._resolve_official_run_id(platform, conversation_id),
            )
            return self._normalize_conversation(raw_data, platform)
        except Exception:
            pass

        fixture_conversation = self._load_fixture_conversation(platform, conversation_id)
        if fixture_conversation is not None:
            return self._normalize_conversation(fixture_conversation, platform)

        return {
            "conversation_id": conversation_id,
            "platform": platform,
            "status": "unknown",
            "status_text": "未知",
            "openid": None,
            "scene": None,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

    def get_conversation_messages(
        self,
        platform: str,
        conversation_id: str,
        limit: int = 100,
        official_run_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        platform_enum = Platform(platform)
        resolved_run_id = official_run_id or self._resolve_official_run_id(platform, conversation_id)
        try:
            provider = self.gateway.get_provider(platform_enum)
            if provider:
                try:
                    raw_data = provider.list_messages(
                        conversation_id,
                        limit,
                        official_run_id=resolved_run_id,
                    )
                except TypeError:
                    raw_data = provider.list_messages(conversation_id, limit)
                messages = self._normalize_messages(raw_data, platform, conversation_id)
                return {
                    "conversation_id": conversation_id,
                    "platform": platform,
                    "official_run_id": resolved_run_id,
                    "messages": messages[:limit],
                    "total": len(messages),
                }
        except Exception:
            pass

        fixture_messages = self._load_fixture_messages(platform, conversation_id)
        if fixture_messages:
            messages = self._normalize_messages(fixture_messages, platform, conversation_id)
            return {
                "conversation_id": conversation_id,
                "platform": platform,
                "messages": messages[:limit],
                "total": len(messages),
            }

        return {
            "conversation_id": conversation_id,
            "platform": platform,
            "messages": [],
            "total": 0,
        }

    def search_conversations(
        self,
        platform: str,
        query: Dict[str, Any],
        skip: int = 0,
        limit: int = 100,
    ) -> Dict[str, Any]:
        conversations = []

        target_platforms = [
            plat
            for plat in _CONVERSATION_SCENARIOS
            if platform in (None, "", "all") or plat == platform
        ]

        for plat in target_platforms:
            provider_items = self._search_provider_conversations(plat, limit=max(limit, 100))
            if provider_items:
                conversations.extend(provider_items)
                continue
            conversations.extend(self._load_fixture_search_conversations(plat))

        if query.get("status"):
            conversations = [c for c in conversations if c["status"] == query["status"]]

        total = len(conversations)
        items = conversations[skip: skip + limit]

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

    def _search_provider_conversations(self, platform: str, limit: int) -> List[Dict[str, Any]]:
        try:
            provider = self.gateway.get_provider(Platform(platform))
        except Exception:
            return []

        if not provider or not hasattr(provider, "search_conversations"):
            return []

        try:
            result = provider.search_conversations(limit=limit)
        except Exception:
            return []

        items = result.get("items", []) if isinstance(result, dict) else []
        normalized: List[Dict[str, Any]] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            normalized.append(
                {
                    "id": item.get("id") or item.get("conversation_id", ""),
                    "conversation_id": item.get("conversation_id") or item.get("id", ""),
                    "conversation_pk": item.get("conversation_pk"),
                    "platform": item.get("platform", platform),
                    "customer_id": item.get("customer_id", ""),
                    "customer_pk": item.get("customer_pk"),
                    "customer_nick": item.get("customer_nick", "未知"),
                    "status": _to_console_status(item.get("status", "waiting")),
                    "assigned_agent": item.get("assigned_agent"),
                    "unread_count": item.get("unread_count", 0),
                    "last_message_time": item.get(
                        "last_message_time",
                        item.get("updated_at", datetime.now().isoformat()),
                    ),
                    "created_at": item.get("created_at", datetime.now().isoformat()),
                    "biz_id": item.get("biz_id"),
                    "biz_type": item.get("biz_type"),
                    "biz_platform": item.get("biz_platform"),
                    "external_biz_id": item.get("external_biz_id"),
                    "official_run_id": item.get("official_run_id"),
                }
            )
        return normalized

    def _resolve_official_run_id(self, platform: str, conversation_id: str) -> Optional[str]:
        provider_items = self._search_provider_conversations(platform, limit=200)
        for item in provider_items:
            if item.get("conversation_id") == conversation_id or item.get("id") == conversation_id:
                return item.get("official_run_id")
        return None

    def resolve_business_reference(
        self,
        platform: str,
        biz_id: str,
        official_run_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        resolved: Dict[str, Any] = {
            "requested_platform": platform,
            "requested_biz_id": biz_id,
            "effective_platform": platform,
            "effective_biz_id": biz_id,
            "biz_platform": None,
            "external_biz_id": biz_id,
            "official_run_id": official_run_id,
        }

        inferred_platform = _infer_order_platform(biz_id)
        if inferred_platform:
            resolved["effective_platform"] = inferred_platform
            resolved["effective_biz_id"] = _resolve_effective_order_id(inferred_platform, biz_id)
            resolved["biz_platform"] = inferred_platform

        conversation_item = self._resolve_provider_business_reference(
            platform,
            biz_id,
            official_run_id=official_run_id,
        )
        if not conversation_item:
            conversation_item = self._resolve_fixture_business_reference(platform, biz_id)
        if not conversation_item:
            return resolved

        external_biz_id = (
            conversation_item.get("external_biz_id")
            or conversation_item.get("biz_id")
            or biz_id
        )
        biz_platform = conversation_item.get("biz_platform") or inferred_platform or platform

        resolved.update(
            {
                "effective_platform": biz_platform,
                "effective_biz_id": _resolve_effective_order_id(biz_platform, external_biz_id),
                "biz_platform": biz_platform,
                "external_biz_id": external_biz_id,
                "conversation_id": conversation_item.get("conversation_id") or conversation_item.get("id"),
                "official_run_id": conversation_item.get("official_run_id") or official_run_id,
            }
        )
        return resolved

    def _resolve_provider_business_reference(
        self,
        platform: str,
        biz_id: str,
        official_run_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        provider_items = self._search_provider_conversations(platform, limit=200)
        for item in provider_items:
            if official_run_id and item.get("official_run_id") == official_run_id:
                return item
            if item.get("conversation_id") == biz_id or item.get("id") == biz_id:
                return item
            if item.get("biz_id") == biz_id or item.get("external_biz_id") == biz_id:
                return item
        return None

    def _resolve_fixture_business_reference(
        self,
        platform: str,
        biz_id: str,
    ) -> Optional[Dict[str, Any]]:
        if platform != "wecom_kf":
            return None
        for item in _load_wecom_user_conversations():
            if item.get("conversation_id") == biz_id:
                return item
            if item.get("biz_id") == biz_id or item.get("external_biz_id") == biz_id:
                return item
        return None

    def _load_fixture_conversation(self, platform: str, conversation_id: str) -> Optional[Dict[str, Any]]:
        if platform == "wecom_kf":
            for conversation in _load_wecom_user_conversations():
                if conversation.get("conversation_id") == conversation_id:
                    return conversation

        scenarios = _CONVERSATION_SCENARIOS.get(platform, [])
        for scenario in scenarios:
            try:
                fixture = _load_conversation_fixture(scenario["scenario_key"], platform)
            except FileNotFoundError:
                continue
            conv_data = fixture["conversation_data"]
            if conv_data.get("conversation_id") == conversation_id or not conversation_id:
                return conv_data
        return None

    def _load_fixture_messages(self, platform: str, conversation_id: str) -> List[Dict[str, Any]]:
        if platform == "wecom_kf":
            for conversation in _load_wecom_user_conversations():
                if conversation.get("conversation_id") == conversation_id:
                    return conversation.get("messages", [])

        scenarios = _CONVERSATION_SCENARIOS.get(platform, [])
        for scenario in scenarios:
            try:
                fixture = _load_conversation_fixture(scenario["scenario_key"], platform)
            except FileNotFoundError:
                continue
            conv_data = fixture["conversation_data"]
            if conv_data.get("conversation_id") == conversation_id or not conversation_id:
                return fixture.get("msg_list", [])
        return []

    def _load_fixture_search_conversations(self, platform: str) -> List[Dict[str, Any]]:
        conversations: List[Dict[str, Any]] = []
        if platform == "wecom_kf":
            for conversation in _load_wecom_user_conversations():
                customer = conversation.get("customer", {})
                messages = conversation.get("messages", [])
                conversations.append(
                    {
                        "id": conversation.get("conversation_id", ""),
                        "conversation_id": conversation.get("conversation_id", ""),
                        "conversation_pk": conversation.get("conversation_pk"),
                        "platform": platform,
                        "customer_id": customer.get("user_id", ""),
                        "customer_pk": conversation.get("customer_pk"),
                        "customer_nick": customer.get("name", "未知"),
                        "status": _to_console_status(conversation.get("status", "waiting")),
                        "assigned_agent": None,
                        "unread_count": len([m for m in messages if m.get("role") == "customer"]),
                        "last_message_time": (
                            messages[-1].get("time")
                            if messages
                            else conversation.get("created_at", datetime.now().isoformat())
                        ),
                        "created_at": conversation.get("created_at", datetime.now().isoformat()),
                        "biz_id": conversation.get("biz_id"),
                        "biz_type": conversation.get("biz_type"),
                        "biz_platform": conversation.get("biz_platform"),
                        "external_biz_id": conversation.get("external_biz_id"),
                    }
                )
            return conversations

        scenarios = _CONVERSATION_SCENARIOS.get(platform, [])
        for scenario in scenarios:
            try:
                fixture = _load_conversation_fixture(scenario["scenario_key"], platform)
            except FileNotFoundError:
                continue
            conv_data = fixture["conversation_data"]
            msg_list = fixture.get("msg_list", [])
            customer = conv_data.get("customer", {})
            conversations.append(
                {
                    "id": conv_data.get("conversation_id", ""),
                    "conversation_id": conv_data.get("conversation_id", ""),
                    "platform": platform,
                    "customer_id": customer.get("external_userid", ""),
                    "customer_pk": _extract_int_suffix(customer.get("external_userid"), fallback=0),
                    "customer_nick": customer.get("nickname", "未知"),
                    "status": _to_console_status(conv_data.get("status", "unknown")),
                    "assigned_agent": None,
                    "unread_count": len([m for m in msg_list if m.get("origin") == 3]),
                    "last_message_time": datetime.now().isoformat(),
                    "created_at": datetime.now().isoformat(),
                    "biz_id": conv_data.get("conversation_id", ""),
                    "biz_type": "conversation",
                    "biz_platform": platform,
                }
            )
        return conversations

    def _normalize_conversation(
        self,
        raw: Dict[str, Any],
        platform: str,
    ) -> Dict[str, Any]:
        create_time = raw.get("create_time")
        if create_time and str(create_time).isdigit() and len(str(create_time)) >= 10:
            create_time = datetime.utcfromtimestamp(int(create_time)).isoformat()
        if not create_time:
            create_time = raw.get("created_at")
        update_time = raw.get("update_time")
        if update_time and str(update_time).isdigit() and len(str(update_time)) >= 10:
            update_time = datetime.utcfromtimestamp(int(update_time)).isoformat()
        if not update_time:
            update_time = raw.get("resolved_at") or raw.get("updated_at")
        customer = raw.get("customer", {})
        status = _to_console_status(raw.get("status", "unknown"))
        return {
            "conversation_id": raw.get("conversation_id") or raw.get("code", ""),
            "platform": platform,
            "status": status,
            "status_text": raw.get("status_text") or self._get_status_text(status),
            "openid": raw.get("openid") or raw.get("open_id") or raw.get("external_userid"),
            "scene": raw.get("scene"),
            "created_at": create_time or datetime.now().isoformat(),
            "updated_at": update_time or datetime.now().isoformat(),
            "customer_id": raw.get("customer_id") or customer.get("user_id") or customer.get("external_userid"),
            "customer_pk": raw.get("customer_pk"),
            "customer_nick": raw.get("customer_nick") or customer.get("name") or customer.get("nickname"),
            "conversation_pk": raw.get("conversation_pk"),
            "biz_id": raw.get("biz_id"),
            "biz_type": raw.get("biz_type", "conversation"),
            "biz_platform": raw.get("biz_platform", platform),
            "external_biz_id": raw.get("external_biz_id"),
            "official_run_id": raw.get("official_run_id"),
            "message_count": raw.get("message_count"),
        }

    def _normalize_messages(
        self,
        raw_payload: Any,
        platform: str,
        conversation_id: str,
    ) -> List[Dict[str, Any]]:
        if isinstance(raw_payload, dict):
            raw_list = raw_payload.get("messages") or raw_payload.get("msg_list") or []
        elif isinstance(raw_payload, list):
            raw_list = raw_payload
        else:
            raw_list = []

        messages = []
        for msg in raw_list:
            if not isinstance(msg, dict):
                continue
            created_at = (
                msg.get("created_at")
                or msg.get("create_time")
                or msg.get("send_time")
            )
            if not created_at:
                created_at = msg.get("time")
            if created_at and str(created_at).isdigit() and len(str(created_at)) >= 10:
                created_at = datetime.utcfromtimestamp(int(created_at)).isoformat()
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
                "conversation_id": conversation_id,
                "platform": platform,
                "msg_type": msg.get("msg_type") or msg.get("msgtype", "text"),
                "content": msg.get("content") or msg.get("text", ""),
                "sender": msg.get("from_userid") or msg.get("sender") or msg.get("role") or msg.get("origin", "unknown"),
                "sender_type": sender_type,
                "created_at": created_at or datetime.now().isoformat(),
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
