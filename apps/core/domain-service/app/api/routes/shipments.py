from fastapi import APIRouter, Depends
from typing import List, Dict
from pydantic import BaseModel

from app.core.response import success_response
from app.dependencies import get_shipment_service
from app.services.shipment_service import ShipmentService

router = APIRouter()


class BatchGetShipmentsRequest(BaseModel):
    requests: List[Dict[str, str]]


@router.get("/{platform}/{order_id}")
async def get_shipment(
    platform: str, order_id: str, official_run_id: str | None = None,
    service: ShipmentService = Depends(get_shipment_service),
):
    shipment = service.get_shipment(platform, order_id, official_run_id=official_run_id)
    return success_response({"shipment": shipment})


@router.post("/batch-get")
async def batch_get_shipments(
    request: BatchGetShipmentsRequest,
    service: ShipmentService = Depends(get_shipment_service),
):
    result = service.batch_get_shipments(request.requests)
    return success_response(result)


@router.get("/{platform}/{order_id}/nodes")
async def get_shipment_nodes(
    platform: str, order_id: str, official_run_id: str | None = None,
    service: ShipmentService = Depends(get_shipment_service),
):
    nodes = service.get_shipment_nodes(platform, order_id, official_run_id=official_run_id)
    return success_response({"order_id": order_id, "platform": platform, "nodes": nodes})
