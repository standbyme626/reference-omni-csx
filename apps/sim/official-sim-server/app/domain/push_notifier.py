"""Synchronous HTTP push dispatcher.

Sends push events from official-sim to registered subscriber endpoints
(e.g. domain-service). Uses inline retry, no background workers.
"""

import logging
import time
from dataclasses import dataclass
from typing import Optional, List

import httpx

from app.models.models import PushEvent

logger = logging.getLogger(__name__)


@dataclass
class DispatchResult:
    ok: bool
    status_code: int = 0
    error: Optional[str] = None


class PushNotifier:
    def __init__(
        self,
        subscriber_urls: Optional[List[str]] = None,
        timeout_s: float = 3.0,
        max_retries: int = 2,
    ):
        self.subscriber_urls = subscriber_urls or []
        self.timeout_s = timeout_s
        self.max_retries = max_retries

    def dispatch(self, push_event: PushEvent) -> DispatchResult:
        if not self.subscriber_urls:
            return DispatchResult(ok=True)

        body = {
            "event_type": push_event.event_type,
            "run_id": str(push_event.run_id),
            "step_no": push_event.step_no,
            "platform": push_event.platform,
            "body": push_event.body_json,
            "headers": push_event.headers_json,
        }

        last_error = None
        last_status = 0

        for attempt in range(self.max_retries + 1):
            for url in self.subscriber_urls:
                try:
                    with httpx.Client(timeout=self.timeout_s) as client:
                        resp = client.post(url, json=body)
                    last_status = resp.status_code

                    if resp.status_code == 200:
                        logger.info(
                            "Push dispatched: event=%s run_id=%s url=%s (attempt %d)",
                            push_event.event_type,
                            push_event.run_id,
                            url,
                            attempt + 1,
                        )
                        return DispatchResult(ok=True, status_code=resp.status_code)

                    last_error = f"HTTP {resp.status_code}: {resp.text[:200]}"

                except httpx.TimeoutException:
                    last_error = f"timeout after {self.timeout_s}s"
                except httpx.RequestError as exc:
                    last_error = str(exc)

                logger.warning(
                    "Push attempt %d/%d failed for %s: %s",
                    attempt + 1,
                    self.max_retries + 1,
                    push_event.event_type,
                    last_error,
                )

            if attempt < self.max_retries:
                time.sleep(0.5)

        return DispatchResult(
            ok=False,
            status_code=last_status,
            error=last_error or "all retries exhausted",
        )
