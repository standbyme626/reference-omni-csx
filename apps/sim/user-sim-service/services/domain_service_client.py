from __future__ import annotations

import os
from typing import Any, Dict, Optional

import httpx


class DomainServiceClientError(RuntimeError):
    pass


class DomainServiceClient:
    def __init__(self, base_url: Optional[str] = None, timeout_s: float = 10.0):
        self.base_url = (
            (base_url or os.getenv("DOMAIN_SERVICE_BASE_URL") or "http://localhost:8000").rstrip("/")
        )
        self.timeout_s = timeout_s

    def get_reply_recommendation(
        self,
        platform: str,
        biz_id: str,
        biz_type: str = "order",
        intent: Optional[str] = None,
        max_candidates: int = 5,
        official_run_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "platform": platform,
            "biz_id": biz_id,
            "biz_type": biz_type,
            "intent": intent,
            "max_candidates": max_candidates,
        }
        if official_run_id:
            payload["official_run_id"] = official_run_id

        result = self._request("POST", "/api/recommendations/reply", json_body=payload)
        if not isinstance(result, dict):
            return {}

        data = result.get("data")
        if isinstance(data, dict):
            return data
        return {}

    def _request(
        self,
        method: str,
        path: str,
        json_body: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        try:
            with httpx.Client(timeout=self.timeout_s) as client:
                response = client.request(method, url, json=json_body)
        except Exception as exc:
            raise DomainServiceClientError(f"domain-service unavailable: {exc}") from exc

        if response.status_code >= 400:
            raise DomainServiceClientError(
                f"domain-service error {response.status_code}: {response.text[:300]}"
            )

        data = response.json()
        if isinstance(data, dict):
            return data
        return {"data": data}

