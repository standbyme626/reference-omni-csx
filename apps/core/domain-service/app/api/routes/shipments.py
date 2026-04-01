from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from pydantic import BaseModel

from app.core.response import success_response
from app.adapters.registry import PlatformRegistry
from app.services.platform_gateway_service import PlatformGatewayService
from app.services.shipment_domain_service import ShipmentDomainService

router = APIRouter()


class BatchGetShipmentsRequest(BaseModel):
    requests: List[Dict[str, str]]


def get_shipment_service() -> ShipmentDomainService:
    registry = PlatformRegistry()
    gateway = PlatformGatewayService(registry)
    return ShipmentDomainService(gateway)


@router.get("/{platform}/{order_id}")
async def get_shipment(
    platform: str,
    order_id: str,
):
    try:
        service = get_shipment_service()
        shipment = service.get_shipment(platform, order_id)
        return success_response({"shipment": shipment})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Shipment not found for order: {order_id}")


@router.post("/batch-get")
async def batch_get_shipments(request: BatchGetShipmentsRequest):
    service = get_shipment_service()
    result = service.batch_get_shipments(request.requests)
    return success_response(result)


@router.get("/{platform}/{order_id}/nodes")
async def get_shipment_nodes(
    platform: str,
    order_id: str,
):
    try:
        service = get_shipment_service()
        nodes = service.get_shipment_nodes(platform, order_id)
        return success_response({
            "order_id": order_id,
            "platform": platform,
            "nodes": nodes,
        })
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Shipment not found for order: {order_id}")
