from typing import List, Dict, Any, Optional
from datetime import datetime

from providers.odoo.provider import OdooProvider, OdooProviderMode
from providers.odoo.mock.provider import InventorySnapshot, OrderAuditSnapshot, OrderExceptionSnapshot, FulfillmentSnapshot


class IntegrationService:
    def __init__(self, odoo_provider: OdooProvider):
        self.odoo_provider = odoo_provider

    def get_inventory(self, product_id: Optional[str] = None, warehouse: Optional[str] = None) -> List[Dict[str, Any]]:
        if product_id:
            inventory = self.odoo_provider.get_inventory(product_id)
            if inventory:
                return [self._serialize_inventory(inventory)]
            return []
        else:
            inventories = self.odoo_provider.list_inventory(warehouse)
            return [self._serialize_inventory(inv) for inv in inventories]

    def get_order_audits(self, order_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if order_id:
            audit = self.odoo_provider.get_order_audit(order_id)
            if audit:
                return [self._serialize_audit(audit)]
            return []
        audits = self.odoo_provider.list_order_audits()
        return [self._serialize_audit(a) for a in audits]

    def get_order_exceptions(
        self,
        order_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        if order_id:
            exceptions = self.odoo_provider.get_order_exceptions(order_id)
        else:
            exceptions = self.odoo_provider.list_order_exceptions()

        if status:
            exceptions = [e for e in exceptions if e.status == status]

        return [self._serialize_exception(e) for e in exceptions]

    def get_fulfillment(self, order_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if order_id:
            fulfillment = self.odoo_provider.get_fulfillment(order_id)
            if fulfillment:
                return [self._serialize_fulfillment(fulfillment)]
            return []
        fulfillments = self.odoo_provider.list_fulfillments()
        return [self._serialize_fulfillment(f) for f in fulfillments]

    def _serialize_inventory(self, inv: InventorySnapshot) -> Dict[str, Any]:
        return {
            "product_id": inv.product_id,
            "sku_id": inv.sku_id,
            "quantity": inv.quantity,
            "reserved_quantity": inv.reserved_quantity,
            "available_quantity": inv.available_quantity,
            "warehouse": inv.warehouse,
            "location": inv.location,
            "updated_at": inv.updated_at.isoformat() if inv.updated_at else None,
        }

    def _serialize_audit(self, audit: OrderAuditSnapshot) -> Dict[str, Any]:
        return {
            "order_id": audit.order_id,
            "audit_status": audit.audit_status,
            "audit_notes": audit.audit_notes,
            "audited_by": audit.audited_by,
            "audited_at": audit.audited_at.isoformat() if audit.audited_at else None,
        }

    def _serialize_exception(self, exc: OrderExceptionSnapshot) -> Dict[str, Any]:
        return {
            "exception_id": exc.exception_id,
            "order_id": exc.order_id,
            "exception_type": exc.exception_type,
            "severity": exc.severity,
            "description": exc.description,
            "status": exc.status,
            "created_at": exc.created_at.isoformat() if exc.created_at else None,
            "resolved_at": exc.resolved_at.isoformat() if exc.resolved_at else None,
        }

    def _serialize_fulfillment(self, ff: FulfillmentSnapshot) -> Dict[str, Any]:
        return {
            "order_id": ff.order_id,
            "status": ff.status,
            "warehouse": ff.warehouse,
            "picking_id": ff.picking_id,
            "scheduled_date": ff.scheduled_date.isoformat() if ff.scheduled_date else None,
            "actual_date": ff.actual_date.isoformat() if ff.actual_date else None,
        }
