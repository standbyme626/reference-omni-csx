import pytest

from providers.odoo.mock.provider import OdooMockProvider
from providers.odoo.provider import OdooProvider, OdooProviderMode


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
