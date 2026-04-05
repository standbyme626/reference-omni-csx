from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict
from pydantic import BaseModel

from app.core.response import success_response
from app.dependencies import get_order_domain_service
from app.services.order_domain_service import OrderDomainService

router = APIRouter()


class BatchGetOrdersRequest(BaseModel):
    requests: List[Dict[str, str]]


@router.get("/{platform}/{order_id}")
async def get_order(
    platform: str,
    order_id: str,
    official_run_id: str | None = None,
    service: OrderDomainService = Depends(get_order_domain_service),
):
    try:
        order = service.get_order(platform, order_id, official_run_id=official_run_id)
        return success_response({"order": order})
    except ValueError as e:
        message = str(e).lower()
        status_code = 404 if "not found" in message or "no order fixture found" in message else 400
        raise HTTPException(status_code=status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Order not found: {order_id}")


@router.post("/batch-get")
async def batch_get_orders(
    request: BatchGetOrdersRequest,
    service: OrderDomainService = Depends(get_order_domain_service),
):
    result = service.batch_get_orders(request.requests)
    return success_response(result)


@router.get("/{platform}/{order_id}/timeline")
async def get_order_timeline(
    platform: str,
    order_id: str,
    official_run_id: str | None = None,
    service: OrderDomainService = Depends(get_order_domain_service),
):
    try:
        timeline = service.get_order_timeline(platform, order_id, official_run_id=official_run_id)
        return success_response({
            "order_id": order_id,
            "platform": platform,
            "timeline": timeline,
        })
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Order not found: {order_id}")


@router.get("/{platform}/{order_id}/raw-links")
async def get_order_raw_links(
    platform: str,
    order_id: str,
    official_run_id: str | None = None,
):
    official_sim_link = f"/official-sim/raw/orders/{order_id}?platform={platform}"
    if official_run_id:
        official_sim_link = f"{official_sim_link}&run_id={official_run_id}"
    return success_response({
        "order_id": order_id,
        "platform": platform,
        "raw_links": {
            "official_sim": official_sim_link,
            "mock": f"/mock/{platform}/orders/{order_id}",
        },
    })
