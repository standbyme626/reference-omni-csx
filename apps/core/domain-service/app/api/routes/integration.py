from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
from pydantic import BaseModel

from app.core.response import success_response
from app.dependencies import get_integration_service
from app.services.integration_service import IntegrationService


router = APIRouter()


class InventoryResponse(BaseModel):
    product_id: str
    sku_id: Optional[str] = None
    quantity: int = 0
    reserved_quantity: int = 0
    available_quantity: int = 0
    warehouse: Optional[str] = None
    location: Optional[str] = None
    updated_at: Optional[str] = None


class OrderAuditResponse(BaseModel):
    order_id: str
    audit_status: str
    audit_notes: Optional[str] = None
    audited_by: Optional[str] = None
    audited_at: Optional[str] = None


class OrderExceptionResponse(BaseModel):
    exception_id: str
    order_id: str
    exception_type: str
    severity: str
    description: str
    status: str
    created_at: Optional[str] = None
    resolved_at: Optional[str] = None


class FulfillmentResponse(BaseModel):
    order_id: str
    status: str
    warehouse: Optional[str] = None
    picking_id: Optional[str] = None
    scheduled_date: Optional[str] = None
    actual_date: Optional[str] = None


@router.get("/inventory")
async def get_inventory(
    product_id: Optional[str] = Query(None, description="Product ID to query"),
    warehouse: Optional[str] = Query(None, description="Warehouse filter"),
    service: IntegrationService = Depends(get_integration_service),
):
    try:
        result = service.get_inventory(product_id, warehouse)
        return success_response({
            "inventories": result,
            "total": len(result),
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/order-audits")
async def get_order_audits(
    order_id: Optional[str] = Query(None, description="Order ID to query"),
    platform: Optional[str] = Query(None, description="Platform key for external order mapping"),
    service: IntegrationService = Depends(get_integration_service),
):
    try:
        result = service.get_order_audits(order_id, platform=platform)
        return success_response({
            "audits": result,
            "total": len(result),
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/order-exceptions")
async def get_order_exceptions(
    order_id: Optional[str] = Query(None, description="Order ID to query"),
    status: Optional[str] = Query(None, description="Filter by status: open/resolved"),
    service: IntegrationService = Depends(get_integration_service),
):
    try:
        result = service.get_order_exceptions(order_id, status)
        return success_response({
            "exceptions": result,
            "total": len(result),
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/fulfillment")
async def get_fulfillment(
    order_id: Optional[str] = Query(None, description="Order ID to query"),
    platform: Optional[str] = Query(None, description="Platform key for external order mapping"),
    service: IntegrationService = Depends(get_integration_service),
):
    try:
        result = service.get_fulfillment(order_id, platform=platform)
        return success_response({
            "fulfillments": result,
            "total": len(result),
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
