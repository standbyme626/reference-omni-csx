"""
Mock compatibility routes for Omni-CSX integration.

Exposes /mock/{platform}/... endpoints that match the existing
mock-platform-server contract, so Omni-CSX providers can point
to official-sim-server without code changes.
"""

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, status

router = APIRouter()

# Platform name normalization
PLATFORM_ALIAS = {
    "douyin-shop": "douyin_shop",
    "douyin_shop": "douyin_shop",
    "wecom-kf": "wecom_kf",
    "wecom_kf": "wecom_kf",
    "taobao": "taobao",
    "jd": "jd",
    "xhs": "xhs",
    "kuaishou": "kuaishou",
}

# Fixture name mapping: Omni-CSX expected names → platform-sim success fixtures
FIXTURE_ALIAS: Dict[str, Dict[str, str]] = {
    "jd": {
        "order_sample.json": "order_paid.json",
        "shipment_sample.json": "order_shipped.json",
        "after_sale_sample.json": "refund_applied.json",
    },
    "douyin_shop": {
        "order_sample.json": "order_paid.json",
        "refund_sample.json": "refund_applied.json",
        "product_sample.json": "order_paid.json",
    },
    "wecom_kf": {
        "message_sample.json": "conversation_in_session.json",
        "service_state_sample.json": "conversation_pending.json",
        "event_message_sample.json": "conversation_closed.json",
    },
    "taobao": {
        "trade_wait_ship.json": "trade_wait_ship.json",
        "trade_shipped.json": "trade_shipped.json",
        "refund_requested.json": "refund_requested.json",
    },
    "xhs": {
        "order_paid.json": "order_paid.json",
        "order_delivering.json": "order_delivering.json",
        "refund_requested.json": "refund_applied.json",
    },
    "kuaishou": {
        "order_paid.json": "order_paid.json",
        "order_delivering.json": "order_delivered.json",
        "refund_requested.json": "refund_applied.json",
    },
}

# Project absolute paths (not relative to __file__)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_REPO_ROOT = _PROJECT_ROOT.parent.parent.parent
_OMNI_FIXTURE_CANDIDATES = [
    _REPO_ROOT / "multiplatform_mock_openapi_zh" / "apps" / "mock-platform-server" / "app" / "data",
    _REPO_ROOT / "reference" / "omni-csx-v35" / "apps" / "mock-platform-server" / "app" / "data",
]
_OMNI_FIXTURE_BASE = next((p for p in _OMNI_FIXTURE_CANDIDATES if p.exists()), _OMNI_FIXTURE_CANDIDATES[0])
_SIM_FIXTURE_BASE = _PROJECT_ROOT / "fixtures"


def _fixtures_by_prefix(platform: str, prefix: str) -> List[str]:
    """List available success fixtures matching a prefix for a platform."""
    base = _SIM_FIXTURE_BASE / platform / "success"
    return sorted(p.name for p in base.glob(f"{prefix}_*.json"))


def _select_fixture_by_id(platform: str, prefix: str, entity_id: str) -> str:
    """Deterministically select a fixture variant based on entity_id hash."""
    fixtures = _fixtures_by_prefix(platform, prefix)
    assert fixtures, f"No fixtures for {platform}/{prefix}_*"
    idx = int(hashlib.md5(entity_id.encode()).hexdigest(), 16) % len(fixtures)
    return fixtures[idx]


def _load_fixture_file(platform: str, filename: str, entity_id: str = None) -> dict:
    """Load a raw JSON fixture from mock data.

    If entity_id is given, select fixture variant deterministically from id hash.
    Otherwise fall back to default alias mapping.
    """
    # 1. Try Omni-CSX fixtures first (jd, douyin_shop, wecom_kf only)
    omni_base = _OMNI_FIXTURE_BASE / platform
    omni_path = omni_base / filename
    if omni_path.exists():
        with open(omni_path, "r", encoding="utf-8") as f:
            return json.load(f)

    # 2. Determine which fixture to load
    prefix = filename.rsplit(".", 1)[0].split("_")[0]
    sim_base = _SIM_FIXTURE_BASE / platform / "success"

    if entity_id:
        # Use hash-based selection for different states
        actual = _select_fixture_by_id(platform, prefix, entity_id)
    else:
        # Default: use alias mapping or first match
        aliases = FIXTURE_ALIAS.get(platform, {})
        actual = aliases.get(filename, filename)
        if not (sim_base / actual).exists():
            for p in sim_base.glob(f"{prefix}_*.json"):
                actual = p.name
                break

    full = sim_base / actual
    if full.exists():
        with open(full, "r", encoding="utf-8") as f:
            return json.load(f)

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Fixture not found: {platform}/{filename}",
    )


def _inject_nested(data: dict, entity_id: str) -> dict:
    """Replace placeholder IDs with the requested entity_id at all nesting levels."""
    for k in [
        "orderId",
        "order_id",
        "tid",
        "trade_id",
        "afterSaleId",
        "after_sale_id",
        "refundId",
        "refund_id",
        "oid",
    ]:
        if k in data:
            data[k] = entity_id

    resp = data.get("response", {})
    if not isinstance(resp, dict):
        return data

    for section_key in ["trade", "order", "refund"]:
        section = resp.get(section_key, {})
        if not isinstance(section, dict):
            continue
        for k in [
            "orderId",
            "order_id",
            "tid",
            "trade_id",
            "afterSaleId",
            "after_sale_id",
            "refundId",
            "refund_id",
            "oid",
            "id",
        ]:
            if k in section:
                section[k] = entity_id

        for items_key, child_key in [("orders", "order"), ("productItems", None)]:
            items = (
                section.get(items_key, section)
                if items_key == "productItems"
                else section.get(items_key, {})
            )
            child_list = items.get(child_key, []) if isinstance(items, dict) else items
            for child in child_list:
                if not isinstance(child, dict):
                    continue
                for k in ["oid", "orderId", "order_id", "refund_id"]:
                    if k in child:
                        child[k] = entity_id

    return data


# ---------- JD routes ----------

jd_router = APIRouter(prefix="/mock/jd", tags=["mock-jd"])


@jd_router.get("/orders/{order_id}")
def jd_get_order(order_id: str) -> dict:
    data = _load_fixture_file("jd", "order_sample.json")
    return _inject_nested(data, order_id)


@jd_router.get("/shipments/{order_id}")
def jd_get_shipment(order_id: str) -> dict:
    data = _load_fixture_file("jd", "shipment_sample.json")
    return _inject_nested(data, order_id)


@jd_router.get("/after-sales/{after_sale_id}")
def jd_get_after_sale(after_sale_id: str) -> dict:
    data = _load_fixture_file("jd", "after_sale_sample.json")
    return _inject_nested(data, after_sale_id)


@jd_router.post("/oauth/token")
def jd_oauth_token() -> dict:
    return _load_fixture_file("jd", "token_response.json")


# ---------- Douyin Shop routes ----------

douyin_router = APIRouter(prefix="/mock/douyin-shop", tags=["mock-douyin-shop"])


@douyin_router.get("/orders/{order_id}")
def dy_get_order(order_id: str) -> dict:
    data = _load_fixture_file("douyin_shop", "order_sample.json")
    return _inject_nested(data, order_id)


@douyin_router.get("/refunds/{after_sale_id}")
def dy_get_refund(after_sale_id: str) -> dict:
    data = _load_fixture_file("douyin_shop", "refund_sample.json")
    return _inject_nested(data, after_sale_id)


@douyin_router.get("/products/{product_id}")
def dy_get_product(product_id: str) -> dict:
    data = _load_fixture_file("douyin_shop", "product_sample.json")
    data["productId"] = product_id
    return data


@douyin_router.post("/auth/token")
def dy_oauth_token() -> dict:
    return _load_fixture_file("douyin_shop", "token_response.json")


# ---------- WeCom KF routes ----------

wecom_router = APIRouter(prefix="/mock/wecom-kf", tags=["mock-wecom-kf"])


@wecom_router.post("/token")
def wecom_token() -> dict:
    return _load_fixture_file("wecom_kf", "token_response.json")


@wecom_router.post("/messages/sync")
def wecom_messages_sync() -> dict:
    return _load_fixture_file("wecom_kf", "message_sample.json")


@wecom_router.post("/service-state/trans")
def wecom_service_state() -> dict:
    return _load_fixture_file("wecom_kf", "service_state_sample.json")


@wecom_router.post("/event-message/send")
def wecom_event_message() -> dict:
    return _load_fixture_file("wecom_kf", "event_message_sample.json")


# ---------- Taobao routes ----------

taobao_router = APIRouter(prefix="/mock/taobao", tags=["mock-taobao"])


@taobao_router.get("/orders/{order_id}")
def tb_get_order(order_id: str) -> dict:
    data = _load_fixture_file("taobao", "trade_wait_ship.json", order_id)
    return _inject_nested(data, order_id)


@taobao_router.get("/shipments/{order_id}")
def tb_get_shipment(order_id: str) -> dict:
    data = _load_fixture_file("taobao", "trade_shipped.json", order_id)
    return _inject_nested(data, order_id)


@taobao_router.get("/after-sales/{after_sale_id}")
def tb_get_after_sale(after_sale_id: str) -> dict:
    data = _load_fixture_file("taobao", "refund_requested.json", after_sale_id)
    return _inject_nested(data, after_sale_id)


@taobao_router.post("/oauth/token")
def tb_oauth_token() -> dict:
    return {"access_token": "mock_taobao_token", "expires_in": 86400}


# ---------- XHS routes ----------

xhs_router = APIRouter(prefix="/mock/xhs", tags=["mock-xhs"])


@xhs_router.get("/orders/{order_id}")
def xhs_get_order(order_id: str) -> dict:
    data = _load_fixture_file("xhs", "order_paid.json", order_id)
    return _inject_nested(data, order_id)


@xhs_router.get("/shipments/{order_id}")
def xhs_get_shipment(order_id: str) -> dict:
    data = _load_fixture_file("xhs", "order_delivering.json", order_id)
    return _inject_nested(data, order_id)


@xhs_router.get("/after-sales/{after_sale_id}")
def xhs_get_after_sale(after_sale_id: str) -> dict:
    data = _load_fixture_file("xhs", "refund_requested.json", after_sale_id)
    return _inject_nested(data, after_sale_id)


# ---------- Kuaishou routes ----------

kuaishou_router = APIRouter(prefix="/mock/kuaishou", tags=["mock-kuaishou"])


@kuaishou_router.get("/orders/{order_id}")
def ks_get_order(order_id: str) -> dict:
    data = _load_fixture_file("kuaishou", "order_paid.json", order_id)
    return _inject_nested(data, order_id)


@kuaishou_router.get("/shipments/{order_id}")
def ks_get_shipment(order_id: str) -> dict:
    data = _load_fixture_file("kuaishou", "order_delivering.json", order_id)
    return _inject_nested(data, order_id)


@kuaishou_router.get("/after-sales/{after_sale_id}")
def ks_get_after_sale(after_sale_id: str) -> dict:
    data = _load_fixture_file("kuaishou", "refund_requested.json", after_sale_id)
    return _inject_nested(data, after_sale_id)
