from fastapi import APIRouter, HTTPException, Depends
import logging

from app.core.response import success_response
from app.dependencies import get_business_context_service
from app.services.business_context_service import BusinessContextService
from app.schemas.context import BusinessContextBuildRequest


router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/{platform}/{biz_id}")
async def get_context(
    platform: str,
    biz_id: str,
    official_run_id: str | None = None,
    service: BusinessContextService = Depends(get_business_context_service),
):
    try:
        context = service.get_context(
            platform,
            biz_id,
            official_run_id=official_run_id,
        )
        logger.info(
            "context queried official_run_id=%s platform=%s biz_id=%s",
            official_run_id,
            platform,
            biz_id,
        )
        return success_response(context)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Context not found: {biz_id}")


@router.post("/build")
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
            official_run_id=request.official_run_id,
        )
        logger.info(
            "context built official_run_id=%s platform=%s biz_id=%s biz_type=%s",
            request.official_run_id,
            request.platform,
            request.biz_id,
            request.biz_type,
        )
        return success_response(context)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/refresh")
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
            official_run_id=request.official_run_id,
        )
        logger.info(
            "context refreshed official_run_id=%s platform=%s biz_id=%s biz_type=%s",
            request.official_run_id,
            request.platform,
            request.biz_id,
            request.biz_type,
        )
        return success_response(context)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
