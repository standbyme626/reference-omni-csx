from __future__ import annotations

import os
from typing import Any, Dict, Optional

import httpx


class OfficialSimClientError(RuntimeError):
    pass


class OfficialSimClient:
    def __init__(self, base_url: Optional[str] = None, timeout_s: float = 10.0):
        self.base_url = (
            (base_url or os.getenv("OFFICIAL_SIM_BASE_URL") or "http://localhost:8001").rstrip("/")
        )
        self.timeout_s = timeout_s

    def create_run(
        self,
        platform: str,
        scenario_name: str,
        metadata: Optional[Dict[str, Any]] = None,
        strict_mode: bool = True,
        push_enabled: bool = True,
    ) -> Dict[str, Any]:
        payload = {
            "platform": platform,
            "scenario_name": scenario_name,
            "strict_mode": strict_mode,
            "push_enabled": push_enabled,
            "metadata": metadata or {},
        }
        return self._request("POST", "/official-sim/runs", json_body=payload)

    def write_artifact(
        self,
        run_id: str,
        artifact_kind: str,
        payload: Dict[str, Any],
        turn_no: Optional[int] = None,
        step_no: Optional[int] = None,
    ) -> Dict[str, Any]:
        body: Dict[str, Any] = {
            "artifact_kind": artifact_kind,
            "payload": payload,
        }
        if turn_no is not None:
            body["turn_no"] = turn_no
        if step_no is not None:
            body["step_no"] = step_no
        return self._request("POST", f"/official-sim/runs/{run_id}/artifacts", json_body=body)

    def advance_run(self, run_id: str, event_type: str = "conversation_turn") -> Dict[str, Any]:
        return self._request(
            "POST",
            f"/official-sim/runs/{run_id}/advance",
            json_body={"event_type": event_type},
        )

    def get_report(self, run_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/official-sim/runs/{run_id}/report")

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
            raise OfficialSimClientError(f"official-sim unavailable: {exc}") from exc

        if response.status_code >= 400:
            raise OfficialSimClientError(
                f"official-sim error {response.status_code}: {response.text[:300]}"
            )

        data = response.json()
        if isinstance(data, dict):
            return data
        return {"data": data}

