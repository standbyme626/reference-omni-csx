from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from pydantic import BaseModel

from app.core.response import success_response
from app.dependencies import get_after_sale_domain_service
from app.services.after_sale_domain_service import AfterSaleDomainService

router = APIRouter()


class BatchGetAfterSalesRequest(BaseModel):
    requests: List[Dict[str, str]]


@router.get("/{platform}/{after_sale_id}")
async def get_after_sale(
    platform: str,
    after_sale_id: str,
    official_run_id: str | None = None,
    service: AfterSaleDomainService = Depends(get_after_sale_domain_service),
):
    try:
        after_sale = service.get_after_sale(
            platform,
            after_sale_id,
            official_run_id=official_run_id,
        )
        return success_response({"after_sale": after_sale})
    except ValueError as e:
        status_code = 404 if "not found" in str(e).lower() else 400
        raise HTTPException(status_code=status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"After-sale not found: {after_sale_id}")


@router.get("/{platform}/by-order/{order_id}")
async def get_after_sale_by_order(
    platform: str,
    order_id: str,
    official_run_id: str | None = None,
    service: AfterSaleDomainService = Depends(get_after_sale_domain_service),
):
    try:
        after_sale = service.get_after_sale_by_order(
            platform,
            order_id,
            official_run_id=official_run_id,
        )
        return success_response({"after_sale": after_sale, "order_id": order_id})
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"After-sale not found for order: {order_id}")


@router.post("/batch-get")
async def batch_get_after_sales(
    request: BatchGetAfterSalesRequest,
    service: AfterSaleDomainService = Depends(get_after_sale_domain_service),
):
    result = service.batch_get_after_sales(request.requests)
    return success_response(result)
