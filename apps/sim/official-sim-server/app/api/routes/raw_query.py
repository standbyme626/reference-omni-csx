from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

from providers.utils.fixture_loader import FixtureLoader

router = APIRouter()


class RawQueryResponse(BaseModel):
    code: str = "0"
    message: str = "success"
    data: Dict[str, Any]
    source: str = "fixture"


@router.get("/orders/{order_id}")
async def raw_get_order(
    order_id: str,
    platform: str = Query(..., description="Platform: taobao, douyin_shop, jd, xhs, kuaishou, wecom_kf"),
):
    try:
        order_data = FixtureLoader.get_order(platform, order_id)
        if order_data:
            return RawQueryResponse(
                data={"order": order_data, "order_id": order_id},
                source="fixture"
            )
        
        for uid in FixtureLoader.list_users(platform):
            try:
                order_data = FixtureLoader.get_user_order(platform, uid, order_id)
                if order_data:
                    return RawQueryResponse(
                        data={"order": order_data, "order_id": order_id},
                        source="fixture"
                    )
            except FileNotFoundError:
                continue
        
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")


@router.get("/shipments/{order_id}")
async def raw_get_shipment(
    order_id: str,
    platform: str = Query(..., description="Platform: taobao, douyin_shop, jd, xhs, kuaishou"),
):
    try:
        shipment_data = FixtureLoader.get_shipment(platform, order_id)
        if shipment_data:
            return RawQueryResponse(
                data={"shipment": shipment_data, "order_id": order_id},
                source="fixture"
            )
        raise HTTPException(status_code=404, detail=f"Shipment not found for order {order_id}")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Shipment not found for order {order_id}")


@router.get("/after-sales/{after_sale_id}")
async def raw_get_after_sale(
    after_sale_id: str,
    platform: str = Query(..., description="Platform: taobao, douyin_shop, jd, xhs, kuaishou"),
):
    try:
        refund_data = FixtureLoader.get_refund(platform, after_sale_id)
        if refund_data:
            return RawQueryResponse(
                data={"after_sale": refund_data, "after_sale_id": after_sale_id},
                source="fixture"
            )
        raise HTTPException(status_code=404, detail=f"After-sale {after_sale_id} not found")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"After-sale {after_sale_id} not found")


@router.get("/conversations/{conversation_id}")
async def raw_get_conversation(
    conversation_id: str,
    platform: str = Query(..., description="Platform: wecom_kf"),
):
    return RawQueryResponse(
        data={
            "conversation_id": conversation_id,
            "platform": platform,
            "message": "Use /mock/wecom-kf/messages/sync for conversation data",
        },
        source="fixture"
    )


@router.get("/users")
async def raw_list_users(
    platform: str = Query(..., description="Platform"),
):
    user_ids = FixtureLoader.list_users(platform)
    users = []
    for uid in user_ids:
        try:
            user_data = FixtureLoader.load_user(platform, uid)
            users.append({
                "user_id": user_data.get("user_id"),
                "platform": user_data.get("platform"),
                "name": user_data.get("name"),
            })
        except FileNotFoundError:
            continue
    return RawQueryResponse(
        data={"users": users, "total": len(users)},
        source="fixture"
    )
