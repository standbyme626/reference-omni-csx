from fastapi import APIRouter, Depends
from typing import List, Dict
from pydantic import BaseModel

from app.core.response import success_response
from app.dependencies import get_order_service
from app.services.order_service import OrderService

router = APIRouter()


class BatchGetOrdersRequest(BaseModel):
    requests: List[Dict[str, str]]


@router.get("/{platform}/{order_id}")
async def get_order(
    platform: str, order_id: str, official_run_id: str | None = None,
    service: OrderService = Depends(get_order_service),
):
    order = service.get_order(platform, order_id, official_run_id=official_run_id)
    return success_response({"order": order})


@router.post("/batch-get")
async def batch_get_orders(
    request: BatchGetOrdersRequest,
    service: OrderService = Depends(get_order_service),
):
    result = service.batch_get_orders(request.requests)
    return success_response(result)


@router.get("/{platform}/{order_id}/timeline")
async def get_order_timeline(
    platform: str, order_id: str, official_run_id: str | None = None,
    service: OrderService = Depends(get_order_service),
):
    timeline = service.get_order_timeline(platform, order_id, official_run_id=official_run_id)
    return success_response({"order_id": order_id, "platform": platform, "timeline": timeline})


@router.get("/{platform}/{order_id}/raw-links")
async def get_order_raw_links(platform: str, order_id: str, official_run_id: str | None = None):
    official_sim_link = f"/official-sim/raw/orders/{order_id}?platform={platform}"
    if official_run_id:
        official_sim_link = f"{official_sim_link}&run_id={official_run_id}"
    return success_response({
        "order_id": order_id, "platform": platform,
        "raw_links": {"official_sim": official_sim_link, "mock": f"/mock/{platform}/orders/{order_id}"},
    })
