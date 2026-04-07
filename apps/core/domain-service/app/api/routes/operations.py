from fastapi import APIRouter

from app.core.response import success_response


router = APIRouter()


@router.get("/operation-campaigns")
async def list_operation_campaigns():
    campaigns = [
        {
            "id": "CAMP_001",
            "name": "618 大促活动",
            "type": "promotion",
            "status": "active",
            "start_time": "2026-06-01T00:00:00",
            "end_time": "2026-06-20T23:59:59",
            "target_platforms": ["taobao", "douyin_shop", "jd"],
            "description": "618 年中大促活动",
        },
        {
            "id": "CAMP_002",
            "name": "双十一预热",
            "type": "promotion",
            "status": "preparing",
            "start_time": "2026-11-01T00:00:00",
            "end_time": "2026-11-11T23:59:59",
            "target_platforms": ["taobao", "jd", "xhs"],
            "description": "双十一购物节预热活动",
        },
        {
            "id": "CAMP_003",
            "name": "新品上市推广",
            "type": "launch",
            "status": "active",
            "start_time": "2026-04-01T00:00:00",
            "end_time": "2026-04-30T23:59:59",
            "target_platforms": ["douyin_shop", "kuaishou"],
            "description": "春季新品上市推广活动",
        },
    ]
    return success_response({"items": campaigns, "total": len(campaigns)})


@router.get("/tags")
async def list_tags(
    category: str = None,
):
    tags = [
        {"id": "TAG_001", "name": "VIP 客户", "category": "customer", "color": "gold"},
        {"id": "TAG_002", "name": "新客户", "category": "customer", "color": "green"},
        {"id": "TAG_003", "name": "高价值", "category": "order", "color": "red"},
        {"id": "TAG_004", "name": "敏感商品", "category": "product", "color": "orange"},
        {"id": "TAG_005", "name": "活动用户", "category": "customer", "color": "blue"},
    ]

    filtered = tags
    if category:
        filtered = [t for t in filtered if t["category"] == category]

    return success_response({"items": filtered, "total": len(filtered)})
