import os
from typing import Any, Dict

from .base import ReplyAdapter, ReplyAdapterError, ReplySource
from .official_sim import OfficialSimReplyAdapter
from .stub import StubReplyAdapter


class UnifiedReplyAdapter(ReplyAdapter):
    def __init__(
        self,
        use_official_sim: bool = True,
        allow_stub_fallback: bool = False,
        official_sim_base_url: str = "",
        platform: str = "taobao"
    ):
        self.use_official_sim = use_official_sim
        self.allow_stub_fallback = allow_stub_fallback
        self.platform = platform
        resolved_base_url = (
            official_sim_base_url
            or os.getenv("OFFICIAL_SIM_BASE_URL")
            or "http://localhost:8001"
        )
        self.official_adapter = OfficialSimReplyAdapter(base_url=resolved_base_url)
        self.stub_adapter = StubReplyAdapter(platform=platform)

    def get_reply(
        self,
        run_id: str,
        user_message: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        if self.use_official_sim:
            result = self.official_adapter.get_reply(run_id, user_message, context)
            if result.get("fallback_to_stub"):
                if self.allow_stub_fallback:
                    return self.stub_adapter.get_reply(run_id, user_message, context)
                raise ReplyAdapterError(
                    str(
                        result.get("error")
                        or result.get("text")
                        or "official-sim reply unavailable"
                    )
                )
            return result
        else:
            return self.stub_adapter.get_reply(run_id, user_message, context)

    def get_source(self) -> ReplySource:
        if self.use_official_sim:
            return ReplySource.OFFICIAL_SIM
        else:
            return ReplySource.STUB

    def switch_mode(self, use_official_sim: bool):
        self.use_official_sim = use_official_sim

    def set_allow_stub_fallback(self, allow_stub_fallback: bool):
        self.allow_stub_fallback = allow_stub_fallback

    def set_platform(self, platform: str):
        self.platform = platform
        self.stub_adapter = StubReplyAdapter(platform=platform)

    def get_available_modes(self) -> Dict[str, bool]:
        return {
            "use_official_sim": self.use_official_sim,
            "allow_stub_fallback": self.allow_stub_fallback,
            "official_sim_available": self._check_official_sim_available(),
        }

    def _check_official_sim_available(self) -> bool:
        try:
            import httpx
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{self.official_adapter.base_url}/healthz")
                return response.status_code == 200
        except:
            return False
