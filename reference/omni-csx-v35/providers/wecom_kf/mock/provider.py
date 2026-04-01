"""WeCom KF mock provider - calls official-sim-server for message/session data."""

import httpx


class WecomKfMockProvider:
    def __init__(self, base_url: str = "http://localhost:8200"):
        self.base_url = base_url

    def get_platform(self) -> str:
        return "wecom_kf"

    def sync_message(self, msg_data: dict) -> dict:
        response = httpx.post(f"{self.base_url}/mock/wecom-kf/messages/sync", timeout=10)
        response.raise_for_status()
        return response.json()