from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx

from providers.odoo.mock.provider import (
    FulfillmentSnapshot,
    InventorySnapshot,
    OrderAuditSnapshot,
    OrderExceptionSnapshot,
)
from providers.odoo.real.link_resolver import OdooOrderLinkResolver


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
            if result.get("error"):
                raise RuntimeError(result["error"].get("data", {}).get("message") or result["error"].get("message", "Odoo authenticate failed"))
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
            if result.get("error"):
                raise RuntimeError(result["error"].get("data", {}).get("message") or result["error"].get("message", "Odoo execute failed"))
            return result.get("result")


class OdooMapper:
    @staticmethod
    def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        return datetime.fromisoformat(value)

    @staticmethod
    def _map_sale_state_to_audit_status(state: Optional[str]) -> str:
        state_map = {
            "draft": "pending",
            "sent": "pending",
            "sale": "approved",
            "done": "approved",
            "cancel": "rejected",
        }
        return state_map.get(state or "", "pending")

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
    def to_order_audit_snapshot(
        data: Dict[str, Any],
        platform_order_id: Optional[str] = None,
    ) -> OrderAuditSnapshot:
        audited_by = None
        if data.get("audited_by"):
            audited_by = data.get("audited_by", ["", ""])[1]
        elif data.get("user_id"):
            audited_by = data.get("user_id", ["", ""])[1]
        elif data.get("create_uid"):
            audited_by = data.get("create_uid", ["", ""])[1]

        return OrderAuditSnapshot(
            order_id=str(platform_order_id or data.get("id", "") or data.get("name", "")),
            audit_status=data.get("audit_status") or OdooMapper._map_sale_state_to_audit_status(data.get("state")),
            audit_notes=data.get("audit_notes") or data.get("note") or data.get("client_order_ref"),
            audited_by=audited_by,
            audited_at=(
                OdooMapper._parse_datetime(data.get("audited_at"))
                or OdooMapper._parse_datetime(data.get("write_date"))
                or OdooMapper._parse_datetime(data.get("date_order"))
            ),
            platform_order_id=platform_order_id,
            odoo_order_id=str(data.get("id", "")) if data.get("id") is not None else None,
            odoo_order_name=str(data.get("name", "")) if data.get("name") is not None else None,
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
    def to_fulfillment_snapshot(
        data: Dict[str, Any],
        platform_order_id: Optional[str] = None,
    ) -> FulfillmentSnapshot:
        return FulfillmentSnapshot(
            order_id=str(platform_order_id or data.get("origin", "") or data.get("name", "") or data.get("id", "")),
            status=data.get("state", "draft"),
            warehouse=data.get("location_id", ["", ""])[1] if data.get("location_id") else None,
            picking_id=str(data.get("id", "")),
            scheduled_date=OdooMapper._parse_datetime(data.get("scheduled_date")),
            actual_date=OdooMapper._parse_datetime(data.get("date_done")),
            platform_order_id=platform_order_id,
            odoo_order_id=str(data.get("origin", "") or data.get("id", "")) if data.get("id") is not None else None,
            odoo_order_name=str(data.get("origin", "") or data.get("name", "")) if data.get("name") is not None else None,
        )


class OdooRealProvider:
    def __init__(self, client: OdooClient, link_file: Optional[str] = None):
        self.client = client
        self.mapper = OdooMapper()
        self.link_resolver = OdooOrderLinkResolver(client, link_file=link_file)

    @staticmethod
    def _can_use_odoo_int_id(value: str) -> bool:
        if not value.isdigit():
            return False
        try:
            numeric = int(value)
        except ValueError:
            return False
        return 0 < numeric <= 2_147_483_647

    async def healthcheck(self) -> Dict[str, Any]:
        authenticated = await self.client.authenticate()
        if not authenticated:
            raise RuntimeError("Odoo authentication failed")
        return {
            "status": "healthy",
            "mode": "real",
            "message": "Authenticated to Odoo successfully",
        }

    def _build_product_domain(self, product_id: str) -> List[Any]:
        if product_id.isdigit():
            return [("product_id", "=", int(product_id))]
        return [("product_id.display_name", "ilike", product_id)]

    def _build_sale_order_domain(self, order_id: str) -> List[Any]:
        lookup_terms: List[Any] = [
            ("name", "=", order_id),
            ("client_order_ref", "=", order_id),
            ("origin", "=", order_id),
        ]
        if self._can_use_odoo_int_id(order_id):
            lookup_terms.insert(0, ("id", "=", int(order_id)))

        if len(lookup_terms) == 1:
            return lookup_terms

        return ["|"] * (len(lookup_terms) - 1) + lookup_terms

    def _build_picking_domain(self, order_id: str) -> List[Any]:
        lookup_terms: List[Any] = [
            ("origin", "=", order_id),
            ("name", "=", order_id),
        ]
        if self._can_use_odoo_int_id(order_id):
            lookup_terms.insert(0, ("id", "=", int(order_id)))

        if len(lookup_terms) == 1:
            return lookup_terms

        return ["|"] * (len(lookup_terms) - 1) + lookup_terms

    async def _search_sale_order_records(self, order_id: str) -> List[Dict[str, Any]]:
        return await self.client.execute(
            "sale.order",
            "search_read",
            [[*self._build_sale_order_domain(order_id)]],
            {"fields": ["id", "name", "state", "note", "user_id", "create_uid", "date_order", "write_date", "client_order_ref"]},
        )

    async def _search_picking_records(self, order_id: str) -> List[Dict[str, Any]]:
        return await self.client.execute(
            "stock.picking",
            "search_read",
            [self._build_picking_domain(order_id)],
            {"fields": ["id", "origin", "state", "location_id", "scheduled_date", "date_done", "name"]},
        )

    async def _resolve_linked_order_name(
        self,
        order_id: str,
        platform: Optional[str] = None,
    ) -> Optional[str]:
        if not platform:
            return None
        link = await self.link_resolver.resolve_order_link(platform, order_id)
        if not link:
            return None
        return link.get("odoo_order_name")

    @staticmethod
    def _should_preserve_platform_order_id(
        record: Dict[str, Any],
        order_id: str,
        platform: Optional[str] = None,
    ) -> bool:
        if not platform:
            return False
        candidate_values = {
            str(record.get("id", "")).strip(),
            str(record.get("name", "")).strip(),
            str(record.get("origin", "")).strip(),
        }
        return order_id not in candidate_values

    async def get_inventory(self, product_id: str) -> Optional[InventorySnapshot]:
        results = await self.client.execute(
            "stock.quant",
            "search_read",
            [[*self._build_product_domain(product_id)]],
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
    
    async def get_order_audit(
        self,
        order_id: str,
        platform: Optional[str] = None,
    ) -> Optional[OrderAuditSnapshot]:
        results = await self._search_sale_order_records(order_id)
        if results:
            platform_order_id = (
                order_id
                if self._should_preserve_platform_order_id(results[0], order_id, platform=platform)
                else None
            )
            return self.mapper.to_order_audit_snapshot(results[0], platform_order_id=platform_order_id)

        linked_order_name = await self._resolve_linked_order_name(order_id, platform=platform)
        if linked_order_name:
            linked_results = await self._search_sale_order_records(linked_order_name)
            if linked_results:
                return self.mapper.to_order_audit_snapshot(
                    linked_results[0],
                    platform_order_id=order_id,
                )
        return None

    async def list_order_audits(self) -> List[OrderAuditSnapshot]:
        results = await self.client.execute(
            "sale.order",
            "search_read",
            [[]],
            {"fields": ["id", "name", "state", "note", "user_id", "create_uid", "date_order", "write_date", "client_order_ref"]},
        )
        return [self.mapper.to_order_audit_snapshot(r) for r in (results or [])]
    
    async def get_order_exceptions(self, order_id: str) -> List[OrderExceptionSnapshot]:
        try:
            results = await self.client.execute(
                "sale.exception",
                "search_read",
                [[("order_id", "=", int(order_id))]] if order_id.isdigit() else [[("order_id.display_name", "=", order_id)]],
                {"fields": ["id", "order_id", "exception_type", "severity", "description", "status", "create_date", "resolved_at"]},
            )
        except Exception:
            return []
        return [self.mapper.to_order_exception_snapshot(r) for r in (results or [])]

    async def list_order_exceptions(self) -> List[OrderExceptionSnapshot]:
        try:
            results = await self.client.execute(
                "sale.exception",
                "search_read",
                [[]],
                {"fields": ["id", "order_id", "exception_type", "severity", "description", "status", "create_date", "resolved_at"]},
            )
        except Exception:
            return []
        return [self.mapper.to_order_exception_snapshot(r) for r in (results or [])]
    
    async def get_fulfillment(
        self,
        order_id: str,
        platform: Optional[str] = None,
    ) -> Optional[FulfillmentSnapshot]:
        results = await self._search_picking_records(order_id)
        if results:
            platform_order_id = (
                order_id
                if self._should_preserve_platform_order_id(results[0], order_id, platform=platform)
                else None
            )
            return self.mapper.to_fulfillment_snapshot(results[0], platform_order_id=platform_order_id)

        linked_order_name = await self._resolve_linked_order_name(order_id, platform=platform)
        if linked_order_name:
            linked_results = await self._search_picking_records(linked_order_name)
            if linked_results:
                return self.mapper.to_fulfillment_snapshot(
                    linked_results[0],
                    platform_order_id=order_id,
                )
        return None

    async def list_fulfillments(self) -> List[FulfillmentSnapshot]:
        results = await self.client.execute(
            "stock.picking",
            "search_read",
            [[]],
            {"fields": ["id", "origin", "state", "location_id", "scheduled_date", "date_done", "name"]},
        )
        return [self.mapper.to_fulfillment_snapshot(r) for r in (results or [])]
