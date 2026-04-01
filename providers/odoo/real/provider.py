from typing import Dict, Any, Optional, List
from datetime import datetime
import httpx

from providers.odoo.mock.provider import (
    InventorySnapshot,
    OrderAuditSnapshot,
    OrderExceptionSnapshot,
    FulfillmentSnapshot,
)


class OdooClient:
    def __init__(
        self,
        base_url: str,
        db: str,
        username: str,
        api_key: str,
    ):
        self.base_url = base_url.rstrip("/")
        self.db = db
        self.username = username
        self.api_key = api_key
        self.uid: Optional[int] = None
    
    async def authenticate(self) -> bool:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/jsonrpc",
                json={
                    "jsonrpc": "2.0",
                    "method": "call",
                    "params": {
                        "service": "common",
                        "method": "authenticate",
                        "args": [self.db, self.username, self.api_key, {}],
                    },
                },
            )
            result = response.json()
            self.uid = result.get("result")
            return self.uid is not None
    
    async def execute(
        self,
        model: str,
        method: str,
        args: List[Any],
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> Any:
        if not self.uid:
            await self.authenticate()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/jsonrpc",
                json={
                    "jsonrpc": "2.0",
                    "method": "call",
                    "params": {
                        "service": "object",
                        "method": "execute_kw",
                        "args": [
                            self.db,
                            self.uid,
                            self.api_key,
                            model,
                            method,
                            args,
                            kwargs or {},
                        ],
                    },
                },
            )
            result = response.json()
            return result.get("result")


class OdooMapper:
    @staticmethod
    def to_inventory_snapshot(data: Dict[str, Any]) -> InventorySnapshot:
        return InventorySnapshot(
            product_id=str(data.get("product_id", ["", ""])[0]),
            sku_id=str(data.get("product_id", ["", ""])[0]),
            quantity=data.get("quantity", 0),
            reserved_quantity=data.get("reserved_quantity", 0),
            available_quantity=data.get("available_quantity", 0),
            warehouse=data.get("location_id", ["", ""])[1] if data.get("location_id") else None,
            location=data.get("location_id", ["", ""])[1] if data.get("location_id") else None,
            updated_at=datetime.now(),
        )
    
    @staticmethod
    def to_order_audit_snapshot(data: Dict[str, Any]) -> OrderAuditSnapshot:
        return OrderAuditSnapshot(
            order_id=str(data.get("id", "")),
            audit_status=data.get("audit_status", "pending"),
            audit_notes=data.get("audit_notes"),
            audited_by=data.get("audited_by", ["", ""])[1] if data.get("audited_by") else None,
            audited_at=datetime.fromisoformat(data["audited_at"]) if data.get("audited_at") else None,
        )
    
    @staticmethod
    def to_order_exception_snapshot(data: Dict[str, Any]) -> OrderExceptionSnapshot:
        return OrderExceptionSnapshot(
            exception_id=str(data.get("id", "")),
            order_id=str(data.get("order_id", ["", ""])[0]) if data.get("order_id") else "",
            exception_type=data.get("exception_type", "unknown"),
            severity=data.get("severity", "medium"),
            description=data.get("description", ""),
            status=data.get("status", "open"),
            created_at=datetime.fromisoformat(data["create_date"]) if data.get("create_date") else None,
            resolved_at=datetime.fromisoformat(data["resolved_at"]) if data.get("resolved_at") else None,
        )
    
    @staticmethod
    def to_fulfillment_snapshot(data: Dict[str, Any]) -> FulfillmentSnapshot:
        return FulfillmentSnapshot(
            order_id=str(data.get("origin", "")),
            status=data.get("state", "draft"),
            warehouse=data.get("location_id", ["", ""])[1] if data.get("location_id") else None,
            picking_id=str(data.get("id", "")),
            scheduled_date=datetime.fromisoformat(data["scheduled_date"]) if data.get("scheduled_date") else None,
            actual_date=datetime.fromisoformat(data["date_done"]) if data.get("date_done") else None,
        )


class OdooRealProvider:
    def __init__(self, client: OdooClient):
        self.client = client
        self.mapper = OdooMapper()
    
    async def get_inventory(self, product_id: str) -> Optional[InventorySnapshot]:
        results = await self.client.execute(
            "stock.quant",
            "search_read",
            [[("product_id", "=", int(product_id))]],
            {"fields": ["product_id", "quantity", "reserved_quantity", "available_quantity", "location_id"]},
        )
        if results:
            return self.mapper.to_inventory_snapshot(results[0])
        return None
    
    async def list_inventory(self, warehouse: Optional[str] = None) -> List[InventorySnapshot]:
        domain = []
        if warehouse:
            domain.append(("location_id", "ilike", warehouse))
        
        results = await self.client.execute(
            "stock.quant",
            "search_read",
            [domain],
            {"fields": ["product_id", "quantity", "reserved_quantity", "available_quantity", "location_id"]},
        )
        return [self.mapper.to_inventory_snapshot(r) for r in results]
    
    async def get_order_audit(self, order_id: str) -> Optional[OrderAuditSnapshot]:
        results = await self.client.execute(
            "sale.order",
            "search_read",
            [[("id", "=", int(order_id))]],
            {"fields": ["id", "audit_status", "audit_notes", "audited_by", "audited_at"]},
        )
        if results:
            return self.mapper.to_order_audit_snapshot(results[0])
        return None

    async def list_order_audits(self) -> List[OrderAuditSnapshot]:
        results = await self.client.execute(
            "sale.order",
            "search_read",
            [[]],
            {"fields": ["id", "audit_status", "audit_notes", "audited_by", "audited_at"]},
        )
        return [self.mapper.to_order_audit_snapshot(r) for r in results]
    
    async def get_order_exceptions(self, order_id: str) -> List[OrderExceptionSnapshot]:
        results = await self.client.execute(
            "sale.exception",
            "search_read",
            [[("order_id", "=", int(order_id))]],
            {"fields": ["id", "order_id", "exception_type", "severity", "description", "status", "create_date", "resolved_at"]},
        )
        return [self.mapper.to_order_exception_snapshot(r) for r in results]

    async def list_order_exceptions(self) -> List[OrderExceptionSnapshot]:
        results = await self.client.execute(
            "sale.exception",
            "search_read",
            [[]],
            {"fields": ["id", "order_id", "exception_type", "severity", "description", "status", "create_date", "resolved_at"]},
        )
        return [self.mapper.to_order_exception_snapshot(r) for r in results]
    
    async def get_fulfillment(self, order_id: str) -> Optional[FulfillmentSnapshot]:
        results = await self.client.execute(
            "stock.picking",
            "search_read",
            [[("origin", "=", order_id)]],
            {"fields": ["id", "origin", "state", "location_id", "scheduled_date", "date_done"]},
        )
        if results:
            return self.mapper.to_fulfillment_snapshot(results[0])
        return None

    async def list_fulfillments(self) -> List[FulfillmentSnapshot]:
        results = await self.client.execute(
            "stock.picking",
            "search_read",
            [[]],
            {"fields": ["id", "origin", "state", "location_id", "scheduled_date", "date_done"]},
        )
        return [self.mapper.to_fulfillment_snapshot(r) for r in results]
