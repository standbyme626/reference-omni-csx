from functools import lru_cache
from typing import Generator

from app.adapters.registry import PlatformRegistry, bootstrap_default_registry
from app.services.platform_gateway_service import PlatformGatewayService
from app.services.order_domain_service import OrderDomainService
from app.services.shipment_domain_service import ShipmentDomainService
from app.services.after_sale_domain_service import AfterSaleDomainService
from app.services.conversation_domain_service import ConversationDomainService
from app.services.business_context_service import BusinessContextService
from app.services.integration_service import IntegrationService
from providers.odoo.provider import OdooProvider, OdooProviderMode
from app.core.config import settings


@lru_cache()
def get_platform_registry() -> PlatformRegistry:
    return bootstrap_default_registry()


@lru_cache()
def get_platform_gateway_service() -> PlatformGatewayService:
    registry = get_platform_registry()
    return PlatformGatewayService(registry)


@lru_cache()
def get_order_domain_service() -> OrderDomainService:
    gateway = get_platform_gateway_service()
    registry = get_platform_registry()
    return OrderDomainService(gateway, registry)


@lru_cache()
def get_shipment_domain_service() -> ShipmentDomainService:
    gateway = get_platform_gateway_service()
    return ShipmentDomainService(gateway)


@lru_cache()
def get_after_sale_domain_service() -> AfterSaleDomainService:
    gateway = get_platform_gateway_service()
    return AfterSaleDomainService(gateway)


@lru_cache()
def get_conversation_domain_service() -> ConversationDomainService:
    gateway = get_platform_gateway_service()
    return ConversationDomainService(gateway)


@lru_cache()
def get_odoo_provider() -> OdooProvider:
    mode_value = (settings.odoo_provider_mode or settings.default_provider_mode or "mock").lower()
    mode = OdooProviderMode.REAL if mode_value == OdooProviderMode.REAL.value else OdooProviderMode.MOCK
    return OdooProvider(
        mode=mode,
        base_url=settings.odoo_base_url,
        db=settings.odoo_db,
        username=settings.odoo_username,
        api_key=settings.odoo_api_key,
    )


def get_business_context_service() -> BusinessContextService:
    gateway = get_platform_gateway_service()
    order_service = get_order_domain_service()
    shipment_service = get_shipment_domain_service()
    after_sale_service = get_after_sale_domain_service()
    conversation_service = get_conversation_domain_service()
    odoo_provider = get_odoo_provider()
    
    return BusinessContextService(
        gateway=gateway,
        order_service=order_service,
        shipment_service=shipment_service,
        after_sale_service=after_sale_service,
        conversation_service=conversation_service,
        odoo_provider=odoo_provider,
    )


def get_integration_service() -> IntegrationService:
    odoo_provider = get_odoo_provider()
    return IntegrationService(odoo_provider)
