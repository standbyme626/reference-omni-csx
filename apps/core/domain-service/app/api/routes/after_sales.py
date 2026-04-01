from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from pydantic import BaseModel

from app.core.response import success_response
from app.adapters.registry import PlatformRegistry
from app.services.platform_gateway_service import PlatformGatewayService
from app.services.after_sale_domain_service import AfterSaleDomainService

router = APIRouter()


class BatchGetAfterSalesRequest(BaseModel):
    requests: List[Dict[str, str]]


def get_after_sale_service() -> AfterSaleDomainService:
    registry = PlatformRegistry()
    gateway = PlatformGatewayService(registry)
    return AfterSaleDomainService(gateway)


@router.get("/{platform}/{after_sale_id}")
async def get_after_sale(
    platform: str,
    after_sale_id: str,
):
    try:
        service = get_after_sale_service()
        after_sale = service.get_after_sale(platform, after_sale_id)
        return success_response({"after_sale": after_sale})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"After-sale not found: {after_sale_id}")


@router.get("/{platform}/by-order/{order_id}")
async def get_after_sale_by_order(
    platform: str,
    order_id: str,
):
    try:
        service = get_after_sale_service()
        after_sale = service.get_after_sale_by_order(platform, order_id)
        return success_response({"after_sale": after_sale, "order_id": order_id})
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"After-sale not found for order: {order_id}")


@router.post("/batch-get")
async def batch_get_after_sales(request: BatchGetAfterSalesRequest):
    service = get_after_sale_service()
    result = service.batch_get_after_sales(request.requests)
    return success_response(result)
