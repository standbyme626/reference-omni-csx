from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.response import success_response
from app.services.compat_data import (
    build_customer_profile,
    create_customer_tag,
    delete_customer_tag,
    list_customer_tags,
)


router = APIRouter()


class CustomerTagCreateRequest(BaseModel):
    customer_id: int
    tag_type: str
    tag_value: str


@router.get("/customers/{customer_id}/profile")
async def get_customer_profile(customer_id: int):
    return success_response(build_customer_profile(customer_id))


@router.get("/customers/{customer_id}/tags")
async def get_customer_tags(customer_id: int):
    tags = list_customer_tags(customer_id)
    return success_response({"items": tags, "total": len(tags)})


@router.post("/tags")
async def create_tag(request: CustomerTagCreateRequest):
    return success_response(create_customer_tag(request.customer_id, request.tag_type, request.tag_value))


@router.delete("/tags/{tag_id}")
async def delete_tag(tag_id: int):
    if not delete_customer_tag(tag_id):
        raise HTTPException(status_code=404, detail=f"Tag not found: {tag_id}")
    return success_response({"success": True})
