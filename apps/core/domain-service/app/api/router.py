from fastapi import APIRouter

from app.api.routes import (
    health,
    orders,
    shipments,
    after_sales,
    conversations,
    context,
    recommendations,
    quality,
    risk,
    integration,
    analytics,
    operations,
)

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(orders.router, prefix="/api/orders", tags=["orders"])
api_router.include_router(shipments.router, prefix="/api/shipments", tags=["shipments"])
api_router.include_router(after_sales.router, prefix="/api/after-sales", tags=["after-sales"])
api_router.include_router(conversations.router, prefix="/api/conversations", tags=["conversations"])
api_router.include_router(context.router, prefix="/api/context", tags=["context"])
api_router.include_router(recommendations.router, prefix="/api/recommendations", tags=["recommendations"])
api_router.include_router(quality.router, prefix="/api/quality", tags=["quality"])
api_router.include_router(risk.router, prefix="/api/risk", tags=["risk"])
api_router.include_router(integration.router, prefix="/api/integration", tags=["integration"])
api_router.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
api_router.include_router(operations.router, prefix="/api", tags=["operations"])
