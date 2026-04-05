from fastapi import APIRouter, Depends
from typing import List, Dict
from pydantic import BaseModel

from app.core.response import success_response
from app.dependencies import get_after_sale_service
from app.services.after_sale_service import AfterSaleService

router = APIRouter()


class BatchGetAfterSalesRequest(BaseModel):
    requests: List[Dict[str, str]]


@router.get("/{platform}/{after_sale_id}")
async def get_after_sale(
    platform: str, after_sale_id: str, official_run_id: str | None = None,
    service: AfterSaleService = Depends(get_after_sale_service),
):
    after_sale = service.get_after_sale(platform, after_sale_id, official_run_id=official_run_id)
    return success_response({"after_sale": after_sale})


@router.get("/{platform}/by-order/{order_id}")
async def get_after_sale_by_order(
    platform: str, order_id: str, official_run_id: str | None = None,
    service: AfterSaleService = Depends(get_after_sale_service),
):
    after_sale = service.get_after_sale_by_order(platform, order_id, official_run_id=official_run_id)
    return success_response({"after_sale": after_sale, "order_id": order_id})


@router.post("/batch-get")
async def batch_get_after_sales(
    request: BatchGetAfterSalesRequest,
    service: AfterSaleService = Depends(get_after_sale_service),
):
    result = service.batch_get_after_sales(request.requests)
    return success_response(result)
