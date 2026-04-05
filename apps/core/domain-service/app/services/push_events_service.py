"""Push events service — queries and applies push-state to context snapshots.

Extracted from BusinessContextService._get_push_events and _apply_push_state.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from app.services.push_event_tracker import PushEventTracker

__all__ = ["PushEventsService"]


class PushEventsService:
    """Query push events and apply the latest event state to context snapshots."""

    def __init__(self, tracker: Optional[PushEventTracker] = None):
        self.tracker = tracker

    def get_push_events(self, official_run_id: str) -> List[Dict[str, Any]]:
        if not self.tracker:
            return []
        pushes = self.tracker.get_by_run(official_run_id)
        return [{
            "event_type": p.event_type, "step_no": p.step_no,
            "platform": p.platform, "body": p.body, "received_at": p.received_at,
        } for p in pushes]

    def apply_state(self, context: Dict[str, Any], push_events: List[Dict[str, Any]]) -> None:
        latest_order = None
        latest_shipment = None
        latest_refund = None

        for push in push_events:
            et = push["event_type"].lower()
            if "order" in et or "trade" in et:
                if not latest_order or push["step_no"] > latest_order["step_no"]:
                    latest_order = push
            if "ship" in et or "shipment" in et or "logistics" in et:
                if not latest_shipment or push["step_no"] > latest_shipment["step_no"]:
                    latest_shipment = push
            if "refund" in et:
                if not latest_refund or push["step_no"] > latest_refund["step_no"]:
                    latest_refund = push

        if latest_order and context.get("order_snapshot"):
            body = latest_order["body"]
            ctx_order = context["order_snapshot"]
            if "new_status" in body:
                ctx_order["status"] = body["new_status"]
            ctx_order["push_updated_at"] = latest_order["received_at"]

        if latest_shipment and context.get("shipment_snapshot"):
            body = latest_shipment["body"]
            ctx_ship = context["shipment_snapshot"]
            if "logistics_company" in body:
                ctx_ship["company"] = body["logistics_company"]
            if "tracking_no" in body:
                ctx_ship["tracking_no"] = body["tracking_no"]
            ctx_ship["push_updated_at"] = latest_shipment["received_at"]

        if latest_refund:
            context["push_refund_detected"] = {
                "event_type": latest_refund["event_type"], "received_at": latest_refund["received_at"],
            }
