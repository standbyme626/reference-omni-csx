from functools import lru_cache
from typing import Optional

from app.adapters.registry import PlatformRegistry, bootstrap_default_registry
from app.core.config import settings
from app.services.after_sale_service import AfterSaleService
from app.services.business_context_service import BusinessContextService
from app.services.conversation_service import ConversationService
from app.services.context_resolver import ContextResolver
from app.services.integration_service import IntegrationService
from app.services.order_service import OrderService
from app.services.platform_gateway_service import PlatformGatewayService
from app.services.push_event_tracker import PushEventTracker
from app.services.push_events_service import PushEventsService
from app.services.reply_generator import ReplyGenerator
from app.services.recommendation_service import RecommendationService
from app.services.risk_evaluator import RiskEvaluator
from app.services.shipment_service import ShipmentService
from app.services.operations_service import OperationsService

from providers.odoo.provider import OdooProvider, OdooProviderMode


# ---------------------------------------------------------------------------
# Core infrastructure
# ---------------------------------------------------------------------------

@lru_cache()
def get_platform_registry() -> PlatformRegistry:
    return bootstrap_default_registry()


@lru_cache()
def get_platform_gateway_service() -> PlatformGatewayService:
    registry = get_platform_registry()
    return PlatformGatewayService(registry)


@lru_cache()
def get_odoo_provider() -> OdooProvider:
    mode_value = (settings.odoo_provider_mode or OdooProviderMode.REAL.value).lower()
    mode = OdooProviderMode.REAL if mode_value == OdooProviderMode.REAL.value else OdooProviderMode.MOCK
    return OdooProvider(
        mode=mode,
        base_url=settings.odoo_base_url,
        db=settings.odoo_db,
        username=settings.odoo_username,
        api_key=settings.odoo_api_key,
    )


@lru_cache()
def get_push_event_tracker() -> PushEventTracker:
    return PushEventTracker()


# ---------------------------------------------------------------------------
# Domain services
# ---------------------------------------------------------------------------

@lru_cache()
def get_order_service() -> OrderService:
    gateway = get_platform_gateway_service()
    registry = get_platform_registry()
    return OrderService(gateway, registry)


@lru_cache()
def get_shipment_service() -> ShipmentService:
    gateway = get_platform_gateway_service()
    return ShipmentService(gateway)


@lru_cache()
def get_after_sale_service() -> AfterSaleService:
    gateway = get_platform_gateway_service()
    return AfterSaleService(gateway)


@lru_cache()
def get_conversation_service() -> ConversationService:
    gateway = get_platform_gateway_service()
    registry = get_platform_registry()
    return ConversationService(gateway, registry)


# ---------------------------------------------------------------------------
# Composite / higher-level services
# ---------------------------------------------------------------------------

@lru_cache()
def get_push_events_service() -> PushEventsService:
    return PushEventsService(get_push_event_tracker())


@lru_cache()
def get_risk_evaluator() -> RiskEvaluator:
    return RiskEvaluator()


@lru_cache()
def get_reply_generator() -> ReplyGenerator:
    return ReplyGenerator()


@lru_cache()
def get_context_resolver() -> ContextResolver:
    return ContextResolver(
        order_service=get_order_service(),
        shipment_service=get_shipment_service(),
        after_sale_service=get_after_sale_service(),
        conversation_service=get_conversation_service(),
        odoo_provider=get_odoo_provider(),
        push_events_service=get_push_events_service(),
        risk_evaluator=get_risk_evaluator(),
    )


@lru_cache()
def get_business_context_service() -> BusinessContextService:
    gateway = get_platform_gateway_service()
    return BusinessContextService(
        gateway=gateway,
        order_service=get_order_service(),
        shipment_service=get_shipment_service(),
        after_sale_service=get_after_sale_service(),
        conversation_service=get_conversation_service(),
        odoo_provider=get_odoo_provider(),
        push_event_tracker=get_push_event_tracker(),
    )


@lru_cache()
def get_recommendation_service() -> RecommendationService:
    return RecommendationService(get_business_context_service())


@lru_cache()
def get_integration_service() -> IntegrationService:
    return IntegrationService(get_odoo_provider())


@lru_cache()
def get_operations_service() -> OperationsService:
    return OperationsService()


# ---------------------------------------------------------------------------
# Backward-compatible aliases (used by some existing modules)
# ---------------------------------------------------------------------------

@lru_cache()
def get_order_domain_service():
    """Backward-compatible alias for OrderService."""
    return get_order_service()


@lru_cache()
def get_shipment_domain_service():
    """Backward-compatible alias for ShipmentService."""
    return get_shipment_service()


@lru_cache()
def get_after_sale_domain_service():
    """Backward-compatible alias for AfterSaleService."""
    return get_after_sale_service()
