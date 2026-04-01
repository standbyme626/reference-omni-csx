import importlib
import os

import httpx
from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/api", tags=["context"])

PROVIDER_MAP = {}

# Platform -> (mock_module, mock_cls, real_module, real_cls, env_mode, env_base_url)
_PLATFORM_ENV_BASE = {
    "jd": "JD",
    "douyin_shop": "DOUYIN",
    "wecom_kf": "WECOM",
    "taobao": "TAOBAO",
    "xhs": "XHS",
    "kuaishou": "KUAISHOU",
}

PLATFORM_CONFIG = {
    "jd": (
        "providers.jd.mock.provider",
        "JdMockProvider",
        "providers.jd.real.provider",
        "JdRealProvider",
        "JD_PROVIDER_MODE",
        "JD_MOCK_BASE_URL",
    ),
    "douyin_shop": (
        "providers.douyin_shop.mock.provider",
        "DouyinShopMockProvider",
        "providers.douyin_shop.real.provider",
        "DouyinShopRealProvider",
        "DOUYIN_PROVIDER_MODE",
        "DOUYIN_MOCK_BASE_URL",
    ),
    "wecom_kf": (
        "providers.wecom_kf.mock.provider",
        "WecomKfMockProvider",
        "providers.wecom_kf.real.provider",
        "WecomKfRealProvider",
        "WECOM_PROVIDER_MODE",
        "WECOM_MOCK_BASE_URL",
    ),
    "taobao": (
        "providers.taobao.mock.provider",
        "TaobaoMockProvider",
        "providers.taobao.real.provider",
        "TaobaoRealProvider",
        "TAOBAO_PROVIDER_MODE",
        "TAOBAO_MOCK_BASE_URL",
    ),
    "xhs": (
        "providers.xhs.mock.provider",
        "XhsMockProvider",
        "providers.xhs.real.provider",
        "XhsRealProvider",
        "XHS_PROVIDER_MODE",
        "XHS_MOCK_BASE_URL",
    ),
    "kuaishou": (
        "providers.kuaishou.mock.provider",
        "KuaishouMockProvider",
        "providers.kuaishou.real.provider",
        "KuaishouRealProvider",
        "KUAISHOU_PROVIDER_MODE",
        "KUAISHOU_MOCK_BASE_URL",
    ),
}


def _get_provider(platform: str):
    if platform not in PLATFORM_CONFIG:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown platform: {platform}",
        )

    mock_mod, mock_cls, real_mod, real_cls, env_name, env_url = PLATFORM_CONFIG[
        platform
    ]
    mode = os.getenv(env_name, "mock").lower()

    if mode == "real":
        cache_key = f"{platform}_real"
        if cache_key not in PROVIDER_MAP:
            mod = importlib.import_module(real_mod)
            PROVIDER_MAP[cache_key] = getattr(mod, real_cls)()
        return PROVIDER_MAP[cache_key]

    # default: mock
    if platform not in PROVIDER_MAP:
        mod = importlib.import_module(mock_mod)
        base_url = os.getenv(env_url, "http://localhost:8200")
        PROVIDER_MAP[platform] = getattr(mod, mock_cls)(base_url=base_url)
    return PROVIDER_MAP[platform]


def _safe_provider_call(provider, method: str, *args):
    """Call a provider method with error handling, converting exceptions to HTTP errors."""
    try:
        return getattr(provider, method)(*args)
    except httpx.ConnectError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Provider connection failed: {e}",
        ) from e
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Provider returned error {e.response.status_code}",
        ) from e
    except NotImplementedError as e:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=str(e),
        ) from e
    except AttributeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Platform {method} not supported: {e}",
        ) from e


@router.get("/orders/{platform}/{order_id}")
def get_order(platform: str, order_id: str) -> dict:
    provider = _get_provider(platform)
    order_dto = _safe_provider_call(provider, "get_order", order_id)
    return {
        "platform": order_dto.platform,
        "order_id": order_dto.order_id,
        "status": order_dto.status,
        "status_name": order_dto.status_name,
        "create_time": order_dto.create_time,
        "pay_time": order_dto.pay_time,
        "total_amount": order_dto.total_amount,
        "freight_amount": order_dto.freight_amount,
        "discount_amount": order_dto.discount_amount,
        "payment_amount": order_dto.payment_amount,
        "buyer_nick": order_dto.buyer_nick,
        "buyer_phone": order_dto.buyer_phone,
        "receiver_name": order_dto.receiver_name,
        "receiver_phone": order_dto.receiver_phone,
        "receiver_address": {
            "province": order_dto.receiver_address.province
            if order_dto.receiver_address
            else None,
            "city": order_dto.receiver_address.city
            if order_dto.receiver_address
            else None,
            "district": order_dto.receiver_address.district
            if order_dto.receiver_address
            else None,
            "detail": order_dto.receiver_address.detail
            if order_dto.receiver_address
            else None,
        }
        if order_dto.receiver_address
        else None,
        "items": [
            {
                "sku_id": item.sku_id,
                "sku_name": item.sku_name,
                "quantity": item.quantity,
                "price": item.price,
                "sub_total": item.sub_total,
            }
            for item in order_dto.items
        ],
    }


@router.get("/shipments/{platform}/{order_id}")
def get_shipment(platform: str, order_id: str) -> dict:
    provider = _get_provider(platform)
    shipment_dto = _safe_provider_call(provider, "get_shipment", order_id)
    return {
        "platform": shipment_dto.platform,
        "order_id": shipment_dto.order_id,
        "shipments": [
            {
                "shipment_id": ship.shipment_id,
                "express_company": ship.express_company,
                "express_no": ship.express_no,
                "status": ship.status,
                "status_name": ship.status_name,
                "create_time": ship.create_time,
                "estimated_arrival": ship.estimated_arrival,
                "trace": [
                    {"time": t.time, "message": t.message, "location": t.location}
                    for t in ship.trace
                ],
            }
            for ship in shipment_dto.shipments
        ],
    }


@router.get("/after-sales/{platform}/{after_sale_id}")
def get_after_sale(platform: str, after_sale_id: str) -> dict:
    provider = _get_provider(platform)
    after_sale_dto = _safe_provider_call(provider, "get_after_sale", after_sale_id)
    return {
        "platform": after_sale_dto.platform,
        "after_sale_id": after_sale_dto.after_sale_id,
        "order_id": after_sale_dto.order_id,
        "type": after_sale_dto.type,
        "type_name": after_sale_dto.type_name,
        "status": after_sale_dto.status,
        "status_name": after_sale_dto.status_name,
        "apply_time": after_sale_dto.apply_time,
        "handle_time": after_sale_dto.handle_time,
        "apply_amount": after_sale_dto.apply_amount,
        "approve_amount": after_sale_dto.approve_amount,
        "reason": after_sale_dto.reason,
        "reason_detail": after_sale_dto.reason_detail,
    }
