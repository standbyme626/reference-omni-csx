from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FIXTURES_ROOT = REPO_ROOT / "apps" / "sim" / "official-sim-server" / "fixtures"
SUPPORTED_ORDER_PLATFORMS = ("taobao", "douyin_shop", "jd", "xhs", "kuaishou")


def _extract_order_id_from_fixture_payload(payload: Mapping[str, Any]) -> str | None:
    response = payload.get("response", payload)
    if not isinstance(response, Mapping):
        return None

    trade = response.get("trade")
    if isinstance(trade, Mapping):
        order_id = trade.get("tid") or trade.get("order_id") or trade.get("orderId")
        return str(order_id) if order_id not in (None, "") else None

    order = response.get("order")
    if isinstance(order, Mapping):
        order_id = order.get("order_id") or order.get("orderId") or order.get("tid")
        return str(order_id) if order_id not in (None, "") else None

    jd_order = response.get("jingdong_order_search_responce")
    if isinstance(jd_order, Mapping):
        order_id = jd_order.get("orderId")
        return str(order_id) if order_id not in (None, "") else None

    order_id = response.get("order_id") or response.get("orderId") or response.get("tid")
    return str(order_id) if order_id not in (None, "") else None


def _collect_platform_user_orders(fixtures_root: Path) -> List[Dict[str, str]]:
    collected: Dict[str, Dict[str, str]] = {}

    for platform in SUPPORTED_ORDER_PLATFORMS:
        users_dir = fixtures_root / platform / "users"
        if not users_dir.exists():
            continue

        for path in sorted(users_dir.glob("*.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue

            for order in payload.get("orders", []):
                platform_order_id = str(
                    order.get("external_order_id")
                    or order.get("order_id")
                    or ""
                ).strip()
                if not platform_order_id:
                    continue

                key = f"{platform}:{platform_order_id}"
                if key in collected:
                    continue

                collected[key] = {
                    "platform": platform,
                    "platform_order_id": platform_order_id,
                    "fixture_path": str(path.relative_to(REPO_ROOT)),
                }

    return [collected[key] for key in sorted(collected)]


def collect_platform_fixture_orders(fixtures_root: Path = DEFAULT_FIXTURES_ROOT) -> List[Dict[str, str]]:
    collected: Dict[str, Dict[str, str]] = {}

    for item in _collect_platform_user_orders(fixtures_root):
        key = f"{item['platform']}:{item['platform_order_id']}"
        collected[key] = item

    for platform in SUPPORTED_ORDER_PLATFORMS:
        success_dir = fixtures_root / platform / "success"
        if not success_dir.exists():
            continue

        for path in sorted(success_dir.glob("*.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue

            order_id = _extract_order_id_from_fixture_payload(payload)
            if not order_id:
                continue

            key = f"{platform}:{order_id}"
            if key in collected:
                continue

            collected[key] = {
                "platform": platform,
                "platform_order_id": order_id,
                "fixture_path": str(path.relative_to(REPO_ROOT)),
            }

    return [collected[key] for key in sorted(collected)]


def build_platform_order_link_seed(
    sale_order_rows: Sequence[Mapping[str, Any]],
    fixture_orders: Iterable[Mapping[str, Any]],
) -> Dict[str, Any]:
    normalized_sale_orders = [
        {
            "id": str(row.get("id", "")).strip(),
            "name": str(row.get("name", "")).strip(),
        }
        for row in sale_order_rows
        if str(row.get("id", "")).strip() and str(row.get("name", "")).strip()
    ]
    normalized_fixture_orders = [
        {
            "platform": str(item.get("platform", "")).strip(),
            "platform_order_id": str(item.get("platform_order_id", "")).strip(),
            "fixture_path": str(item.get("fixture_path", "")).strip(),
        }
        for item in fixture_orders
        if str(item.get("platform", "")).strip() and str(item.get("platform_order_id", "")).strip()
    ]

    links: Dict[str, Dict[str, Any]] = {}
    for index, fixture_order in enumerate(normalized_fixture_orders):
        if index >= len(normalized_sale_orders):
            break
        sale_order = normalized_sale_orders[index]
        key = f"{fixture_order['platform']}:{fixture_order['platform_order_id']}"
        links[key] = {
            "platform": fixture_order["platform"],
            "platform_order_id": fixture_order["platform_order_id"],
            "sale_order_external_id": sale_order["id"],
            "sale_order_name": sale_order["name"],
            "fixture_path": fixture_order["fixture_path"],
            "link_strategy": "seed_fixture_to_sale_order",
        }

    return {"links": links}


def build_runtime_platform_order_links(
    seed_payload: Mapping[str, Any],
    created_orders_by_external_id: Mapping[str, Mapping[str, Any]],
) -> Dict[str, Any]:
    links: Dict[str, Dict[str, Any]] = {}
    raw_links = seed_payload.get("links", {}) if isinstance(seed_payload, Mapping) else {}
    if not isinstance(raw_links, Mapping):
        return {"links": {}}

    for key, seed in raw_links.items():
        if not isinstance(seed, Mapping):
            continue
        sale_order_external_id = str(seed.get("sale_order_external_id", "")).strip()
        if not sale_order_external_id:
            continue
        created_order = created_orders_by_external_id.get(sale_order_external_id)
        if not isinstance(created_order, Mapping):
            continue

        odoo_order_id = created_order.get("odoo_order_id")
        odoo_order_name = created_order.get("odoo_order_name")
        if odoo_order_id in (None, "") or odoo_order_name in (None, ""):
            continue

        links[str(key)] = {
            "platform": str(seed.get("platform", "")).strip(),
            "platform_order_id": str(seed.get("platform_order_id", "")).strip(),
            "odoo_order_id": str(odoo_order_id),
            "odoo_order_name": str(odoo_order_name),
            "odoo_picking_id": created_order.get("odoo_picking_id"),
            "odoo_picking_name": created_order.get("odoo_picking_name"),
            "odoo_picking_origin": created_order.get("odoo_picking_origin"),
            "sale_order_external_id": sale_order_external_id,
            "fixture_path": seed.get("fixture_path"),
            "link_strategy": "seed_imported",
        }

    return {"links": links}


def build_created_orders_from_existing_live_batch(
    sale_order_rows: Sequence[Mapping[str, Any]],
    live_sale_orders: Sequence[Mapping[str, Any]],
    limit: int,
) -> Dict[str, Dict[str, Any]]:
    if limit <= 0:
        return {}

    normalized_sale_orders = [
        {
            "id": str(row.get("id", "")).strip(),
            "name": str(row.get("name", "")).strip(),
        }
        for row in sale_order_rows
        if str(row.get("id", "")).strip() and str(row.get("name", "")).strip()
    ]
    normalized_live_orders = [
        {
            "id": str(row.get("id", "")).strip(),
            "name": str(row.get("name", "")).strip(),
            "client_order_ref": row.get("client_order_ref"),
        }
        for row in live_sale_orders
        if str(row.get("id", "")).strip() and str(row.get("name", "")).strip()
    ]

    if len(normalized_sale_orders) < limit:
        raise ValueError("Not enough staged sale orders to build existing live order mapping")
    if len(normalized_live_orders) < limit:
        raise ValueError("Not enough live sale orders to build existing live order mapping")

    created_orders: Dict[str, Dict[str, Any]] = {}
    for sale_order, live_order in zip(
        normalized_sale_orders[:limit],
        normalized_live_orders[-limit:],
    ):
        created_orders[sale_order["id"]] = {
            "odoo_order_id": live_order["id"],
            "odoo_order_name": live_order["name"],
            "client_order_ref": live_order.get("client_order_ref"),
        }

    return created_orders


def build_seed_client_order_ref_updates(
    seed_payload: Mapping[str, Any],
    created_orders_by_external_id: Mapping[str, Mapping[str, Any]],
) -> List[Dict[str, str]]:
    updates: List[Dict[str, str]] = []
    raw_links = seed_payload.get("links", {}) if isinstance(seed_payload, Mapping) else {}
    if not isinstance(raw_links, Mapping):
        return updates

    for key in sorted(raw_links):
        seed = raw_links.get(key)
        if not isinstance(seed, Mapping):
            continue

        sale_order_external_id = str(seed.get("sale_order_external_id", "")).strip()
        platform_order_id = str(seed.get("platform_order_id", "")).strip()
        platform = str(seed.get("platform", "")).strip()
        if not sale_order_external_id or not platform_order_id or not platform:
            continue

        created_order = created_orders_by_external_id.get(sale_order_external_id)
        if not isinstance(created_order, Mapping):
            continue

        odoo_order_id = str(created_order.get("odoo_order_id", "")).strip()
        odoo_order_name = str(created_order.get("odoo_order_name", "")).strip()
        if not odoo_order_id or not odoo_order_name:
            continue

        updates.append(
            {
                "platform": platform,
                "platform_order_id": platform_order_id,
                "sale_order_external_id": sale_order_external_id,
                "odoo_order_id": odoo_order_id,
                "odoo_order_name": odoo_order_name,
            }
        )

    return updates


def merge_link_payload(existing: Mapping[str, Any] | None, incoming: Mapping[str, Any] | None) -> Dict[str, Any]:
    merged: Dict[str, Any] = {"links": {}}
    incoming_platform_order_ids = set()

    for payload in (existing, incoming):
        if not isinstance(payload, Mapping):
            continue
        links = payload.get("links", {})
        if not isinstance(links, Mapping):
            continue
        for key, value in links.items():
            if isinstance(value, Mapping):
                merged["links"][str(key)] = dict(value)
                platform = str(value.get("platform", "")).strip()
                platform_order_id = str(value.get("platform_order_id", "")).strip()
                if payload is incoming and platform and platform != "unknown" and platform_order_id:
                    incoming_platform_order_ids.add(platform_order_id)

    for platform_order_id in incoming_platform_order_ids:
        merged["links"].pop(f"unknown:{platform_order_id}", None)

    return merged
