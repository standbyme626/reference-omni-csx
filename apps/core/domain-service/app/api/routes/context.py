from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime

from app.core.response import success_response
from app.dependencies import get_business_context_service
from app.services.business_context_service import BusinessContextService
from app.schemas.context import BusinessContextResponse, BusinessContextBuildRequest


router = APIRouter()


@router.get("/{platform}/{biz_id}", response_model=BusinessContextResponse)
async def get_context(
    platform: str,
    biz_id: str,
    service: BusinessContextService = Depends(get_business_context_service),
):
    try:
        context = service.get_context(platform, biz_id)
        context["created_at"] = datetime.fromisoformat(context["created_at"])
        context["updated_at"] = datetime.fromisoformat(context["updated_at"])
        return BusinessContextResponse(**context)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Context not found: {biz_id}")


@router.post("/build", response_model=BusinessContextResponse)
async def build_context(
    request: BusinessContextBuildRequest,
    service: BusinessContextService = Depends(get_business_context_service),
):
    try:
        options = {
            "include_inventory": request.include_inventory,
            "include_risk": request.include_risk,
            "include_quality": request.include_quality,
            "include_recommendations": request.include_recommendations,
        }
        context = service.build_context(
            request.platform,
            request.biz_id,
            request.biz_type,
            options,
        )
        context["created_at"] = datetime.fromisoformat(context["created_at"])
        context["updated_at"] = datetime.fromisoformat(context["updated_at"])
        return BusinessContextResponse(**context)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/refresh", response_model=BusinessContextResponse)
async def refresh_context(
    request: BusinessContextBuildRequest,
    service: BusinessContextService = Depends(get_business_context_service),
):
    try:
        options = {
            "include_inventory": request.include_inventory,
            "include_risk": request.include_risk,
            "include_quality": request.include_quality,
            "include_recommendations": request.include_recommendations,
        }
        context = service.build_context(
            request.platform,
            request.biz_id,
            request.biz_type,
            options,
        )
        context["created_at"] = datetime.fromisoformat(context["created_at"])
        context["updated_at"] = datetime.fromisoformat(context["updated_at"])
        return BusinessContextResponse(**context)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
