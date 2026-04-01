from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from app.core.response import success_response, error_response
from app.core.errors import ErrorCode
from app.adapters.registry import PlatformRegistry
from app.services.platform_gateway_service import PlatformGatewayService
from app.services.order_domain_service import OrderDomainService

router = APIRouter()


class BatchGetOrdersRequest(BaseModel):
    requests: List[Dict[str, str]]


def get_order_service() -> OrderDomainService:
    registry = PlatformRegistry()
    gateway = PlatformGatewayService(registry)
    return OrderDomainService(gateway, registry)


@router.get("/{platform}/{order_id}")
async def get_order(
    platform: str,
    order_id: str,
):
    try:
        service = get_order_service()
        order = service.get_order(platform, order_id)
        return success_response({"order": order})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Order not found: {order_id}")


@router.post("/batch-get")
async def batch_get_orders(request: BatchGetOrdersRequest):
    service = get_order_service()
    result = service.batch_get_orders(request.requests)
    return success_response(result)


@router.get("/{platform}/{order_id}/timeline")
async def get_order_timeline(
    platform: str,
    order_id: str,
):
    try:
        service = get_order_service()
        timeline = service.get_order_timeline(platform, order_id)
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
):
    return success_response({
        "order_id": order_id,
        "platform": platform,
        "raw_links": {
            "official_sim": f"/official-sim/raw/orders/{order_id}?platform={platform}",
            "mock": f"/mock/{platform}/orders/{order_id}",
        },
    })
