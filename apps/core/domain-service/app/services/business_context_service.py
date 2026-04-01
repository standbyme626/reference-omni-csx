from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid

from app.services.platform_gateway_service import PlatformGatewayService
from app.services.order_domain_service import OrderDomainService
from app.services.shipment_domain_service import ShipmentDomainService
from app.services.after_sale_domain_service import AfterSaleDomainService
from app.services.conversation_domain_service import ConversationDomainService
from providers.odoo.provider import OdooProvider
from models.unified import Platform


class BusinessContextService:
    def __init__(
        self,
        gateway: PlatformGatewayService,
        order_service: OrderDomainService,
        shipment_service: ShipmentDomainService,
        after_sale_service: AfterSaleDomainService,
        conversation_service: ConversationDomainService,
        odoo_provider: OdooProvider,
    ):
        self.gateway = gateway
        self.order_service = order_service
        self.shipment_service = shipment_service
        self.after_sale_service = after_sale_service
        self.conversation_service = conversation_service
        self.odoo_provider = odoo_provider
    
    def get_context(self, platform: str, biz_id: str) -> Dict[str, Any]:
        context_id = str(uuid.uuid4())
        now = datetime.now()
        
        context = {
            "context_id": context_id,
            "platform": platform,
            "biz_id": biz_id,
            "biz_type": "order",
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }
        
        try:
            order = self.order_service.get_order(platform, biz_id)
            context["order_snapshot"] = {
                "order_id": order.get("order_id"),
                "status": order.get("status"),
                "total_amount": order.get("total_amount"),
                "created_at": order.get("created_at"),
            }
        except Exception:
            pass
        
        try:
            shipment = self.shipment_service.get_shipment(platform, biz_id)
            context["shipment_snapshot"] = {
                "shipment_id": shipment.get("shipment_id"),
                "status": shipment.get("status"),
                "company": shipment.get("company"),
                "tracking_no": shipment.get("tracking_no"),
            }
        except Exception:
            pass
        
        try:
            after_sale = self.after_sale_service.get_after_sale_by_order(platform, biz_id)
            if "error" not in after_sale:
                context["after_sale_snapshot"] = {
                    "after_sale_id": after_sale.get("after_sale_id"),
                    "status": after_sale.get("status"),
                    "reason": after_sale.get("reason"),
                }
        except Exception:
            pass
        
        context["risk_flags"] = self._calculate_risk_flags(context)
        context["quality_flags"] = self._calculate_quality_flags(context)
        
        return context
    
    def build_context(
        self,
        platform: str,
        biz_id: str,
        biz_type: str = "order",
        options: Optional[Dict[str, bool]] = None,
    ) -> Dict[str, Any]:
        options = options or {}
        
        if biz_type == "order":
            context = self._build_order_context(platform, biz_id, options)
        elif biz_type == "conversation":
            context = self._build_conversation_context(platform, biz_id, options)
        elif biz_type == "after_sale":
            context = self._build_after_sale_context(platform, biz_id, options)
        else:
            context = self.get_context(platform, biz_id)
        
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
    ) -> Dict[str, Any]:
        context = self.get_context(platform, order_id)
        
        if options.get("include_inventory", False):
            try:
                inventory = self.odoo_provider.get_inventory(order_id)
                if inventory:
                    context["inventory_snapshot"] = {
                        "product_id": inventory.product_id,
                        "sku_id": inventory.sku_id,
                        "quantity": inventory.quantity,
                        "reserved_quantity": inventory.reserved_quantity,
                        "available_quantity": inventory.available_quantity,
                        "warehouse": inventory.warehouse,
                        "location": inventory.location,
                        "updated_at": inventory.updated_at.isoformat() if inventory.updated_at else None,
                    }
            except Exception:
                context["inventory_snapshot"] = None
        
        try:
            order_audit = self.odoo_provider.get_order_audit(order_id)
            if order_audit:
                context["order_audit_snapshot"] = {
                    "order_id": order_audit.order_id,
                    "audit_status": order_audit.audit_status,
                    "audit_notes": order_audit.audit_notes,
                    "audited_by": order_audit.audited_by,
                    "audited_at": order_audit.audited_at.isoformat() if order_audit.audited_at else None,
                }
        except Exception:
            context["order_audit_snapshot"] = None
        
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
        except Exception:
            context["order_exception_snapshots"] = []
        
        try:
            fulfillment = self.odoo_provider.get_fulfillment(order_id)
            if fulfillment:
                context["fulfillment_snapshot"] = {
                    "order_id": fulfillment.order_id,
                    "status": fulfillment.status,
                    "warehouse": fulfillment.warehouse,
                    "picking_id": fulfillment.picking_id,
                    "scheduled_date": fulfillment.scheduled_date.isoformat() if fulfillment.scheduled_date else None,
                    "actual_date": fulfillment.actual_date.isoformat() if fulfillment.actual_date else None,
                }
        except Exception:
            context["fulfillment_snapshot"] = None
        
        return context
    
    def _build_conversation_context(
        self,
        platform: str,
        conversation_id: str,
        options: Dict[str, bool],
    ) -> Dict[str, Any]:
        context_id = str(uuid.uuid4())
        now = datetime.now()
        
        context = {
            "context_id": context_id,
            "platform": platform,
            "biz_id": conversation_id,
            "biz_type": "conversation",
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }
        
        try:
            conversation = self.conversation_service.get_conversation(platform, conversation_id)
            context["conversation_snapshot"] = conversation
        except Exception:
            context["conversation_snapshot"] = None
        
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
    ) -> Dict[str, Any]:
        context_id = str(uuid.uuid4())
        now = datetime.now()
        
        context = {
            "context_id": context_id,
            "platform": platform,
            "biz_id": after_sale_id,
            "biz_type": "after_sale",
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }
        
        try:
            after_sale = self.after_sale_service.get_after_sale(platform, after_sale_id)
            context["after_sale_snapshot"] = {
                "after_sale_id": after_sale.get("after_sale_id"),
                "status": after_sale.get("status"),
                "reason": after_sale.get("reason"),
            }
            
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
                except Exception:
                    context["order_exception_snapshots"] = []
        except Exception:
            context["after_sale_snapshot"] = None
            context["order_exception_snapshots"] = []
        
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
