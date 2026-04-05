import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.services.after_sale_domain_service import AfterSaleDomainService
from app.services.conversation_domain_service import ConversationDomainService
from app.services.order_domain_service import OrderDomainService
from app.services.platform_gateway_service import PlatformGatewayService
from app.services.push_event_tracker import PushEventTracker
from app.services.shipment_domain_service import ShipmentDomainService

from providers.odoo.provider import OdooProvider


class BusinessContextService:
    def __init__(
        self,
        gateway: PlatformGatewayService,
        order_service: OrderDomainService,
        shipment_service: ShipmentDomainService,
        after_sale_service: AfterSaleDomainService,
        conversation_service: ConversationDomainService,
        odoo_provider: OdooProvider,
        push_event_tracker: Optional[PushEventTracker] = None,
    ):
        self.gateway = gateway
        self.order_service = order_service
        self.shipment_service = shipment_service
        self.after_sale_service = after_sale_service
        self.conversation_service = conversation_service
        self.odoo_provider = odoo_provider
        self.push_event_tracker = push_event_tracker

    def get_context(
        self,
        platform: str,
        biz_id: str,
        official_run_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        context_id = str(uuid.uuid4())
        now = datetime.now()

        context: Dict[str, Any] = {
            "context_id": context_id,
            "platform": platform,
            "biz_id": biz_id,
            "biz_type": "order",
            "official_run_id": official_run_id,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "data_sources": {},
            "source_errors": [],
        }

        biz_reference = self._resolve_biz_reference(platform, biz_id, official_run_id)
        effective_platform = biz_reference["effective_platform"]
        effective_biz_id = biz_reference["effective_biz_id"]
        linked_source = self._resolve_business_data_source(
            requested_platform=platform,
            effective_platform=effective_platform,
            official_run_id=official_run_id,
        )

        if (
            effective_platform != platform
            or effective_biz_id != biz_id
            or biz_reference.get("external_biz_id") not in (None, biz_id)
        ):
            context["resolved_biz_reference"] = biz_reference
            self._mark_data_source(context, "resolved_biz_reference", "conversation_bridge")

        # Pull push events from tracker (P2-3: consume pushes in business context)
        push_events = self._get_push_events(official_run_id) if official_run_id else []
        if push_events:
            context["push_events"] = push_events
            self._mark_data_source(context, "push_events", "push_event_tracker")

        try:
            order = self.order_service.get_order(
                effective_platform,
                effective_biz_id,
                official_run_id=official_run_id if effective_platform == platform else None,
            )
            context["order_snapshot"] = {
                "order_id": order.get("order_id"),
                "requested_order_id": order.get("requested_order_id"),
                "external_order_id": order.get("external_order_id"),
                "canonical_order_id": order.get("canonical_order_id"),
                "status": order.get("status"),
                "total_amount": order.get("total_amount"),
                "product_ids": self._extract_product_ids(order),
                "created_at": order.get("created_at"),
            }
            self._mark_data_source(context, "order_snapshot", linked_source)
        except Exception as exc:
            self._record_source_error(context, "order_snapshot", exc)

        try:
            shipment = self.shipment_service.get_shipment(
                effective_platform,
                effective_biz_id,
                official_run_id=official_run_id if effective_platform == platform else None,
            )
            context["shipment_snapshot"] = {
                "shipment_id": shipment.get("shipment_id"),
                "canonical_shipment_id": shipment.get("canonical_shipment_id"),
                "order_id": shipment.get("order_id"),
                "requested_order_id": shipment.get("requested_order_id"),
                "external_order_id": shipment.get("external_order_id"),
                "canonical_order_id": shipment.get("canonical_order_id"),
                "status": shipment.get("status"),
                "company": shipment.get("company"),
                "tracking_no": shipment.get("tracking_no"),
            }
            self._mark_data_source(context, "shipment_snapshot", linked_source)
        except Exception as exc:
            self._record_source_error(context, "shipment_snapshot", exc)

        try:
            after_sale = self.after_sale_service.get_after_sale_by_order(
                effective_platform,
                effective_biz_id,
                official_run_id=official_run_id if effective_platform == platform else None,
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
                self._mark_data_source(context, "after_sale_snapshot", linked_source)
        except Exception as exc:
            self._record_source_error(context, "after_sale_snapshot", exc)

        # Augment context with latest push state if available
        if push_events:
            self._apply_push_state(context, push_events)

        context["risk_flags"] = self._calculate_risk_flags(context)
        context["quality_flags"] = self._calculate_quality_flags(context)

        return context

    def _get_push_events(self, official_run_id: str) -> List[Dict[str, Any]]:
        """Query push events from tracker for a given run."""
        if not self.push_event_tracker:
            return []
        pushes = self.push_event_tracker.get_by_run(official_run_id)
        return [
            {
                "event_type": p.event_type,
                "step_no": p.step_no,
                "platform": p.platform,
                "body": p.body,
                "received_at": p.received_at,
            }
            for p in pushes
        ]

    def _apply_push_state(
        self, context: Dict[str, Any], push_events: List[Dict[str, Any]]
    ) -> None:
        """Apply latest push state to order/shipment snapshots."""
        latest_order_push = None
        latest_shipment_push = None
        latest_refund_push = None

        for push in push_events:
            et = push["event_type"].lower()
            if "order" in et or "trade" in et:
                if not latest_order_push or push["step_no"] > latest_order_push["step_no"]:
                    latest_order_push = push
            if "ship" in et or "shipment" in et or "logistics" in et:
                if not latest_shipment_push or push["step_no"] > latest_shipment_push["step_no"]:
                    latest_shipment_push = push
            if "refund" in et:
                if not latest_refund_push or push["step_no"] > latest_refund_push["step_no"]:
                    latest_refund_push = push

        if latest_order_push and context.get("order_snapshot"):
            body = latest_order_push["body"]
            ctx_order = context["order_snapshot"]
            if "new_status" in body:
                ctx_order["status"] = body["new_status"]
            ctx_order["push_updated_at"] = latest_order_push["received_at"]

        if latest_shipment_push and context.get("shipment_snapshot"):
            body = latest_shipment_push["body"]
            ctx_ship = context["shipment_snapshot"]
            if "logistics_company" in body:
                ctx_ship["company"] = body["logistics_company"]
            if "tracking_no" in body:
                ctx_ship["tracking_no"] = body["tracking_no"]
            ctx_ship["push_updated_at"] = latest_shipment_push["received_at"]

        # Push-based after_sale detection
        if latest_refund_push:
            context["push_refund_detected"] = {
                "event_type": latest_refund_push["event_type"],
                "received_at": latest_refund_push["received_at"],
            }

    def _mark_data_source(self, context: Dict[str, Any], key: str, source: str) -> None:
        context.setdefault("data_sources", {})[key] = source

    def _record_source_error(self, context: Dict[str, Any], key: str, exc: Exception) -> None:
        errors = context.setdefault("source_errors", [])
        errors.append(
            {
                "source": key,
                "error_type": exc.__class__.__name__,
                "message": str(exc),
            }
        )

    def _resolve_biz_reference(
        self,
        platform: str,
        biz_id: str,
        official_run_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self.conversation_service.resolve_business_reference(
            platform,
            biz_id,
            official_run_id=official_run_id,
        )

    def _resolve_business_data_source(
        self,
        requested_platform: str,
        effective_platform: str,
        official_run_id: Optional[str] = None,
    ) -> str:
        if effective_platform != requested_platform:
            return "linked_platform_provider"
        if official_run_id:
            return "official_sim_run"
        return "platform_provider"
    
    def build_context(
        self,
        platform: str,
        biz_id: str,
        biz_type: str = "order",
        options: Optional[Dict[str, bool]] = None,
        official_run_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        options = options or {}
        
        if biz_type == "order":
            context = self._build_order_context(platform, biz_id, options, official_run_id)
        elif biz_type == "conversation":
            context = self._build_conversation_context(platform, biz_id, options, official_run_id)
        elif biz_type == "after_sale":
            context = self._build_after_sale_context(platform, biz_id, options, official_run_id)
        else:
            context = self.get_context(platform, biz_id, official_run_id)
        
        context["biz_type"] = biz_type
        
        if options.get("include_recommendations", True):
            context["action_candidates"] = self._generate_action_candidates(context)
            context["reply_candidates"] = self._generate_reply_candidates(context)
        
        return context
    
    def _build_order_context(
        self,
        platform: str,
        order_id: str,
        options: Dict[str, bool],
        official_run_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        context = self.get_context(platform, order_id, official_run_id)
        biz_reference = context.get("resolved_biz_reference") or self._resolve_biz_reference(
            platform,
            order_id,
            official_run_id=official_run_id,
        )
        effective_platform = biz_reference["effective_platform"]
        effective_order_id = biz_reference["effective_biz_id"]
        
        if options.get("include_inventory", False):
            context["inventory_snapshot"] = self._resolve_inventory_snapshot(context, effective_order_id)
            if context.get("inventory_snapshot"):
                self._mark_data_source(context, "inventory_snapshot", "odoo")

        try:
            order_audit = self.odoo_provider.get_order_audit(
                effective_order_id,
                platform=effective_platform,
            )
            if order_audit:
                context["order_audit_snapshot"] = {
                    "order_id": order_audit.order_id,
                    "audit_status": order_audit.audit_status,
                    "audit_notes": order_audit.audit_notes,
                    "audited_by": order_audit.audited_by,
                    "audited_at": order_audit.audited_at.isoformat() if order_audit.audited_at else None,
                }
                self._mark_data_source(context, "order_audit_snapshot", "odoo")
        except Exception as exc:
            context["order_audit_snapshot"] = None
            self._record_source_error(context, "order_audit_snapshot", exc)

        try:
            exceptions = self.odoo_provider.get_order_exceptions(effective_order_id)
            context["order_exception_snapshots"] = [
                {
                    "exception_id": exc.exception_id,
                    "order_id": exc.order_id,
                    "exception_type": exc.exception_type,
                    "severity": exc.severity,
                    "description": exc.description,
                    "status": exc.status,
                    "created_at": exc.created_at.isoformat() if exc.created_at else None,
                    "resolved_at": exc.resolved_at.isoformat() if exc.resolved_at else None,
                }
                for exc in exceptions
            ]
            if context["order_exception_snapshots"]:
                self._mark_data_source(context, "order_exception_snapshots", "odoo")
        except Exception as exc:
            context["order_exception_snapshots"] = []
            self._record_source_error(context, "order_exception_snapshots", exc)

        try:
            fulfillment = self.odoo_provider.get_fulfillment(
                effective_order_id,
                platform=effective_platform,
            )
            if fulfillment:
                context["fulfillment_snapshot"] = {
                    "order_id": fulfillment.order_id,
                    "status": fulfillment.status,
                    "warehouse": fulfillment.warehouse,
                    "picking_id": fulfillment.picking_id,
                    "scheduled_date": fulfillment.scheduled_date.isoformat() if fulfillment.scheduled_date else None,
                    "actual_date": fulfillment.actual_date.isoformat() if fulfillment.actual_date else None,
                }
                self._mark_data_source(context, "fulfillment_snapshot", "odoo")
        except Exception as exc:
            context["fulfillment_snapshot"] = None
            self._record_source_error(context, "fulfillment_snapshot", exc)
        
        return context
    
    def _build_conversation_context(
        self,
        platform: str,
        conversation_id: str,
        options: Dict[str, bool],
        official_run_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        context_id = str(uuid.uuid4())
        now = datetime.now()
        
        context = {
            "context_id": context_id,
            "platform": platform,
            "biz_id": conversation_id,
            "biz_type": "conversation",
            "official_run_id": official_run_id,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "data_sources": {},
            "source_errors": [],
        }
        
        try:
            conversation = self.conversation_service.get_conversation(
                platform,
                conversation_id,
                official_run_id=official_run_id,
            )
            context["conversation_snapshot"] = conversation
            self._mark_data_source(
                context,
                "conversation_snapshot",
                "official_sim_run" if official_run_id else "platform_provider",
            )
        except Exception as exc:
            context["conversation_snapshot"] = None
            self._record_source_error(context, "conversation_snapshot", exc)
        
        if options.get("include_inventory", False):
            context["inventory_snapshot"] = None
        
        context["order_audit_snapshot"] = None
        context["order_exception_snapshots"] = []
        context["fulfillment_snapshot"] = None
        
        context["risk_flags"] = self._calculate_risk_flags(context)
        context["quality_flags"] = self._calculate_quality_flags(context)
        
        return context
    
    def _build_after_sale_context(
        self,
        platform: str,
        after_sale_id: str,
        options: Dict[str, bool],
        official_run_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        context_id = str(uuid.uuid4())
        now = datetime.now()
        
        context = {
            "context_id": context_id,
            "platform": platform,
            "biz_id": after_sale_id,
            "biz_type": "after_sale",
            "official_run_id": official_run_id,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "data_sources": {},
            "source_errors": [],
        }
        
        try:
            after_sale = self.after_sale_service.get_after_sale(
                platform,
                after_sale_id,
                official_run_id=official_run_id,
            )
            context["after_sale_snapshot"] = {
                "after_sale_id": after_sale.get("after_sale_id"),
                "canonical_after_sale_id": after_sale.get("canonical_after_sale_id"),
                "external_after_sale_id": after_sale.get("external_after_sale_id"),
                "status": after_sale.get("status"),
                "status_text": after_sale.get("status_text"),
                "reason": after_sale.get("reason"),
            }
            self._mark_data_source(
                context,
                "after_sale_snapshot",
                "official_sim_run" if official_run_id else "platform_provider",
            )
            
            order_id = after_sale.get("order_id")
            if order_id:
                try:
                    exceptions = self.odoo_provider.get_order_exceptions(order_id)
                    context["order_exception_snapshots"] = [
                        {
                            "exception_id": exc.exception_id,
                            "order_id": exc.order_id,
                            "exception_type": exc.exception_type,
                            "severity": exc.severity,
                            "description": exc.description,
                            "status": exc.status,
                            "created_at": exc.created_at.isoformat() if exc.created_at else None,
                            "resolved_at": exc.resolved_at.isoformat() if exc.resolved_at else None,
                        }
                        for exc in exceptions
                    ]
                    if context["order_exception_snapshots"]:
                        self._mark_data_source(context, "order_exception_snapshots", "odoo")
                except Exception as exc:
                    context["order_exception_snapshots"] = []
                    self._record_source_error(context, "order_exception_snapshots", exc)
        except Exception as exc:
            context["after_sale_snapshot"] = None
            context["order_exception_snapshots"] = []
            self._record_source_error(context, "after_sale_snapshot", exc)
        
        if options.get("include_inventory", False):
            context["inventory_snapshot"] = None
        
        context["order_audit_snapshot"] = None
        context["fulfillment_snapshot"] = None
        
        context["risk_flags"] = self._calculate_risk_flags(context)
        context["quality_flags"] = self._calculate_quality_flags(context)
        
        return context
    
    def refresh_context(self, context_id: str, platform: str, biz_id: str) -> Dict[str, Any]:
        return self.get_context(platform, biz_id)
    
    def _calculate_risk_flags(self, context: Dict[str, Any]) -> Dict[str, Any]:
        risk_level = "low"
        tags = []
        score = 0
        
        order_snapshot = context.get("order_snapshot", {})
        after_sale_snapshot = context.get("after_sale_snapshot")
        exceptions = context.get("order_exception_snapshots", [])
        
        if after_sale_snapshot:
            risk_level = "medium"
            tags.append("has_after_sale")
            score += 20
        
        if exceptions:
            risk_level = "high" if risk_level == "low" else "critical"
            tags.append("has_exceptions")
            score += len(exceptions) * 15
        
        order_status = order_snapshot.get("status")
        if order_status in ["refunding", "refunded"]:
            risk_level = "high"
            tags.append("refund_involved")
            score += 30
        
        return {
            "level": risk_level,
            "tags": tags,
            "score": score,
            "reasons": [],
        }
    
    def _calculate_quality_flags(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "score": 100,
            "issues": [],
            "suggestions": [],
        }

    def _extract_product_ids(self, order: Dict[str, Any]) -> List[str]:
        product_ids: List[str] = []
        for item in order.get("products", []):
            if not isinstance(item, dict):
                continue
            product_id = item.get("product_id") or item.get("sku_id")
            if product_id:
                product_ids.append(str(product_id))
        return product_ids

    def _serialize_inventory(self, inventory: Any) -> Dict[str, Any]:
        return {
            "product_id": inventory.product_id,
            "sku_id": inventory.sku_id,
            "quantity": inventory.quantity,
            "reserved_quantity": inventory.reserved_quantity,
            "available_quantity": inventory.available_quantity,
            "warehouse": inventory.warehouse,
            "location": inventory.location,
            "updated_at": inventory.updated_at.isoformat() if inventory.updated_at else None,
        }

    def _resolve_inventory_snapshot(self, context: Dict[str, Any], order_id: str) -> Optional[Dict[str, Any]]:
        order_snapshot = context.get("order_snapshot") or {}
        product_ids: List[str] = []

        if isinstance(order_snapshot, dict):
            raw_ids = order_snapshot.get("product_ids", [])
            if isinstance(raw_ids, list):
                product_ids.extend(str(pid) for pid in raw_ids if pid)

        # Backward-compatible fallback for existing Odoo mock data keyed by order_id.
        product_ids.append(order_id)

        checked = set()
        for product_id in product_ids:
            if product_id in checked:
                continue
            checked.add(product_id)
            try:
                inventory = self.odoo_provider.get_inventory(product_id)
                if inventory:
                    return self._serialize_inventory(inventory)
            except Exception:
                continue

        return None
    
    def _generate_action_candidates(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        candidates = []
        
        order_snapshot = context.get("order_snapshot", {})
        after_sale_snapshot = context.get("after_sale_snapshot")
        exceptions = context.get("order_exception_snapshots", [])
        
        if order_snapshot.get("status") == "wait_ship":
            candidates.append({
                "action_type": "ship_order",
                "priority": 10,
                "description": "订单待发货，建议尽快安排发货",
                "params": {"order_id": order_snapshot.get("order_id")},
                "auto_executable": False,
            })
        
        if after_sale_snapshot:
            candidates.append({
                "action_type": "handle_after_sale",
                "priority": 20,
                "description": "存在售后申请，需要处理",
                "params": {"after_sale_id": after_sale_snapshot.get("after_sale_id")},
                "auto_executable": False,
            })
        
        for exc in exceptions:
            if exc.get("status") == "open":
                candidates.append({
                    "action_type": "resolve_exception",
                    "priority": 30,
                    "description": f"订单异常需要处理: {exc.get('description')}",
                    "params": {"exception_id": exc.get("exception_id")},
                    "auto_executable": False,
                })
        
        return candidates
    
    def _generate_reply_candidates(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        candidates = []
        
        order_snapshot = context.get("order_snapshot", {})
        
        if order_snapshot.get("status") == "wait_ship":
            candidates.append({
                "reply_type": "shipping_notice",
                "content": "您好，您的订单正在安排发货中，请耐心等待。",
                "confidence": 0.9,
                "source": "rule",
                "tags": ["shipping", "wait_ship"],
            })
        
        if order_snapshot.get("status") == "shipped":
            candidates.append({
                "reply_type": "shipment_query",
                "content": "您好，您的订单已发货，物流信息已更新。",
                "confidence": 0.85,
                "source": "rule",
                "tags": ["shipping", "shipped"],
            })
        
        return candidates
