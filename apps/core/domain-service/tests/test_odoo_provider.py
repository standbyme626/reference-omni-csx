import asyncio

from providers.odoo.mock.provider import OdooMockProvider
from providers.odoo.provider import OdooProvider, OdooProviderMode
from providers.odoo.real.provider import OdooRealProvider


class TestOdooMockProvider:
    def test_get_inventory(self):
        provider = OdooMockProvider()
        
        inventory = provider.get_inventory("PROD_001")
        
        assert inventory is not None
        assert inventory.product_id == "PROD_001"
        assert inventory.quantity == 100
    
    def test_get_inventory_not_found(self):
        provider = OdooMockProvider()
        
        inventory = provider.get_inventory("NONEXISTENT")
        
        assert inventory is None
    
    def test_list_inventory(self):
        provider = OdooMockProvider()
        
        inventory_list = provider.list_inventory()
        
        assert len(inventory_list) >= 1
    
    def test_update_inventory(self):
        provider = OdooMockProvider()
        
        updated = provider.update_inventory("PROD_001", 200)
        
        assert updated.quantity == 200
        assert updated.available_quantity == 190
    
    def test_create_order_exception(self):
        provider = OdooMockProvider()
        
        exception = provider.create_order_exception(
            order_id="ORDER_001",
            exception_type="stock_out",
            severity="high",
            description="库存不足",
        )
        
        assert exception.order_id == "ORDER_001"
        assert exception.exception_type == "stock_out"
        assert exception.status == "open"


class TestOdooProvider:
    def test_mock_mode(self):
        provider = OdooProvider(mode=OdooProviderMode.MOCK)
        
        inventory = provider.get_inventory("PROD_001")
        
        assert inventory is not None
        assert inventory.product_id == "PROD_001"
    
    def test_list_inventory_mock(self):
        provider = OdooProvider(mode=OdooProviderMode.MOCK)
        
        inventory_list = provider.list_inventory()
        
        assert len(inventory_list) >= 1

    def test_real_mode_healthcheck_bridges_async_provider(self):
        class FakeRealProvider:
            async def healthcheck(self):
                return {
                    "status": "healthy",
                    "mode": "real",
                    "message": "ok",
                }

        provider = OdooProvider(mode=OdooProviderMode.MOCK)
        provider.mode = OdooProviderMode.REAL
        provider._real_provider = FakeRealProvider()

        result = provider.healthcheck()

        assert result["status"] == "healthy"
        assert result["mode"] == "real"


class FakeOdooClient:
    def __init__(self):
        self.authenticated = False
        self.calls = []

    async def authenticate(self):
        self.authenticated = True
        return True

    async def execute(self, model, method, args, kwargs=None):
        self.calls.append(
            {
                "model": model,
                "method": method,
                "args": args,
                "kwargs": kwargs or {},
            }
        )
        if model == "sale.order":
            return [
                {
                    "id": 24,
                    "name": "S00024",
                    "state": "sale",
                    "note": False,
                    "user_id": [6, "Marc Demo"],
                    "create_uid": [1, "OdooBot"],
                    "date_order": "2026-03-31 18:17:18",
                    "write_date": "2026-03-31 18:17:17",
                    "client_order_ref": False,
                }
            ]
        if model == "stock.picking":
            return []
        if model == "sale.exception":
            return None
        return []


class TestOdooRealProvider:
    def test_list_order_audits_maps_standard_sale_order_fields(self):
        provider = OdooRealProvider(FakeOdooClient())

        audits = asyncio.run(provider.list_order_audits())

        assert len(audits) == 1
        assert audits[0].order_id == "24"
        assert audits[0].audit_status == "approved"
        assert audits[0].audited_by == "Marc Demo"

    def test_list_order_exceptions_returns_empty_list_when_model_missing(self):
        provider = OdooRealProvider(FakeOdooClient())

        exceptions = asyncio.run(provider.list_order_exceptions())

        assert exceptions == []

    def test_healthcheck_uses_authentication(self):
        client = FakeOdooClient()
        provider = OdooRealProvider(client)

        result = asyncio.run(provider.healthcheck())

        assert result["status"] == "healthy"
        assert result["mode"] == "real"
        assert client.authenticated is True

    def test_get_order_audit_does_not_treat_large_numeric_external_id_as_odoo_pk(self):
        client = FakeOdooClient()
        provider = OdooRealProvider(client)

        asyncio.run(provider.get_order_audit("98765432101234"))

        domain = client.calls[-1]["args"][0]

        assert ("id", "=", 98765432101234) not in domain
        assert ("name", "=", "98765432101234") in domain
        assert ("client_order_ref", "=", "98765432101234") in domain
        assert ("origin", "=", "98765432101234") in domain

    def test_get_fulfillment_does_not_treat_large_numeric_external_id_as_odoo_pk(self):
        client = FakeOdooClient()
        provider = OdooRealProvider(client)

        asyncio.run(provider.get_fulfillment("98765432101234"))

        domain = client.calls[-1]["args"][0]

        assert ("id", "=", 98765432101234) not in domain
        assert ("origin", "=", "98765432101234") in domain
        assert ("name", "=", "98765432101234") in domain

    def test_get_order_audit_passes_platform_to_link_resolver(self):
        class EmptyClient(FakeOdooClient):
            async def execute(self, model, method, args, kwargs=None):
                self.calls.append(
                    {
                        "model": model,
                        "method": method,
                        "args": args,
                        "kwargs": kwargs or {},
                    }
                )
                return []

        client = EmptyClient()
        provider = OdooRealProvider(client)
        captured = {}

        async def fake_resolve_order_link(platform, platform_order_id):
            captured["platform"] = platform
            captured["platform_order_id"] = platform_order_id
            return None

        provider.link_resolver.resolve_order_link = fake_resolve_order_link

        asyncio.run(provider.get_order_audit("98765432101234", platform="jd"))

        assert captured == {
            "platform": "jd",
            "platform_order_id": "98765432101234",
        }

    def test_get_order_audit_preserves_platform_order_id_on_client_order_ref_match(self):
        class ClientOrderRefClient(FakeOdooClient):
            async def execute(self, model, method, args, kwargs=None):
                self.calls.append(
                    {
                        "model": model,
                        "method": method,
                        "args": args,
                        "kwargs": kwargs or {},
                    }
                )
                if model == "sale.order":
                    return [
                        {
                            "id": 29,
                            "name": "S00029",
                            "state": "draft",
                            "note": False,
                            "user_id": [2, "Mitchell Admin"],
                            "create_uid": [2, "Mitchell Admin"],
                            "date_order": "2026-04-02 16:05:37",
                            "write_date": "2026-04-02 16:05:37",
                            "client_order_ref": "98765432101234",
                        }
                    ]
                return []

        provider = OdooRealProvider(ClientOrderRefClient())

        audit = asyncio.run(provider.get_order_audit("98765432101234", platform="jd"))

        assert audit is not None
        assert audit.order_id == "98765432101234"
        assert audit.platform_order_id == "98765432101234"
        assert audit.odoo_order_id == "29"
