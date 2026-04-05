"""Conversation service — unified replacement for ConversationDomainService.

Handles conversation retrieval, message fetching, search, state transitions,
and business reference resolution.
"""
from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.adapters.registry import PlatformRegistry, AdapterRegistry
from app.services.platform_gateway_service import PlatformGatewayService

from providers.utils.fixture_loader import FixtureLoader
from providers.utils.sim_identity import get_primary_order_id

_CONVERSATION_SCENARIOS = {
    "wecom_kf": [
        {"scenario_key": "conversation_pending", "status": "pending"},
        {"scenario_key": "conversation_in_session", "status": "in_session"},
        {"scenario_key": "conversation_closed", "status": "closed"},
    ],
}


class ConversationService:
    """Conversation query service."""

    def __init__(self, gateway: PlatformGatewayService, registry: AdapterRegistry):
        self.gateway = gateway
        self.registry = registry

    def get_conversation(
        self,
        platform: str,
        conversation_id: str,
        official_run_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        try:
            raw_data = self.gateway.get_conversation(
                platform, conversation_id,
                official_run_id=official_run_id or self._resolve_official_run_id(platform, conversation_id),
            )
            return self._normalize_conversation(raw_data, platform)
        except Exception:
            pass

        if plat_conv := self._load_fixture_conversation(platform, conversation_id):
            return self._normalize_conversation(plat_conv, platform)

        return {
            "conversation_id": conversation_id,
            "platform": platform,
            "status": "unknown",
            "status_text": "未知",
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
        resolved_run_id = official_run_id or self._resolve_official_run_id(platform, conversation_id)
        try:
            provider = self.gateway.get_provider(platform)
            if provider:
                raw_data = provider.list_messages(conversation_id, limit, official_run_id=resolved_run_id)
                messages = self._normalize_messages(raw_data, platform, conversation_id)
                return {"conversation_id": conversation_id, "platform": platform,
                        "official_run_id": resolved_run_id, "messages": messages[:limit], "total": len(messages)}
        except Exception:
            pass

        if fixture_msg := self._load_fixture_messages(platform, conversation_id):
            messages = self._normalize_messages(fixture_msg, platform, conversation_id)
            return {"conversation_id": conversation_id, "platform": platform,
                    "messages": messages[:limit], "total": len(messages)}

        return {"conversation_id": conversation_id, "platform": platform, "messages": [], "total": 0}

    def search_conversations(
        self, platform: str, query: Dict[str, Any], skip: int = 0, limit: int = 100,
    ) -> Dict[str, Any]:
        conversations = []
        target_platforms = [
            p for p in _CONVERSATION_SCENARIOS if platform in (None, "", "all") or p == platform
        ]
        for plat in target_platforms:
            if plat_items := self._search_provider_conversations(plat, limit=max(limit, 100)):
                conversations.extend(plat_items)
            else:
                conversations.extend(self._load_fixture_search_conversations(plat))

        if query.get("status"):
            conversations = [c for c in conversations if c["status"] == query["status"]]

        return {"items": conversations[skip: skip + limit], "total": len(conversations)}

    def state_transition(self, platform: str, conversation_id: str, target_state: str) -> Dict[str, Any]:
        return {
            "conversation_id": conversation_id, "platform": platform,
            "previous_state": "unknown", "current_state": target_state,
            "transitioned_at": datetime.now().isoformat(),
        }

    def resolve_business_reference(
        self, platform: str, biz_id: str, official_run_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        resolved = {
            "requested_platform": platform, "requested_biz_id": biz_id,
            "effective_platform": platform, "effective_biz_id": biz_id,
            "biz_platform": None, "external_biz_id": biz_id, "official_run_id": official_run_id,
        }

        inferred = self._infer_order_platform(biz_id)
        if inferred:
            resolved["effective_platform"] = inferred
            resolved["effective_biz_id"] = self._resolve_effective_order_id(inferred, biz_id)
            resolved["biz_platform"] = inferred

        for candidate in self._lookup_conversation(platform, biz_id, official_run_id):
            ext = candidate.get("external_biz_id") or candidate.get("biz_id") or biz_id
            biz_plat = candidate.get("biz_platform") or inferred or platform
            resolved.update({
                "effective_platform": biz_plat, "effective_biz_id": self._resolve_effective_order_id(biz_plat, ext),
                "biz_platform": biz_plat, "external_biz_id": ext,
                "conversation_id": candidate.get("conversation_id") or candidate.get("id"),
                "official_run_id": candidate.get("official_run_id") or official_run_id,
            })
            break
        return resolved

    # -- internal helpers ---------------------------------------------------

    def _normalize_conversation(self, raw: Dict[str, Any], platform: str) -> Dict[str, Any]:
        create_time = raw.get("create_time") or raw.get("created_at")
        update_time = raw.get("update_time") or raw.get("resolved_at") or raw.get("updated_at")
        for ts_key, target in [("create_time", create_time), ("update_time", update_time)]:
            if target and str(target).isdigit() and len(str(target)) >= 10:
                ts = datetime.utcfromtimestamp(int(target)).isoformat()
                if ts_key == "create_time":
                    create_time = ts
                else:
                    update_time = ts

        customer = raw.get("customer", {})
        status = self._to_console_status(raw.get("status", "unknown"))
        return {
            "conversation_id": raw.get("conversation_id") or raw.get("code", ""),
            "platform": platform, "status": status,
            "status_text": raw.get("status_text") or self._status_text(status),
            "openid": raw.get("openid") or raw.get("open_id") or raw.get("external_userid"),
            "scene": raw.get("scene"),
            "created_at": create_time or datetime.now().isoformat(),
            "updated_at": update_time or datetime.now().isoformat(),
            "customer_id": raw.get("customer_id") or customer.get("user_id") or customer.get("external_userid"),
            "customer_pk": raw.get("customer_pk"),
            "customer_nick": raw.get("customer_nick") or customer.get("name") or customer.get("nickname"),
            "conversation_pk": raw.get("conversation_pk"),
            "biz_id": raw.get("biz_id"), "biz_type": raw.get("biz_type", "conversation"),
            "biz_platform": raw.get("biz_platform", platform),
            "external_biz_id": raw.get("external_biz_id"), "official_run_id": raw.get("official_run_id"),
            "message_count": raw.get("message_count"),
        }

    def _normalize_messages(self, raw: Any, platform: str, conversation_id: str) -> List[Dict[str, Any]]:
        raw_list = raw.get("messages", []) if isinstance(raw, dict) else (raw if isinstance(raw, list) else [])
        messages = []
        for msg in raw_list:
            if not isinstance(msg, dict):
                continue
            created_at = msg.get("created_at") or msg.get("create_time") or msg.get("send_time")
            if not created_at:
                created_at = msg.get("time")
            if created_at and str(created_at).isdigit() and len(str(created_at)) >= 10:
                created_at = datetime.utcfromtimestamp(int(created_at)).isoformat()

            sender_type = msg.get("sender_type")
            if not sender_type:
                role = msg.get("role", "")
                sender_type = "customer" if role == "customer" else ("agent" if role in {"servicer", "agent"} else ("customer" if msg.get("origin") == 3 else "agent"))

            messages.append({
                "msg_id": msg.get("msg_id") or msg.get("msgid", ""),
                "conversation_id": conversation_id, "platform": platform,
                "msg_type": msg.get("msg_type") or msg.get("msgtype", "text"),
                "content": msg.get("content") or msg.get("text", ""),
                "sender": msg.get("from_userid") or msg.get("sender") or msg.get("role") or msg.get("origin", "unknown"),
                "sender_type": sender_type,
                "created_at": created_at or datetime.now().isoformat(),
            })
        return messages

    def _search_provider_conversations(self, platform: str, limit: int) -> List[Dict[str, Any]]:
        try:
            provider = self.gateway.get_provider(platform)
        except Exception:
            return []
        if not provider or not hasattr(provider, "search_conversations"):
            return []
        try:
            result = provider.search_conversations(limit=limit)
        except Exception:
            return []
        items = result.get("items", []) if isinstance(result, dict) else []
        normalized = []
        for item in items:
            if not isinstance(item, dict):
                continue
            normalized.append({
                "id": item.get("id") or item.get("conversation_id", ""),
                "conversation_id": item.get("conversation_id") or item.get("id", ""),
                "conversation_pk": item.get("conversation_pk"), "platform": item.get("platform", platform),
                "customer_id": item.get("customer_id", ""), "customer_pk": item.get("customer_pk"),
                "customer_nick": item.get("customer_nick", "未知"),
                "status": self._to_console_status(item.get("status", "waiting")),
                "assigned_agent": item.get("assigned_agent"),
                "unread_count": item.get("unread_count", 0),
                "last_message_time": item.get("last_message_time") or item.get("updated_at") or datetime.now().isoformat(),
                "created_at": item.get("created_at") or datetime.now().isoformat(),
                "biz_id": item.get("biz_id"), "biz_type": item.get("biz_type"),
                "biz_platform": item.get("biz_platform"), "external_biz_id": item.get("external_biz_id"),
                "official_run_id": item.get("official_run_id"),
            })
        return normalized

    def _resolve_official_run_id(self, platform: str, conversation_id: str) -> Optional[str]:
        for item in self._search_provider_conversations(platform, limit=200):
            if item.get("conversation_id") == conversation_id or item.get("id") == conversation_id:
                return item.get("official_run_id")
        return None

    def _load_fixture_conversation(self, platform: str, conversation_id: str) -> Optional[Dict[str, Any]]:
        if platform == "wecom_kf":
            for conv in self._load_wecom_user_conversations():
                if conv.get("conversation_id") == conversation_id:
                    return conv
        for scenario in _CONVERSATION_SCENARIOS.get(platform, []):
            try:
                fixture = FixtureLoader.load(platform, scenario["scenario_key"], "success")
            except FileNotFoundError:
                continue
            conv_data = fixture.get("response", {})
            conv_data = conv_data.get("conversation", conv_data)
            if conv_data.get("conversation_id") == conversation_id or not conversation_id:
                return conv_data
        return None

    def _load_fixture_messages(self, platform: str, conversation_id: str) -> List[Dict[str, Any]]:
        if platform == "wecom_kf":
            for conv in self._load_wecom_user_conversations():
                if conv.get("conversation_id") == conversation_id:
                    return conv.get("messages", [])
        for scenario in _CONVERSATION_SCENARIOS.get(platform, []):
            try:
                fixture = FixtureLoader.load(platform, scenario["scenario_key"], "success")
            except FileNotFoundError:
                continue
            conv_data = fixture.get("response", {}).get("conversation", fixture.get("response", {}))
            if conv_data.get("conversation_id") == conversation_id or not conversation_id:
                return fixture.get("response", {}).get("msg_list", [])
        return []

    def _load_fixture_search_conversations(self, platform: str) -> List[Dict[str, Any]]:
        conversations = []
        if platform == "wecom_kf":
            for conv in self._load_wecom_user_conversations():
                customer = conv.get("customer", {})
                messages = conv.get("messages", [])
                conversations.append({
                    "id": conv.get("conversation_id", ""), "conversation_id": conv.get("conversation_id", ""),
                    "conversation_pk": conv.get("conversation_pk"), "platform": platform,
                    "customer_id": customer.get("user_id", ""), "customer_pk": conv.get("customer_pk"),
                    "customer_nick": customer.get("name", "未知"), "status": self._to_console_status(conv.get("status", "waiting")),
                    "assigned_agent": None, "unread_count": len([m for m in messages if m.get("role") == "customer"]),
                    "last_message_time": messages[-1].get("time") if messages else conv.get("created_at", datetime.now().isoformat()),
                    "created_at": conv.get("created_at", datetime.now().isoformat()),
                    "biz_id": conv.get("biz_id"), "biz_type": conv.get("biz_type"),
                    "biz_platform": conv.get("biz_platform"), "external_biz_id": conv.get("external_biz_id"),
                })
            return conversations

        for scenario in _CONVERSATION_SCENARIOS.get(platform, []):
            try:
                fixture = FixtureLoader.load(platform, scenario["scenario_key"], "success")
            except FileNotFoundError:
                continue
            conv_data = fixture.get("response", {}).get("conversation", {})
            msg_list = fixture.get("response", {}).get("msg_list", [])
            customer = conv_data.get("customer", {})
            conversations.append({
                "id": conv_data.get("conversation_id", ""), "conversation_id": conv_data.get("conversation_id", ""),
                "platform": platform, "customer_id": customer.get("external_userid", ""),
                "customer_pk": self._extract_int_suffix(customer.get("external_userid"), fallback=0),
                "customer_nick": customer.get("nickname", "未知"),
                "status": self._to_console_status(conv_data.get("status", "unknown")),
                "assigned_agent": None, "unread_count": len([m for m in msg_list if m.get("origin") == 3]),
                "last_message_time": datetime.now().isoformat(), "created_at": datetime.now().isoformat(),
                "biz_id": conv_data.get("conversation_id", ""), "biz_type": "conversation",
                "biz_platform": platform,
            })
        return conversations

    def _load_wecom_user_conversations(self) -> List[Dict[str, Any]]:
        _repo_root = Path(__file__).resolve().parents[5]
        users_dir = _repo_root / "apps/sim/official-sim-server/fixtures/wecom_kf/users"
        conversations = []
        if not users_dir.exists():
            return conversations
        for index, path in enumerate(sorted(users_dir.glob("*.json")), start=1):
            payload = json.loads(path.read_text(encoding="utf-8"))
            for conv_index, conversation in enumerate(payload.get("conversations", []), start=1):
                conv = dict(conversation)
                conv["customer"] = {"user_id": payload.get("user_id"), "name": payload.get("name"), "phone": payload.get("phone")}
                conv["customer_pk"] = self._extract_int_suffix(payload.get("user_id"), fallback=index)
                conv["conversation_pk"] = self._extract_int_suffix(conv.get("conversation_id"), fallback=conv_index)
                related_orders = conv.get("related_orders") or []
                external_biz_id = related_orders[0] if related_orders else conv.get("conversation_id")
                biz_platform = self._infer_order_platform(external_biz_id) or "wecom_kf"
                conv["external_biz_id"] = external_biz_id
                conv["biz_id"] = self._resolve_effective_order_id(biz_platform, external_biz_id)
                conv["biz_type"] = "order" if related_orders else "conversation"
                conv["biz_platform"] = biz_platform
                conversations.append(conv)
        return conversations

    def _lookup_conversation(self, platform, biz_id, official_run_id):
        """Find conversation by platform + biz_id (provider then fixtures)."""
        provider_items = self._search_provider_conversations(platform, limit=200)
        for item in provider_items:
            if official_run_id and item.get("official_run_id") == official_run_id:
                yield item
                return
            if item.get("conversation_id") == biz_id or item.get("id") == biz_id:
                yield item
                return
            if item.get("biz_id") == biz_id or item.get("external_biz_id") == biz_id:
                yield item
                return

        if platform == "wecom_kf":
            for item in self._load_wecom_user_conversations():
                if item.get("conversation_id") == biz_id or item.get("biz_id") == biz_id or item.get("external_biz_id") == biz_id:
                    yield item
                    return

    @staticmethod
    def _to_console_status(status: str) -> str:
        return {"in_session": "active", "pending": "waiting", "resolved": "closed", "closed": "closed"}.get(status, status or "waiting")

    @staticmethod
    def _status_text(status: str) -> str:
        return {"pending": "待接入", "in_session": "会话中", "closed": "已关闭", "waiting": "等待中"}.get(status, status)

    @staticmethod
    def _infer_order_platform(order_id) -> Optional[str]:
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

    @staticmethod
    def _resolve_effective_order_id(platform, order_id):
        if not order_id:
            return order_id
        if not platform or platform == "wecom_kf":
            return str(order_id)
        return get_primary_order_id(platform, str(order_id))

    @staticmethod
    def _extract_int_suffix(value, fallback=0) -> int:
        if not value:
            return fallback
        digits = "".join(ch for ch in value if ch.isdigit())
        return int(digits[-6:] or fallback)
