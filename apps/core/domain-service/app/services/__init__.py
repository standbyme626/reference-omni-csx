"""Domain service layer — single-responsibility services."""

from app.services.order_service import OrderService
from app.services.shipment_service import ShipmentService
from app.services.after_sale_service import AfterSaleService
from app.services.conversation_domain_service import ConversationDomainService
from app.services.context_resolver import ContextResolver
from app.services.risk_evaluator import RiskEvaluator
from app.services.reply_generator import ReplyGenerator
from app.services.push_events_service import PushEventsService
from app.services.operations_service import OperationsService
from app.services.recommendation_service import RecommendationService
from app.services.integration_service import IntegrationService
from app.services.analytics_service import AnalyticsService
from app.services.quality_service import QualityService
from app.services.risk_service import RiskService
from app.services.platform_gateway_service import PlatformGatewayService
from app.services.push_event_tracker import PushEventTracker
from app.services.business_context_service import BusinessContextService

# Backward-compatible aliases for old import paths.
OrderDomainService = __import__(
    "app.services.order_domain_service",
    fromlist=["OrderDomainService"],
).OrderDomainService
ShipmentDomainService = __import__(
    "app.services.shipment_domain_service",
    fromlist=["ShipmentDomainService"],
).ShipmentDomainService
AfterSaleDomainService = __import__(
    "app.services.after_sale_domain_service",
    fromlist=["AfterSaleDomainService"],
).AfterSaleDomainService

__all__ = [
    "OrderService",
    "ShipmentService",
    "AfterSaleService",
    "ConversationDomainService",
    "ContextResolver",
    "RiskEvaluator",
    "ReplyGenerator",
    "PushEventsService",
    "OperationsService",
    "RecommendationService",
    "IntegrationService",
    "AnalyticsService",
    "QualityService",
    "RiskService",
    "PlatformGatewayService",
    "PushEventTracker",
    "BusinessContextService",
    # Backward-compatible aliases.
    "OrderDomainService",
    "ShipmentDomainService",
    "AfterSaleDomainService",
]
