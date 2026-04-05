"""Thread-safe in-memory push event tracker.

Receives push events from official-sim via HTTP callbacks.
P1: no persistence needed; data lives in process memory.
"""

import threading
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass
class ReceivedPush:
    event_type: str
    run_id: str
    step_no: int
    platform: str
    body: Dict[str, Any]
    headers: Dict[str, Any]
    received_at: str


class PushEventTracker:
    def __init__(self):
        self._lock = threading.Lock()
        self._events: List[ReceivedPush] = []

    def record(
        self,
        event_type: str,
        run_id: str,
        step_no: int,
        platform: str,
        body: Dict[str, Any],
        headers: Dict[str, Any],
        received_at: str,
    ) -> ReceivedPush:
        entry = ReceivedPush(
            event_type=event_type,
            run_id=run_id,
            step_no=step_no,
            platform=platform,
            body=body,
            headers=headers,
            received_at=received_at,
        )
        with self._lock:
            self._events.append(entry)
        return entry

    def get_by_run(self, run_id: str) -> List[ReceivedPush]:
        with self._lock:
            return [e for e in self._events if e.run_id == run_id]

    def list_all(self) -> List[ReceivedPush]:
        with self._lock:
            return list(self._events)

    def count(self) -> int:
        with self._lock:
            return len(self._events)

    def clear(self) -> None:
        with self._lock:
            self._events.clear()
