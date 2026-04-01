from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass


@dataclass
class InventorySnapshot:
    product_id: str
    sku_id: Optional[str] = None
    quantity: int = 0
    reserved_quantity: int = 0
    available_quantity: int = 0
    warehouse: Optional[str] = None
    location: Optional[str] = None
    updated_at: Optional[datetime] = None


@dataclass
class OrderAuditSnapshot:
    order_id: str
    audit_status: str
    audit_notes: Optional[str] = None
    audited_by: Optional[str] = None
    audited_at: Optional[datetime] = None


@dataclass
class OrderExceptionSnapshot:
    exception_id: str
    order_id: str
    exception_type: str
    severity: str
    description: str
    status: str
    created_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None


@dataclass
class FulfillmentSnapshot:
    order_id: str
    status: str
    warehouse: Optional[str] = None
    picking_id: Optional[str] = None
    scheduled_date: Optional[datetime] = None
    actual_date: Optional[datetime] = None


class OdooMockProvider:
    def __init__(self):
        self._inventory_data: Dict[str, InventorySnapshot] = {}
        self._order_audits: Dict[str, OrderAuditSnapshot] = {}
        self._order_exceptions: Dict[str, List[OrderExceptionSnapshot]] = {}
        self._fulfillments: Dict[str, FulfillmentSnapshot] = {}
        self._init_mock_data()
    
    def _init_mock_data(self):
        self._inventory_data = {
            "PROD_001": InventorySnapshot(
                product_id="PROD_001",
                sku_id="SKU_001",
                quantity=100,
                reserved_quantity=10,
                available_quantity=90,
                warehouse="WH_MAIN",
                location="LOC_A01",
                updated_at=datetime.now(),
            ),
            "PROD_002": InventorySnapshot(
                product_id="PROD_002",
                sku_id="SKU_002",
                quantity=50,
                reserved_quantity=5,
                available_quantity=45,
                warehouse="WH_MAIN",
                location="LOC_B02",
                updated_at=datetime.now(),
            ),
            "ORDER_001": InventorySnapshot(
                product_id="ORDER_001",
                sku_id="SKU_ORDER_001",
                quantity=200,
                reserved_quantity=20,
                available_quantity=180,
                warehouse="WH_MAIN",
                location="LOC_C01",
                updated_at=datetime.now(),
            ),
            "ORDER_002": InventorySnapshot(
                product_id="ORDER_002",
                sku_id="SKU_ORDER_002",
                quantity=150,
                reserved_quantity=15,
                available_quantity=135,
                warehouse="WH_MAIN",
                location="LOC_D01",
                updated_at=datetime.now(),
            ),
        }
        
        self._order_audits = {
            "ORDER_001": OrderAuditSnapshot(
                order_id="ORDER_001",
                audit_status="approved",
                audit_notes="订单审核通过，可以发货",
                audited_by="auditor_001",
                audited_at=datetime.now(),
            ),
            "ORDER_002": OrderAuditSnapshot(
                order_id="ORDER_002",
                audit_status="pending",
                audit_notes="等待财务审核",
                audited_by=None,
                audited_at=None,
            ),
        }
        
        self._order_exceptions = {
            "ORDER_001": [
                OrderExceptionSnapshot(
                    exception_id="EXC_ORDER_001_1",
                    order_id="ORDER_001",
                    exception_type="inventory_shortage",
                    severity="medium",
                    description="库存不足，需要补货",
                    status="open",
                    created_at=datetime.now(),
                    resolved_at=None,
                ),
            ],
            "ORDER_002": [
                OrderExceptionSnapshot(
                    exception_id="EXC_ORDER_002_1",
                    order_id="ORDER_002",
                    exception_type="address_issue",
                    severity="high",
                    description="收货地址不完整",
                    status="open",
                    created_at=datetime.now(),
                    resolved_at=None,
                ),
                OrderExceptionSnapshot(
                    exception_id="EXC_ORDER_002_2",
                    order_id="ORDER_002",
                    exception_type="payment_delay",
                    severity="low",
                    description="支付超时",
                    status="resolved",
                    created_at=datetime.now(),
                    resolved_at=datetime.now(),
                ),
            ],
        }
        
        self._fulfillments = {
            "ORDER_001": FulfillmentSnapshot(
                order_id="ORDER_001",
                status="picking",
                warehouse="WH_MAIN",
                picking_id="PICK_001",
                scheduled_date=datetime.now(),
                actual_date=None,
            ),
            "ORDER_002": FulfillmentSnapshot(
                order_id="ORDER_002",
                status="pending",
                warehouse="WH_MAIN",
                picking_id=None,
                scheduled_date=datetime.now(),
                actual_date=None,
            ),
        }
    
    def get_inventory(self, product_id: str) -> Optional[InventorySnapshot]:
        return self._inventory_data.get(product_id)
    
    def get_inventory_by_sku(self, sku_id: str) -> Optional[InventorySnapshot]:
        for snapshot in self._inventory_data.values():
            if snapshot.sku_id == sku_id:
                return snapshot
        return None
    
    def list_inventory(self, warehouse: Optional[str] = None) -> List[InventorySnapshot]:
        if warehouse:
            return [s for s in self._inventory_data.values() if s.warehouse == warehouse]
        return list(self._inventory_data.values())
    
    def get_order_audit(self, order_id: str) -> Optional[OrderAuditSnapshot]:
        return self._order_audits.get(order_id)

    def list_order_audits(self) -> List[OrderAuditSnapshot]:
        return list(self._order_audits.values())
    
    def get_order_exceptions(self, order_id: str) -> List[OrderExceptionSnapshot]:
        return self._order_exceptions.get(order_id, [])

    def list_order_exceptions(self) -> List[OrderExceptionSnapshot]:
        result: List[OrderExceptionSnapshot] = []
        for exceptions in self._order_exceptions.values():
            result.extend(exceptions)
        return result
    
    def get_fulfillment(self, order_id: str) -> Optional[FulfillmentSnapshot]:
        return self._fulfillments.get(order_id)

    def list_fulfillments(self) -> List[FulfillmentSnapshot]:
        return list(self._fulfillments.values())
    
    def update_inventory(self, product_id: str, quantity: int) -> InventorySnapshot:
        existing = self._inventory_data.get(product_id)
        if existing:
            existing.quantity = quantity
            existing.available_quantity = quantity - existing.reserved_quantity
            existing.updated_at = datetime.now()
        else:
            existing = InventorySnapshot(
                product_id=product_id,
                quantity=quantity,
                available_quantity=quantity,
                updated_at=datetime.now(),
            )
            self._inventory_data[product_id] = existing
        return existing
    
    def create_order_exception(
        self,
        order_id: str,
        exception_type: str,
        severity: str,
        description: str,
    ) -> OrderExceptionSnapshot:
        exception = OrderExceptionSnapshot(
            exception_id=f"EXC_{order_id}_{len(self._order_exceptions.get(order_id, [])) + 1}",
            order_id=order_id,
            exception_type=exception_type,
            severity=severity,
            description=description,
            status="open",
            created_at=datetime.now(),
        )
        if order_id not in self._order_exceptions:
            self._order_exceptions[order_id] = []
        self._order_exceptions[order_id].append(exception)
        return exception
