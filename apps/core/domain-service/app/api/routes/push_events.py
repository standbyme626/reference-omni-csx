"""Push event receiver for official-sim push notifications."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.response import success_response
from app.dependencies import get_push_event_tracker

router = APIRouter()


class PushEventEnvelope(BaseModel):
    event_type: str = Field(..., description="Platform event type, e.g. trade.OrderStatusChanged")
    run_id: str = Field(..., description="official-sim run UUID")
    step_no: int = Field(..., ge=1)
    platform: str = Field(..., description="Platform name")
    body: Dict[str, Any] = Field(default_factory=dict, description="Push payload body")
    headers: Dict[str, Any] = Field(default_factory=dict, description="Push payload headers")


@router.post("")
async def receive_push_event(envelope: PushEventEnvelope):
    """Receive a push event from official-sim."""
    tracker = get_push_event_tracker()

    tracker.record(
        event_type=envelope.event_type,
        run_id=envelope.run_id,
        step_no=envelope.step_no,
        platform=envelope.platform,
        body=envelope.body,
        headers=envelope.headers,
        received_at=datetime.now(timezone.utc).isoformat(),
    )

    return success_response(
        {
            "status": "ack",
            "event_type": envelope.event_type,
            "run_id": envelope.run_id,
        }
    )


@router.get("")
async def list_received_pushes(run_id: Optional[str] = None):
    """List received push events (debug endpoint)."""
    tracker = get_push_event_tracker()
    if run_id:
        events = tracker.get_by_run(run_id)
    else:
        events = tracker.list_all()
    return success_response({"events": [e.__dict__ for e in events], "total": len(events)})
