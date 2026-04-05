"""Context resolver — aggregates snapshots from other services into a context dict.

Split from BusinessContextService. Does NOT do risk calc or reply generation;
those go to RiskEvaluator and ReplyGenerator respectively.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.services.after_sale_service import AfterSaleService
from app.services.conversation_service import ConversationService
from app.services.order_service import OrderService
from app.services.push_events_service import PushEventsService
from app.services.risk_evaluator import RiskEvaluator
from app.services.shipment_service import ShipmentService
from providers.odoo.provider import OdooProvider


class ContextResolver:
    """Aggregate order, shipment, after-sale, and odoo snapshots into a context dict."""

    def __init__(
        self,
        order_service: OrderService,
        shipment_service: ShipmentService,
        after_sale_service: AfterSaleService,
        conversation_service: ConversationService,
        odoo_provider: OdooProvider,
        push_events_service: PushEventsService,
        risk_evaluator: RiskEvaluator,
    ):
        self.order_service = order_service
        self.shipment_service = shipment_service
        self.after_sale_service = after_sale_service
        self.conversation_service = conversation_service
        self.odoo_provider = odoo_provider
        self.push_events_service = push_events_service
        self.risk_evaluator = risk_evaluator

    def get_context(
        self,
        platform: str,
        biz_id: str,
        official_run_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        context_id = str(uuid.uuid4())
        now = datetime.now()
        context: Dict[str, Any] = {
            "context_id": context_id, "platform": platform, "biz_id": biz_id,
            "biz_type": "order", "official_run_id": official_run_id,
            "created_at": now.isoformat(), "updated_at": now.isoformat(),
            "data_sources": {}, "source_errors": [],
        }

        biz_reference = self.conversation_service.resolve_business_reference(
            platform, biz_id, official_run_id=official_run_id,
        )
        effective_platform = biz_reference["effective_platform"]
        effective_biz_id = biz_reference["effective_biz_id"]
        linked_source = self._resolve_source(platform, effective_platform, official_run_id)

        if effective_platform != platform or effective_biz_id != biz_id:
            context["resolved_biz_reference"] = biz_reference
            self._mark(context, "resolved_biz_reference", "conversation_bridge")

        push_events = self.push_events_service.get_push_events(official_run_id) if official_run_id else []
        if push_events:
            context["push_events"] = push_events
            self._mark(context, "push_events", "push_event_tracker")
            self.push_events_service.apply_state(context, push_events)

        run_override = official_run_id if effective_platform == platform else None

        # Order snapshot
        try:
            order = self.order_service.get_order(effective_platform, effective_biz_id, official_run_id=run_override)
            product_ids = [str(item.get("product_id") or item.get("sku_id"))
                           for item in order.get("products", []) if isinstance(item, dict)
                           and (item.get("product_id") or item.get("sku_id"))]
            context["order_snapshot"] = {
                "order_id": order.get("order_id"), "requested_order_id": order.get("requested_order_id"),
                "external_order_id": order.get("external_order_id"),
                "canonical_order_id": order.get("canonical_order_id"),
                "status": order.get("status"), "total_amount": order.get("total_amount"),
                "product_ids": product_ids, "created_at": order.get("created_at"),
            }
            self._mark(context, "order_snapshot", linked_source)
        except Exception as exc:
            self._record_error(context, "order_snapshot", exc)

        # Shipment snapshot
        try:
            shipment = self.shipment_service.get_shipment(
                effective_platform, effective_biz_id, official_run_id=run_override,
            )
            context["shipment_snapshot"] = {
                "shipment_id": shipment.get("shipment_id"),
                "canonical_shipment_id": shipment.get("canonical_shipment_id"),
                "order_id": shipment.get("order_id"),
                "requested_order_id": shipment.get("requested_order_id"),
                "external_order_id": shipment.get("external_order_id"),
                "canonical_order_id": shipment.get("canonical_order_id"),
                "status": shipment.get("status"), "company": shipment.get("company"),
                "tracking_no": shipment.get("tracking_no"),
            }
            self._mark(context, "shipment_snapshot", linked_source)
        except Exception as exc:
            self._record_error(context, "shipment_snapshot", exc)

        # After-sale snapshot
        try:
            after_sale = self.after_sale_service.get_after_sale_by_order(
                effective_platform, effective_biz_id, official_run_id=run_override,
            )
            if "error" not in after_sale:
                context["after_sale_snapshot"] = {
                    "after_sale_id": after_sale.get("after_sale_id"),
                    "canonical_after_sale_id": after_sale.get("canonical_after_sale_id"),
                    "external_after_sale_id": after_sale.get("external_after_sale_id"),
                    "order_id": after_sale.get("order_id"),
                    "requested_order_id": after_sale.get("requested_order_id"),
                    "external_order_id": after_sale.get("external_order_id"),
                    "canonical_order_id": after_sale.get("canonical_order_id"),
                    "status": after_sale.get("status"),
                    "status_text": after_sale.get("status_text"),
                    "reason": after_sale.get("reason"),
                }
                self._mark(context, "after_sale_snapshot", linked_source)
        except Exception as exc:
            self._record_error(context, "after_sale_snapshot", exc)

        # Risk flags
        context["risk_flags"] = self.risk_evaluator.evaluate(context)
        context["quality_flags"] = {"score": 100, "issues": [], "suggestions": []}
        return context

    def _resolve_source(self, requested: str, effective: str, official_run_id: Optional[str]) -> str:
        if effective != requested:
            return "linked_platform_provider"
        if official_run_id:
            return "official_sim_run"
        return "platform_provider"

    def _mark(self, context: Dict[str, Any], key: str, source: str) -> None:
        context.setdefault("data_sources", {})[key] = source

    def _record_error(self, context: Dict[str, Any], key: str, exc: Exception) -> None:
        context.setdefault("source_errors", []).append({
            "source": key, "error_type": exc.__class__.__name__, "message": str(exc),
        })

    # -- inventory helpers (used by build_context for order type) ----------

    def resolve_inventory_snapshot(self, context: Dict[str, Any], order_id: str) -> Optional[Dict[str, Any]]:
        order_snapshot = context.get("order_snapshot") or {}
        product_ids = [str(p) for p in (order_snapshot.get("product_ids") or []) if p]
        product_ids.append(order_id)  # backward-compatible fallback
        checked: set[str] = set()
        for product_id in product_ids:
            if product_id in checked:
                continue
            checked.add(product_id)
            try:
                inventory = self.odoo_provider.get_inventory(product_id)
                if inventory:
                    return {
                        "product_id": inventory.product_id, "sku_id": inventory.sku_id,
                        "quantity": inventory.quantity, "reserved_quantity": inventory.reserved_quantity,
                        "available_quantity": inventory.available_quantity,
                        "warehouse": inventory.warehouse, "location": inventory.location,
                        "updated_at": inventory.updated_at.isoformat() if inventory.updated_at else None,
                    }
            except Exception:
                continue
        return None
