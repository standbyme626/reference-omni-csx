from typing import Dict, Any, Optional, List
from enum import Enum

from providers.odoo.mock.provider import OdooMockProvider, InventorySnapshot, OrderAuditSnapshot, OrderExceptionSnapshot, FulfillmentSnapshot


class OdooProviderMode(str, Enum):
    MOCK = "mock"
    REAL = "real"


class OdooProvider:
    def __init__(self, mode: OdooProviderMode = OdooProviderMode.MOCK, **kwargs):
        self.mode = mode
        self._mock_provider: Optional[OdooMockProvider] = None
        self._real_provider = None
        
        if mode == OdooProviderMode.MOCK:
            self._mock_provider = OdooMockProvider()
        else:
            from providers.odoo.real.provider import OdooRealProvider, OdooClient
            client = OdooClient(
                base_url=kwargs.get("base_url", "http://localhost:8069"),
                db=kwargs.get("db", "odoo"),
                username=kwargs.get("username", "admin"),
                api_key=kwargs.get("api_key", ""),
            )
            self._real_provider = OdooRealProvider(client)
    
    def get_inventory(self, product_id: str) -> Optional[InventorySnapshot]:
        if self.mode == OdooProviderMode.MOCK:
            return self._mock_provider.get_inventory(product_id)
        raise NotImplementedError("Real provider requires async call")
    
    async def get_inventory_async(self, product_id: str) -> Optional[InventorySnapshot]:
        if self.mode == OdooProviderMode.MOCK:
            return self._mock_provider.get_inventory(product_id)
        return await self._real_provider.get_inventory(product_id)
    
    def list_inventory(self, warehouse: Optional[str] = None) -> List[InventorySnapshot]:
        if self.mode == OdooProviderMode.MOCK:
            return self._mock_provider.list_inventory(warehouse)
        raise NotImplementedError("Real provider requires async call")
    
    async def list_inventory_async(self, warehouse: Optional[str] = None) -> List[InventorySnapshot]:
        if self.mode == OdooProviderMode.MOCK:
            return self._mock_provider.list_inventory(warehouse)
        return await self._real_provider.list_inventory(warehouse)
    
    def get_order_audit(self, order_id: str) -> Optional[OrderAuditSnapshot]:
        if self.mode == OdooProviderMode.MOCK:
            return self._mock_provider.get_order_audit(order_id)
        raise NotImplementedError("Real provider requires async call")

    def list_order_audits(self) -> List[OrderAuditSnapshot]:
        if self.mode == OdooProviderMode.MOCK:
            return self._mock_provider.list_order_audits()
        raise NotImplementedError("Real provider requires async call")
    
    async def get_order_audit_async(self, order_id: str) -> Optional[OrderAuditSnapshot]:
        if self.mode == OdooProviderMode.MOCK:
            return self._mock_provider.get_order_audit(order_id)
        return await self._real_provider.get_order_audit(order_id)

    async def list_order_audits_async(self) -> List[OrderAuditSnapshot]:
        if self.mode == OdooProviderMode.MOCK:
            return self._mock_provider.list_order_audits()
        return await self._real_provider.list_order_audits()
    
    def get_order_exceptions(self, order_id: str) -> List[OrderExceptionSnapshot]:
        if self.mode == OdooProviderMode.MOCK:
            return self._mock_provider.get_order_exceptions(order_id)
        raise NotImplementedError("Real provider requires async call")

    def list_order_exceptions(self) -> List[OrderExceptionSnapshot]:
        if self.mode == OdooProviderMode.MOCK:
            return self._mock_provider.list_order_exceptions()
        raise NotImplementedError("Real provider requires async call")
    
    async def get_order_exceptions_async(self, order_id: str) -> List[OrderExceptionSnapshot]:
        if self.mode == OdooProviderMode.MOCK:
            return self._mock_provider.get_order_exceptions(order_id)
        return await self._real_provider.get_order_exceptions(order_id)

    async def list_order_exceptions_async(self) -> List[OrderExceptionSnapshot]:
        if self.mode == OdooProviderMode.MOCK:
            return self._mock_provider.list_order_exceptions()
        return await self._real_provider.list_order_exceptions()
    
    def get_fulfillment(self, order_id: str) -> Optional[FulfillmentSnapshot]:
        if self.mode == OdooProviderMode.MOCK:
            return self._mock_provider.get_fulfillment(order_id)
        raise NotImplementedError("Real provider requires async call")

    def list_fulfillments(self) -> List[FulfillmentSnapshot]:
        if self.mode == OdooProviderMode.MOCK:
            return self._mock_provider.list_fulfillments()
        raise NotImplementedError("Real provider requires async call")
    
    async def get_fulfillment_async(self, order_id: str) -> Optional[FulfillmentSnapshot]:
        if self.mode == OdooProviderMode.MOCK:
            return self._mock_provider.get_fulfillment(order_id)
        return await self._real_provider.get_fulfillment(order_id)

    async def list_fulfillments_async(self) -> List[FulfillmentSnapshot]:
        if self.mode == OdooProviderMode.MOCK:
            return self._mock_provider.list_fulfillments()
        return await self._real_provider.list_fulfillments()
    
    def update_inventory(self, product_id: str, quantity: int) -> InventorySnapshot:
        if self.mode == OdooProviderMode.MOCK:
            return self._mock_provider.update_inventory(product_id, quantity)
        raise NotImplementedError("Real provider requires async call")
    
    def create_order_exception(
        self,
        order_id: str,
        exception_type: str,
        severity: str,
        description: str,
    ) -> OrderExceptionSnapshot:
        if self.mode == OdooProviderMode.MOCK:
            return self._mock_provider.create_order_exception(
                order_id, exception_type, severity, description
            )
        raise NotImplementedError("Real provider requires async call")
    
    def healthcheck(self) -> Dict[str, Any]:
        if self.mode == OdooProviderMode.MOCK:
            return {
                "status": "healthy",
                "mode": "mock",
                "message": "Mock provider is always healthy",
            }
        try:
            return self._real_provider.healthcheck()
        except Exception as e:
            return {
                "status": "unhealthy",
                "mode": "real",
                "message": str(e),
            }
    
    async def healthcheck_async(self) -> Dict[str, Any]:
        if self.mode == OdooProviderMode.MOCK:
            return {
                "status": "healthy",
                "mode": "mock",
                "message": "Mock provider is always healthy",
            }
        try:
            return await self._real_provider.healthcheck()
        except Exception as e:
            return {
                "status": "unhealthy",
                "mode": "real",
                "message": str(e),
            }
