import pytest
from datetime import datetime

from app.services.business_context_service import BusinessContextService
from app.adapters.registry import PlatformRegistry
from app.services.platform_gateway_service import PlatformGatewayService
from app.services.order_service import OrderService
from app.services.shipment_service import ShipmentService
from app.services.after_sale_service import AfterSaleService
from app.services.conversation_service import ConversationService
from providers.odoo.provider import OdooProvider, OdooProviderMode


@pytest.fixture
def business_context_service():
    registry = PlatformRegistry()
    gateway = PlatformGatewayService(registry)
    order_service = OrderService(gateway, registry)
    shipment_service = ShipmentService(gateway)
    after_sale_service = AfterSaleService(gateway)
    conversation_service = ConversationService(gateway, registry)
    odoo_provider = OdooProvider(mode=OdooProviderMode.MOCK)
    
    return BusinessContextService(
        gateway=gateway,
        order_service=order_service,
        shipment_service=shipment_service,
        after_sale_service=after_sale_service,
        conversation_service=conversation_service,
        odoo_provider=odoo_provider,
    )


class TestBusinessContextWithOdoo:
    def test_build_order_context_with_inventory(self, business_context_service):
        context = business_context_service.build_context(
            platform="taobao",
            biz_id="ORDER_001",
            biz_type="order",
            options={"include_inventory": True},
        )
        
        assert context["biz_type"] == "order"
        assert "inventory_snapshot" in context
        assert context["inventory_snapshot"]["product_id"] == "ORDER_001"
        assert context["inventory_snapshot"]["quantity"] == 200
    
    def test_build_order_context_without_inventory(self, business_context_service):
        context = business_context_service.build_context(
            platform="taobao",
            biz_id="ORDER_001",
            biz_type="order",
            options={"include_inventory": False},
        )
        
        assert context["biz_type"] == "order"
        assert "inventory_snapshot" not in context or context.get("inventory_snapshot") is None
    
    def test_build_order_context_with_order_audit(self, business_context_service):
        context = business_context_service.build_context(
            platform="taobao",
            biz_id="ORDER_001",
            biz_type="order",
            options={},
        )
        
        assert "order_audit_snapshot" in context
        assert context["order_audit_snapshot"]["order_id"] == "ORDER_001"
        assert context["order_audit_snapshot"]["audit_status"] == "approved"
    
    def test_build_order_context_with_exceptions(self, business_context_service):
        context = business_context_service.build_context(
            platform="taobao",
            biz_id="ORDER_002",
            biz_type="order",
            options={},
        )
        
        assert "order_exception_snapshots" in context
        assert len(context["order_exception_snapshots"]) == 2
        assert context["order_exception_snapshots"][0]["exception_type"] == "address_issue"
    
    def test_build_order_context_with_fulfillment(self, business_context_service):
        context = business_context_service.build_context(
            platform="taobao",
            biz_id="ORDER_001",
            biz_type="order",
            options={},
        )
        
        assert "fulfillment_snapshot" in context
        assert context["fulfillment_snapshot"]["order_id"] == "ORDER_001"
        assert context["fulfillment_snapshot"]["status"] == "picking"
    
    def test_build_conversation_context(self, business_context_service):
        context = business_context_service.build_context(
            platform="wecom_kf",
            biz_id="CONV_001",
            biz_type="conversation",
            options={},
        )
        
        assert context["biz_type"] == "conversation"
        assert "conversation_snapshot" in context
        assert context["order_audit_snapshot"] is None
        assert context["order_exception_snapshots"] == []
    
    def test_build_after_sale_context(self, business_context_service):
        context = business_context_service.build_context(
            platform="taobao",
            biz_id="AFTER_SALE_001",
            biz_type="after_sale",
            options={},
        )
        
        assert context["biz_type"] == "after_sale"
        assert "after_sale_snapshot" in context
    
    def test_odoo_provider_healthcheck(self):
        provider = OdooProvider(mode=OdooProviderMode.MOCK)
        health = provider.healthcheck()
        
        assert health["status"] == "healthy"
        assert health["mode"] == "mock"
    
    def test_empty_inventory_returns_none(self, business_context_service):
        context = business_context_service.build_context(
            platform="taobao",
            biz_id="NONEXISTENT_ORDER",
            biz_type="order",
            options={"include_inventory": True},
        )
        
        assert context.get("inventory_snapshot") is None or "inventory_snapshot" not in context
    
    def test_empty_order_audit_returns_none(self, business_context_service):
        context = business_context_service.build_context(
            platform="taobao",
            biz_id="NONEXISTENT_ORDER",
            biz_type="order",
            options={},
        )
        
        assert context.get("order_audit_snapshot") is None
    
    def test_empty_exceptions_returns_empty_list(self, business_context_service):
        context = business_context_service.build_context(
            platform="taobao",
            biz_id="NONEXISTENT_ORDER",
            biz_type="order",
            options={},
        )
        
        assert context.get("order_exception_snapshots") == []
