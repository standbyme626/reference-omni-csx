from fastapi import APIRouter, Query
from typing import Optional
from pydantic import BaseModel

from app.core.response import success_response
from app.services.analytics_service import AnalyticsService


router = APIRouter()


@router.get("/summaries")
async def get_summaries():
    service = AnalyticsService()
    
    conversations_result = service.get_conversations_summary("all")
    
    return success_response({
        "total_conversations": conversations_result.get("total_conversations", 0),
        "active_conversations": conversations_result.get("status_breakdown", {}).get("in_session", 0) + conversations_result.get("status_breakdown", {}).get("pending", 0),
        "pending_followups": 5,
        "risk_alerts": 3,
    })


@router.get("/orders/summary")
async def get_orders_summary(
    platform: Optional[str] = Query("all", description="Platform filter (default: all)"),
):
    service = AnalyticsService()
    result = service.get_orders_summary(platform)
    return success_response(result)


@router.get("/conversations/summary")
async def get_conversations_summary(
    platform: Optional[str] = Query("all", description="Platform filter (default: all)"),
):
    service = AnalyticsService()
    result = service.get_conversations_summary(platform)
    return success_response(result)


@router.get("/platforms/coverage")
async def get_platforms_coverage():
    service = AnalyticsService()
    result = service.get_platforms_coverage()
    return success_response(result)
