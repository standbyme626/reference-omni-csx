from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from providers.utils.fixture_loader import FixtureLoader
from providers.utils.sim_identity import (
    build_canonical_after_sale_id,
    get_primary_order_id,
    iter_order_id_aliases,
    parse_canonical_after_sale_id,
)
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.platforms.douyin_shop.profile import (
    ORDER_SCENARIOS as DOUYIN_RUN_SCENARIOS,
)
from app.platforms.douyin_shop.profile import (
    DouyinOrderStatus,
    DouyinRefundStatus,
)
from app.platforms.douyin_shop.profile import (
    get_default_order_payload as douyin_order_payload,
)
from app.platforms.douyin_shop.profile import (
    get_default_refund_payload as douyin_refund_payload,
)
from app.platforms.jd.profile import (
    ORDER_SCENARIOS as JD_RUN_SCENARIOS,
)
from app.platforms.jd.profile import (
    JdOrderStatus,
    JdRefundStatus,
)
from app.platforms.jd.profile import (
    get_default_order_payload as jd_order_payload,
)
from app.platforms.jd.profile import (
    get_default_refund_payload as jd_refund_payload,
)
from app.platforms.kuaishou.profile import (
    ORDER_SCENARIOS as KUAISHOU_RUN_SCENARIOS,
)
from app.platforms.kuaishou.profile import (
    KuaishouOrderStatus,
    KuaishouRefundStatus,
)
from app.platforms.kuaishou.profile import (
    get_default_order_payload as kuaishou_order_payload,
)
from app.platforms.kuaishou.profile import (
    get_default_refund_payload as kuaishou_refund_payload,
)
from app.platforms.taobao.profile import (
    ORDER_SCENARIOS as TAOBAO_RUN_SCENARIOS,
)
from app.platforms.taobao.profile import (
    TaobaoOrderStatus,
    TaobaoRefundStatus,
)
from app.platforms.taobao.profile import (
    get_default_order_payload as taobao_order_payload,
)
from app.platforms.taobao.profile import (
    get_default_refund_payload as taobao_refund_payload,
)
from app.platforms.xhs.profile import (
    ORDER_SCENARIOS as XHS_RUN_SCENARIOS,
)
from app.platforms.xhs.profile import (
    XhsOrderStatus,
    XhsRefundStatus,
)
from app.platforms.xhs.profile import (
    get_default_order_payload as xhs_order_payload,
)
from app.platforms.xhs.profile import (
    get_default_refund_payload as xhs_refund_payload,
)
from app.repositories.artifact_repo import ArtifactRepository
from app.repositories.run_repo import RunRepository
from app.repositories.snapshot_repo import SnapshotRepository

router = APIRouter()


class RawQueryResponse(BaseModel):
    code: str = "0"
    message: str = "success"
    data: Dict[str, Any]
    source: str = "fixture"


# Scenario key mappings: order_id pattern -> fixture scenario key
ORDER_SCENARIO_MAP = {
    "taobao": {
        "wait_pay": "trade_wait_pay",
        "wait_ship": "trade_wait_ship",
        "shipped": "trade_shipped",
        "finished": "trade_finished",
        "closed": "trade_closed",
    },
    "douyin_shop": {
        "created": "order_created",
        "paid": "order_paid",
        "wait_ship": "order_wait_ship",
        "shipped": "order_shipped",
        "finished": "order_finished",
    },
    "jd": {
        "wait_pay": "order_wait_pay",
        "seller_received": "order_seller_received",
        "shipped": "order_shipped",
        "finished": "order_finished",
    },
    "xhs": {
        "created": "order_created",
        "paid": "order_paid",
        "shipped": "order_delivering",
        "finished": "order_completed",
    },
    "kuaishou": {
        "created": "order_created",
        "paid": "order_paid",
        "shipped": "order_delivered",
        "finished": "order_delivered",
    },
}

REFUND_SCENARIO_MAP = {
    "taobao": "refund_requested",
    "douyin_shop": "refund_requested",
    "jd": "refund_requested",
    "xhs": "refund_requested",
    "kuaishou": "refund_requested",
}

SHIPMENT_SCENARIO_MAP = {
    "taobao": "trade_shipped",
    "douyin_shop": "order_shipped",
    "jd": "order_shipped",
    "xhs": "order_delivering",
    "kuaishou": "order_delivered",
}

PREFERRED_ORDER_FIXTURE_KEYS = {
    "taobao": (
        "trade_shipped",
        "trade_finished",
        "trade_wait_ship",
        "trade_wait_pay",
        "trade_closed",
        "trade_closed_by_taobao",
    ),
    "douyin_shop": (
        "order_shipped",
        "order_fulfilled",
        "order_completed",
        "order_confirmed",
        "order_paid",
        "order_created",
        "order_cancelled",
        "order_cancelling",
    ),
    "jd": (
        "order_shipped",
        "order_delivering",
        "order_delivered",
        "order_finished",
        "order_paid",
        "order_wait_pay",
        "order_seller_received",
        "order_station_received",
        "order_jd_received",
        "order_wait_self_pickup",
        "order_created",
    ),
    "xhs": (
        "order_delivering",
        "order_partial_shipped",
        "order_completed",
        "order_paid",
        "order_created",
        "order_closed",
        "order_cancelled",
        "order_customs_clearing",
        "order_exchanging",
    ),
    "kuaishou": (
        "order_delivered",
        "order_confirmed",
        "order_paid",
        "order_created",
        "order_wait_pay",
        "order_cancelled",
    ),
}

PREFERRED_SHIPMENT_FIXTURE_KEYS = {
    "taobao": ("trade_shipped", "trade_finished", "trade_buyer_signed"),
    "douyin_shop": ("order_shipped", "order_fulfilled", "order_completed", "order_confirmed"),
    "jd": ("order_shipped", "order_delivering", "order_delivered", "order_finished"),
    "xhs": ("order_delivering", "order_partial_shipped", "order_completed", "order_customs_clearing"),
    "kuaishou": ("order_delivered", "order_confirmed"),
}

RUN_ORDER_SCENARIOS = {
    "taobao": TAOBAO_RUN_SCENARIOS,
    "douyin_shop": DOUYIN_RUN_SCENARIOS,
    "jd": JD_RUN_SCENARIOS,
    "xhs": XHS_RUN_SCENARIOS,
    "kuaishou": KUAISHOU_RUN_SCENARIOS,
}


def _extract_order_id(payload: Dict[str, Any]) -> Optional[str]:
    if not isinstance(payload, dict):
        return None

    if isinstance(payload.get("trade"), dict):
        trade = payload["trade"]
        order_id = trade.get("tid") or trade.get("order_id") or trade.get("orderId")
        return str(order_id) if order_id is not None else None

    if isinstance(payload.get("order"), dict):
        order = payload["order"]
        order_id = order.get("order_id") or order.get("orderId") or order.get("tid")
        return str(order_id) if order_id is not None else None

    if isinstance(payload.get("jingdong_order_search_responce"), dict):
        order = payload["jingdong_order_search_responce"]
        order_id = order.get("orderId")
        return str(order_id) if order_id is not None else None

    order_id = payload.get("order_id") or payload.get("orderId") or payload.get("tid")
    return str(order_id) if order_id is not None else None


def _get_initial_run_status(platform: str, scenario_name: Optional[str]) -> Optional[str]:
    scenarios = RUN_ORDER_SCENARIOS.get(platform, {})
    scenario = scenarios.get(scenario_name or "")
    if not isinstance(scenario, dict):
        return None

    initial_status = scenario.get("initial_order_status")
    if hasattr(initial_status, "value"):
        return str(initial_status.value)
    if initial_status is None:
        return None
    return str(initial_status)


def _normalize_profile_status(platform: str, status: Any) -> Optional[str]:
    value = str(status or "").strip()
    if not value:
        return None

    status_map = {
        "taobao": {
            "wait_pay": "wait_pay",
            "WAIT_BUYER_PAY": "wait_pay",
            "wait_ship": "wait_ship",
            "WAIT_SELLER_SEND_GOODS": "wait_ship",
            "paid": "wait_ship",
            "shipped": "shipped",
            "WAIT_BUYER_CONFIRM_GOODS": "shipped",
            "finished": "finished",
            "TRADE_BUYER_SIGNED": "finished",
            "TRADE_FINISHED": "finished",
            "trade_closed": "trade_closed",
            "closed": "trade_closed",
            "cancelled": "trade_closed",
            "TRADE_CLOSED": "trade_closed",
            "TRADE_CLOSED_BY_TAOBAO": "trade_closed",
            "TRADE_REFUNDING": "wait_ship",
        },
        "douyin_shop": {
            "created": "created",
            "0": "created",
            "10": "created",
            "paid": "paid",
            "20": "paid",
            "30": "paid",
            "wait_ship": "paid",
            "shipped": "shipped",
            "100": "shipped",
            "110": "shipped",
            "in_transit": "shipped",
            "confirmed": "confirmed",
            "120": "confirmed",
            "completed": "completed",
            "finished": "completed",
            "200": "completed",
            "700": "completed",
            "refunding": "paid",
            "300": "paid",
            "refunded": "completed",
            "400": "completed",
            "cancelled": "cancelled",
            "500": "cancelled",
        },
        "jd": {
            "created": "created",
            "wait_pay": "created",
            "WAIT_BUYER_PAY": "created",
            "31000": "created",
            "paid": "paid",
            "32000": "paid",
            "wait_ship": "wait_seller_delivery",
            "wait_seller_delivery": "wait_seller_delivery",
            "33000": "wait_seller_delivery",
            "shipped": "wait_buyer_receive",
            "in_transit": "wait_buyer_receive",
            "wait_buyer_receive": "wait_buyer_receive",
            "34000": "wait_buyer_receive",
            "35000": "wait_buyer_receive",
            "36000": "wait_buyer_receive",
            "finished": "finished",
            "completed": "finished",
            "delivered": "finished",
            "37000": "finished",
            "cancelled": "cancelled",
            "trade_closed": "cancelled",
            "refunding": "refunding",
            "refunded": "refunded",
        },
        "xhs": {
            "created": "created",
            "pending": "created",
            "paid": "paid",
            "wait_ship": "paid",
            "delivering": "delivering",
            "shipped": "delivering",
            "in_transit": "delivering",
            "delivered": "delivered",
            "completed": "completed",
            "finished": "completed",
            "cancelled": "cancelled",
            "refund_applied": "paid",
            "refund_processing": "paid",
            "refunding": "paid",
            "refund_refused": "paid",
            "refunded": "completed",
        },
        "kuaishou": {
            "created": "created",
            "1": "created",
            "paid": "paid",
            "2": "paid",
            "wait_delivery": "wait_delivery",
            "3": "wait_delivery",
            "shipped": "delivered",
            "delivered": "delivered",
            "4": "delivered",
            "confirmed": "confirmed",
            "5": "confirmed",
            "finished": "finished",
            "completed": "finished",
            "6": "finished",
            "cancelled": "cancelled",
            "refund_applied": "paid",
            "refund_processing": "paid",
            "refunding": "paid",
            "refund_success": "finished",
            "refunded": "finished",
            "refund_rejected": "paid",
        },
    }

    platform_map = status_map.get(platform, {})
    return platform_map.get(value, platform_map.get(value.lower()))


def _unwrap_profile_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    raw_fixture = payload.get("_raw_fixture")
    if isinstance(raw_fixture, dict) and raw_fixture:
        response = raw_fixture.get("response")
        if isinstance(response, dict):
            return response
        return raw_fixture
    return payload


def _replace_order_identifier_in_payload(payload: Dict[str, Any], order_id: str) -> Dict[str, Any]:
    normalized_order_id = str(order_id)
    normalized_payload = deepcopy(payload)

    if isinstance(normalized_payload.get("trade"), dict):
        normalized_payload["trade"]["tid"] = normalized_order_id

    if isinstance(normalized_payload.get("order"), dict):
        order = normalized_payload["order"]
        if "order_id" in order:
            order["order_id"] = normalized_order_id
        if "orderId" in order:
            order["orderId"] = normalized_order_id
        if "tid" in order:
            order["tid"] = normalized_order_id

    if isinstance(normalized_payload.get("jingdong_order_search_responce"), dict):
        normalized_payload["jingdong_order_search_responce"]["orderId"] = normalized_order_id

    if "order_id" in normalized_payload:
        normalized_payload["order_id"] = normalized_order_id
    if "orderId" in normalized_payload:
        normalized_payload["orderId"] = normalized_order_id
    if "tid" in normalized_payload:
        normalized_payload["tid"] = normalized_order_id

    return normalized_payload


def _build_order_payload_for_status(platform: str, order_id: str, status: Any) -> Optional[Dict[str, Any]]:
    normalized_status = _normalize_profile_status(platform, status)
    if not normalized_status:
        return None

    try:
        if platform == "taobao":
            return _replace_order_identifier_in_payload(
                _unwrap_profile_payload(
                taobao_order_payload(order_id, TaobaoOrderStatus(normalized_status))
                ),
                order_id,
            )
        if platform == "douyin_shop":
            return _replace_order_identifier_in_payload(
                _unwrap_profile_payload(
                douyin_order_payload(order_id, DouyinOrderStatus(normalized_status))
                ),
                order_id,
            )
        if platform == "jd":
            return _replace_order_identifier_in_payload(
                _unwrap_profile_payload(
                jd_order_payload(order_id, JdOrderStatus(normalized_status))
                ),
                order_id,
            )
        if platform == "xhs":
            return _replace_order_identifier_in_payload(
                _unwrap_profile_payload(
                xhs_order_payload(order_id, XhsOrderStatus(normalized_status))
                ),
                order_id,
            )
        if platform == "kuaishou":
            return _replace_order_identifier_in_payload(
                _unwrap_profile_payload(
                kuaishou_order_payload(order_id, KuaishouOrderStatus(normalized_status))
                ),
                order_id,
            )
    except Exception:
        return None

    return None


def _find_fixture_user_order(platform: str, order_id: str) -> Optional[Dict[str, Any]]:
    return FixtureLoader.find_user_order(platform, order_id)


def _find_fixture_order_payload(platform: str, order_id: str) -> Optional[Dict[str, Any]]:
    for scenario_key in _iter_order_fixture_keys(platform, PREFERRED_ORDER_FIXTURE_KEYS.get(platform, ())):
        try:
            fixture = FixtureLoader.load(platform, scenario_key, "success")
        except FileNotFoundError:
            continue

        if fixture.get("fixture_type") != "order":
            continue
        response = fixture.get("response", {})
        if _extract_order_id(response) == str(order_id):
            return response

    user_order = _find_fixture_user_order(platform, order_id)
    if user_order:
        official_response = user_order.get("official_response")
        if isinstance(official_response, dict) and official_response:
            return deepcopy(official_response)

        payload_order_id = str(user_order.get("external_order_id") or order_id)
        payload = _build_order_payload_for_status(platform, payload_order_id, user_order.get("status"))
        if payload:
            return payload
        return deepcopy(user_order)

    return None


def _iter_order_fixture_keys(platform: str, preferred_keys: tuple[str, ...]) -> List[str]:
    available = FixtureLoader.list_fixtures(platform, "success")
    ordered: List[str] = []
    for scenario_key in [*preferred_keys, *sorted(available)]:
        if scenario_key not in ordered:
            ordered.append(scenario_key)
    return ordered


def _find_fixture_shipment_payload(platform: str, order_id: str) -> Optional[Dict[str, Any]]:
    for scenario_key in _iter_order_fixture_keys(platform, PREFERRED_SHIPMENT_FIXTURE_KEYS.get(platform, ())):
        try:
            fixture = FixtureLoader.load(platform, scenario_key, "success")
        except FileNotFoundError:
            continue

        if fixture.get("fixture_type") != "order":
            continue
        response = fixture.get("response", {})
        if _extract_order_id(response) != str(order_id):
            continue
        if _payload_has_shipment_details(response):
            return response

    user_order = _find_fixture_user_order(platform, order_id)
    if isinstance(user_order, dict) and user_order:
        shipment = user_order.get("shipment", {})
        if isinstance(shipment, dict) and shipment:
            official_response = shipment.get("official_response")
            if isinstance(official_response, dict) and official_response:
                return deepcopy(official_response)

            payload_order_id = str(user_order.get("external_order_id") or order_id)
            payload = deepcopy(shipment)
            payload.setdefault("shipment_id", f"SHIP_{payload_order_id}")
            payload.setdefault("order_id", str(user_order.get("order_id") or order_id))
            payload.setdefault("external_order_id", payload_order_id)
            payload.setdefault("requested_order_id", str(order_id))
            return payload

    return None


def _has_fixture_order_reference(platform: str, order_id: str) -> bool:
    if _find_fixture_user_order(platform, order_id):
        return True

    for scenario_key in _iter_order_fixture_keys(platform, PREFERRED_ORDER_FIXTURE_KEYS.get(platform, ())):
        try:
            fixture = FixtureLoader.load(platform, scenario_key, "success")
        except FileNotFoundError:
            continue

        if fixture.get("fixture_type") != "order":
            continue
        response = fixture.get("response", {})
        if _extract_order_id(response) == str(order_id):
            return True

    return False


def _payload_has_shipment_details(payload: Dict[str, Any]) -> bool:
    if not isinstance(payload, dict):
        return False

    if isinstance(payload.get("trade"), dict):
        trade = payload["trade"]
        items = trade.get("orders", {}).get("order", []) or payload.get("orders", {}).get("order", [])
        first_item = items[0] if items else {}
        return any(
            (
                first_item.get("logistics_company"),
                first_item.get("invoice_no"),
                trade.get("consign_time"),
            )
        )

    if isinstance(payload.get("order"), dict):
        order = payload["order"]
        delivery_info = order.get("delivery_info", {})
        logistics = order.get("logistics", {})
        return any(
            (
                delivery_info.get("company_name"),
                delivery_info.get("tracking_no"),
                logistics.get("logisticsCompany"),
                logistics.get("company"),
                logistics.get("trackingNo"),
                order.get("deliveryTime"),
                order.get("delivery_time"),
                order.get("consign_time"),
            )
        )

    if isinstance(payload.get("jingdong_order_search_responce"), dict):
        order = payload["jingdong_order_search_responce"]
        return any((order.get("deliveryCarrierName"), order.get("deliveryBillNo"), order.get("orderStatusTime")))

    return any((payload.get("company"), payload.get("tracking_no"), payload.get("nodes")))


def _build_run_order_payload(
    run_id: UUID,
    platform: str,
    order_id: str,
    db: Session,
) -> Optional[Dict[str, Any]]:
    _, status, _ = _get_run_order_state(run_id, platform, db)
    if not status:
        return None

    return _build_order_payload_for_status(platform, order_id, status)


def _get_run_order_state(
    run_id: UUID,
    platform: str,
    db: Session,
) -> tuple[Any, Optional[str], Optional[str]]:
    run_repo = RunRepository(db)
    snapshot_repo = SnapshotRepository(db)

    run = run_repo.get_by_id(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    if run.platform != platform:
        raise HTTPException(status_code=400, detail="Run platform does not match query platform")

    latest_snapshot = snapshot_repo.get_latest(run_id)
    status = None
    if latest_snapshot:
        status = (latest_snapshot.order_state_json or {}).get("status")
    scenario_name = (run.metadata_json or {}).get("scenario_name")
    if not status:
        status = _get_initial_run_status(platform, scenario_name)
    return run, status, scenario_name


def _build_run_shipment_payload(
    run_id: UUID,
    platform: str,
    order_id: str,
    db: Session,
) -> Optional[Dict[str, Any]]:
    _, status, _ = _get_run_order_state(run_id, platform, db)
    normalized_status = _normalize_profile_status(platform, status)
    if normalized_status not in {
        "shipped",
        "finished",
        "confirmed",
        "completed",
        "wait_buyer_receive",
        "delivering",
        "delivered",
    }:
        return None

    payload = _build_order_payload_for_status(platform, order_id, status)
    if not isinstance(payload, dict):
        return None

    if isinstance(payload.get("trade"), dict):
        trade = payload["trade"]
        items = trade.get("orders", {}).get("order", [])
        if not items:
            items = payload.get("orders", {}).get("order", [])
        first_item = items[0] if items else {}
        return {
            "shipment_id": f"SHIP_{order_id}",
            "order_id": order_id,
            "status": "delivered" if normalized_status == "finished" else "shipped",
            "company": first_item.get("logistics_company"),
            "tracking_no": first_item.get("invoice_no"),
            "created_at": trade.get("consign_time") or trade.get("modified"),
            "updated_at": trade.get("modified") or trade.get("end_time"),
        }

    if isinstance(payload.get("order"), dict):
        order = payload["order"]
        delivery_info = order.get("delivery_info", {})
        logistics = order.get("logistics", {})
        company = (
            delivery_info.get("company_name")
            or logistics.get("logisticsCompany")
            or logistics.get("company")
        )
        tracking_no = delivery_info.get("tracking_no") or logistics.get("trackingNo")
        return {
            "shipment_id": f"SHIP_{order_id}",
            "order_id": order_id,
            "status": logistics.get("status") or delivery_info.get("delivery_status_desc") or normalized_status,
            "company": company,
            "tracking_no": tracking_no,
            "created_at": order.get("deliveryTime") or order.get("consign_time") or order.get("update_time"),
            "updated_at": order.get("updateTime") or order.get("finish_time") or order.get("deliveryTime"),
        }

    if isinstance(payload.get("jingdong_order_search_responce"), dict):
        order = payload["jingdong_order_search_responce"]
        return {
            "shipment_id": f"SHIP_{order_id}",
            "order_id": order_id,
            "status": "delivered" if normalized_status == "finished" else "shipped",
            "company": order.get("deliveryCarrierName"),
            "tracking_no": order.get("deliveryBillNo"),
            "created_at": order.get("orderStatusTime"),
            "updated_at": order.get("deliveryConfirmTime") or order.get("orderStatusTime"),
        }

    return None


def _build_run_after_sale_payload(
    run_id: UUID,
    platform: str,
    after_sale_id: str,
    db: Session,
) -> Optional[Dict[str, Any]]:
    run, status, scenario_name = _get_run_order_state(run_id, platform, db)
    normalized_status = _normalize_profile_status(platform, status)
    if not normalized_status:
        return None

    metadata = run.metadata_json or {}
    resolved_order_id = (
        parse_canonical_after_sale_id(platform, after_sale_id)
        or metadata.get("order_id")
        or after_sale_id
    )
    canonical_after_sale_id = build_canonical_after_sale_id(platform, str(resolved_order_id))
    requested_identifier = str(after_sale_id)

    if platform == "douyin_shop":
        if normalized_status == "refunding":
            payload = _unwrap_profile_payload(
                douyin_refund_payload(after_sale_id, after_sale_id, DouyinRefundStatus.REFUNDING)
            )
            return _normalize_after_sale_payload(
                platform,
                payload,
                requested_order_id=str(resolved_order_id),
                forced_after_sale_id=canonical_after_sale_id,
                fallback_order_id=str(resolved_order_id),
                requested_identifier=requested_identifier,
            )
        if normalized_status == "refunded":
            payload = _unwrap_profile_payload(
                douyin_refund_payload(after_sale_id, after_sale_id, DouyinRefundStatus.REFUNDED)
            )
            return _normalize_after_sale_payload(
                platform,
                payload,
                requested_order_id=str(resolved_order_id),
                forced_after_sale_id=canonical_after_sale_id,
                fallback_order_id=str(resolved_order_id),
                requested_identifier=requested_identifier,
            )
        return None

    if platform == "jd":
        if normalized_status == "refunding":
            payload = _unwrap_profile_payload(
                jd_refund_payload(str(resolved_order_id), str(canonical_after_sale_id), JdRefundStatus.REFUNDING)
            )
            return _normalize_after_sale_payload(
                platform,
                payload,
                requested_order_id=str(resolved_order_id),
                forced_after_sale_id=canonical_after_sale_id,
                fallback_order_id=str(resolved_order_id),
                requested_identifier=requested_identifier,
            )
        if normalized_status == "refunded":
            payload = _unwrap_profile_payload(
                jd_refund_payload(str(resolved_order_id), str(canonical_after_sale_id), JdRefundStatus.REFUNDED)
            )
            return _normalize_after_sale_payload(
                platform,
                payload,
                requested_order_id=str(resolved_order_id),
                forced_after_sale_id=canonical_after_sale_id,
                fallback_order_id=str(resolved_order_id),
                requested_identifier=requested_identifier,
            )
        return None

    if platform == "xhs":
        status_map = {
            "refund_applied": XhsRefundStatus.APPLIED,
            "refund_processing": XhsRefundStatus.PROCESSING,
            "refund_refused": XhsRefundStatus.REFUSED,
            "refunded": XhsRefundStatus.REFUNDED,
        }
        refund_status = status_map.get(normalized_status)
        if refund_status:
            payload = xhs_refund_payload(str(resolved_order_id), str(canonical_after_sale_id), refund_status)
            return _normalize_after_sale_payload(
                platform,
                payload,
                requested_order_id=str(resolved_order_id),
                forced_after_sale_id=canonical_after_sale_id,
                fallback_order_id=str(resolved_order_id),
                requested_identifier=requested_identifier,
            )
        return None

    if platform == "kuaishou":
        status_map = {
            "refund_applied": KuaishouRefundStatus.APPLIED,
            "refund_processing": KuaishouRefundStatus.PROCESSING,
            "refund_success": KuaishouRefundStatus.SUCCESS,
            "refund_rejected": KuaishouRefundStatus.REJECTED,
        }
        refund_status = status_map.get(normalized_status)
        if refund_status:
            payload = kuaishou_refund_payload(str(resolved_order_id), str(canonical_after_sale_id), refund_status)
            return _normalize_after_sale_payload(
                platform,
                payload,
                requested_order_id=str(resolved_order_id),
                forced_after_sale_id=canonical_after_sale_id,
                fallback_order_id=str(resolved_order_id),
                requested_identifier=requested_identifier,
            )
        return None

    if platform == "taobao" and scenario_name and "refund" in scenario_name:
        payload = _unwrap_profile_payload(
            taobao_refund_payload(str(resolved_order_id), str(canonical_after_sale_id), TaobaoRefundStatus.REFUNDING)
        )
        return _normalize_after_sale_payload(
            platform,
            payload,
            requested_order_id=str(resolved_order_id),
            forced_after_sale_id=canonical_after_sale_id,
            fallback_order_id=str(resolved_order_id),
            requested_identifier=requested_identifier,
        )

    return None


def _extract_refund_block(platform: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        return {}

    if isinstance(payload.get("after_sale"), dict):
        return deepcopy(payload["after_sale"])

    if isinstance(payload.get("refund"), dict):
        return deepcopy(payload["refund"])

    if platform == "jd":
        response = payload.get("jingdong_refund_apply_query_response")
        if isinstance(response, dict):
            result = response.get("result") or {}
            service_status = result.get("afsServiceStatus") or {}
            return {
                "refund_id": service_status.get("serviceId") or result.get("applyId"),
                "order_id": result.get("orderId"),
                "status": (payload.get("initial_state") or {}).get("refund_status") or result.get("status"),
                "status_text": service_status.get("afsServiceStepName"),
                "reason": result.get("questionDesc"),
                "description": result.get("questionDesc"),
                "refund_amount": result.get("refundAmount"),
                "apply_time": result.get("afsApplyTime"),
                "update_time": result.get("updateTime"),
                "express_company": service_status.get("expressCompany"),
                "express_no": service_status.get("expressNo"),
            }

    if platform == "kuaishou":
        if isinstance(payload.get("refundInfo"), dict):
            return deepcopy(payload["refundInfo"])
        if isinstance(payload.get("order"), dict) and isinstance(payload["order"].get("refundInfo"), dict):
            return deepcopy(payload["order"]["refundInfo"])

    return deepcopy(payload)


def _candidate_after_sale_identifiers(payload: Dict[str, Any]) -> List[str]:
    candidates: List[str] = []
    for key in (
        "after_sale_id",
        "canonical_after_sale_id",
        "external_after_sale_id",
        "refund_id",
        "refundId",
        "afsServiceId",
        "id",
    ):
        value = payload.get(key)
        if value not in (None, ""):
            normalized = str(value)
            if normalized not in candidates:
                candidates.append(normalized)
    return candidates


def _normalize_after_sale_payload(
    platform: str,
    payload: Dict[str, Any],
    *,
    requested_order_id: Optional[str] = None,
    forced_after_sale_id: Optional[str] = None,
    fallback_order_id: Optional[str] = None,
    requested_identifier: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    refund = _extract_refund_block(platform, payload)
    if not isinstance(refund, dict) or not refund:
        return None

    order_id = (
        refund.get("order_id")
        or refund.get("orderId")
        or refund.get("tid")
        or fallback_order_id
        or requested_order_id
    )
    if order_id in (None, ""):
        return None

    order_id_text = str(order_id)
    primary_order_id = get_primary_order_id(platform, order_id_text)
    canonical_after_sale_id = forced_after_sale_id or build_canonical_after_sale_id(platform, order_id_text)
    external_after_sale_id = (
        refund.get("external_after_sale_id")
        or refund.get("refund_id")
        or refund.get("refundId")
        or refund.get("afsServiceId")
        or refund.get("id")
    )

    created_at = (
        refund.get("created_at")
        or refund.get("apply_time")
        or refund.get("create_time")
        or refund.get("createTime")
        or refund.get("afsApplyTime")
        or refund.get("refund_time")
        or refund.get("modified")
    )
    updated_at = (
        refund.get("updated_at")
        or refund.get("update_time")
        or refund.get("updateTime")
        or refund.get("refund_time")
        or refund.get("finish_time")
        or refund.get("modified")
        or created_at
    )

    return {
        "after_sale_id": canonical_after_sale_id,
        "canonical_after_sale_id": canonical_after_sale_id,
        "external_after_sale_id": str(external_after_sale_id) if external_after_sale_id not in (None, "") else None,
        "refund_id": str(external_after_sale_id) if external_after_sale_id not in (None, "") else canonical_after_sale_id,
        "order_id": order_id_text,
        "external_order_id": primary_order_id,
        "requested_order_id": requested_order_id or order_id_text,
        "requested_identifier": requested_identifier,
        "status": (
            refund.get("status")
            or refund.get("refund_status")
            or refund.get("refundStatus")
            or "unknown"
        ),
        "status_text": (
            refund.get("status_text")
            or refund.get("statusDesc")
            or refund.get("refund_status_desc")
            or refund.get("refundStatusDesc")
            or refund.get("afsServiceStepName")
            or refund.get("status")
            or refund.get("refund_status")
            or refund.get("refundStatus")
        ),
        "reason": (
            refund.get("reason")
            or refund.get("refund_reason")
            or refund.get("reason_desc")
            or refund.get("refundReason")
            or refund.get("questionDesc")
            or ""
        ),
        "description": (
            refund.get("description")
            or refund.get("reason_detail")
            or refund.get("reasonDetail")
            or refund.get("questionDesc")
        ),
        "refund_amount": (
            refund.get("refund_amount")
            or refund.get("refund_fee")
            or refund.get("refundAmount")
            or refund.get("amount")
            or "0"
        ),
        "created_at": created_at,
        "updated_at": updated_at,
    }


def _iter_refund_fixtures(platform: str) -> List[Dict[str, Any]]:
    fixtures: List[Dict[str, Any]] = []
    for fixture_type in ("success", "edge_case"):
        for scenario_key in FixtureLoader.list_fixtures(platform, fixture_type):
            try:
                fixture = FixtureLoader.load(platform, scenario_key, fixture_type)
            except FileNotFoundError:
                continue
            if fixture.get("fixture_type") != "refund":
                continue
            fixtures.append(fixture)
    return fixtures


def _build_fixture_user_after_sale_payload(
    platform: str,
    order: Dict[str, Any],
    *,
    requested_order_id: Optional[str] = None,
    requested_identifier: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    refund = deepcopy(order.get("refund") or {})
    if not refund:
        return None

    payload = {
        "after_sale_id": build_canonical_after_sale_id(platform, str(order.get("order_id"))),
        "refund_id": refund.get("refund_id") or refund.get("after_sale_id"),
        "external_after_sale_id": refund.get("refund_id") or refund.get("after_sale_id"),
        "order_id": order.get("order_id"),
        "status": refund.get("status"),
        "status_text": refund.get("status_text") or order.get("status_text"),
        "reason": refund.get("reason"),
        "description": refund.get("description"),
        "refund_amount": refund.get("amount") or refund.get("refund_amount"),
        "created_at": refund.get("apply_time") or refund.get("created_at") or order.get("created_at"),
        "updated_at": refund.get("refund_time") or refund.get("update_time") or refund.get("apply_time") or order.get("created_at"),
    }
    return _normalize_after_sale_payload(
        platform,
        payload,
        requested_order_id=requested_order_id or str(order.get("order_id")),
        forced_after_sale_id=build_canonical_after_sale_id(platform, str(order.get("order_id"))),
        fallback_order_id=str(order.get("order_id")),
        requested_identifier=requested_identifier,
    )


def _find_fixture_user_after_sale_by_order(platform: str, order_id: str) -> Optional[Dict[str, Any]]:
    for candidate_order_id in iter_order_id_aliases(platform, order_id):
        user_data = FixtureLoader.get_user_by_order(platform, candidate_order_id)
        if not user_data:
            continue
        for order in user_data.get("orders", []):
            if str(order.get("order_id")) != str(candidate_order_id):
                continue
            if not order.get("refund"):
                continue
            payload = _build_fixture_user_after_sale_payload(
                platform,
                order,
                requested_order_id=str(order_id),
                requested_identifier=str(order_id),
            )
            if payload is not None:
                return payload
    return None


def _find_fixture_user_after_sale_by_identifier(platform: str, after_sale_id: str) -> Optional[Dict[str, Any]]:
    for user_id in FixtureLoader.list_users(platform):
        try:
            user_data = FixtureLoader.load_user(platform, user_id)
        except FileNotFoundError:
            continue
        for order in user_data.get("orders", []):
            if not order.get("refund"):
                continue
            payload = _build_fixture_user_after_sale_payload(
                platform,
                order,
                requested_order_id=str(order.get("order_id")),
                requested_identifier=str(after_sale_id),
            )
            if payload is None:
                continue
            if str(after_sale_id) in _candidate_after_sale_identifiers(payload):
                return payload
    return None


def _find_fixture_after_sale_payload_by_order(platform: str, order_id: str) -> Optional[Dict[str, Any]]:
    user_payload = _find_fixture_user_after_sale_by_order(platform, order_id)
    if user_payload is not None:
        return user_payload

    alias_candidates = iter_order_id_aliases(platform, order_id)
    for fixture in _iter_refund_fixtures(platform):
        payload = _normalize_after_sale_payload(
            platform,
            fixture,
            requested_order_id=str(order_id),
            requested_identifier=str(order_id),
        )
        if payload is None:
            continue
        if str(payload.get("order_id")) in alias_candidates or str(payload.get("external_order_id")) in alias_candidates:
            return payload
    return None


def _find_fixture_after_sale_payload(platform: str, after_sale_id: str) -> Optional[Dict[str, Any]]:
    canonical_order_id = parse_canonical_after_sale_id(platform, after_sale_id)
    if canonical_order_id:
        payload = _find_fixture_after_sale_payload_by_order(platform, canonical_order_id)
        if payload is not None:
            return payload

    user_payload = _find_fixture_user_after_sale_by_identifier(platform, after_sale_id)
    if user_payload is not None:
        return user_payload

    for fixture in _iter_refund_fixtures(platform):
        payload = _normalize_after_sale_payload(
            platform,
            fixture,
            requested_identifier=str(after_sale_id),
        )
        if payload is None:
            continue
        if str(after_sale_id) in _candidate_after_sale_identifiers(payload):
            return payload

    return _find_fixture_after_sale_payload_by_order(platform, after_sale_id)


def _to_iso_datetime(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc).isoformat()
    return str(value)


def _normalize_conversation_status(value: Any) -> str:
    status = str(value or "").strip().lower()
    if status in {"running", "active", "in_session"}:
        return "active"
    if status in {"created", "pending", "waiting"}:
        return "waiting"
    if status in {"closed", "completed", "ended", "resolved"}:
        return "closed"
    return status or "waiting"


def _infer_order_platform(order_id: Any) -> Optional[str]:
    if not order_id:
        return None
    upper = str(order_id).upper()
    if upper.startswith("JD_") or "JD_ORDER" in upper:
        return "jd"
    if upper.startswith("TB_") or "TAOBAO" in upper:
        return "taobao"
    if upper.startswith("DY_") or upper.startswith("DS_") or "DOUYIN" in upper:
        return "douyin_shop"
    if upper.startswith("XHS_"):
        return "xhs"
    if upper.startswith("KS_") or "KUAISHOU" in upper:
        return "kuaishou"
    return None


def _artifact_turn_no(artifact: Any) -> int:
    request_body = artifact.request_body_json or {}
    turn_no = request_body.get("turn_no")
    if isinstance(turn_no, int):
        return turn_no
    try:
        return int(turn_no)
    except (TypeError, ValueError):
        return int(getattr(artifact, "step_no", 0) or 0)


def _artifact_payload(artifact: Any) -> Dict[str, Any]:
    payload = artifact.response_body_json or {}
    return payload if isinstance(payload, dict) else {}


def _sort_conversation_artifacts(artifacts: List[Any]) -> List[Any]:
    return sorted(
        artifacts,
        key=lambda artifact: (
            _artifact_turn_no(artifact),
            int(getattr(artifact, "step_no", 0) or 0),
            _to_iso_datetime(getattr(artifact, "created_at", None)) or "",
        ),
    )


def _rebuild_run_messages(
    conversation_id: str,
    artifacts: List[Any],
    default_sender: Optional[str],
) -> List[Dict[str, Any]]:
    by_turn: Dict[int, Dict[str, Any]] = {}
    for artifact in _sort_conversation_artifacts(artifacts):
        route_key = artifact.route_key or ""
        if route_key not in {"user_message_payload", "conversation_turn_payload"}:
            continue
        turn_no = _artifact_turn_no(artifact)
        bucket = by_turn.setdefault(turn_no, {})
        bucket[route_key] = artifact

    messages: List[Dict[str, Any]] = []
    for turn_no in sorted(by_turn):
        turn_artifacts = by_turn[turn_no]
        user_artifact = turn_artifacts.get("user_message_payload")
        turn_artifact = turn_artifacts.get("conversation_turn_payload")
        user_payload = _artifact_payload(user_artifact) if user_artifact is not None else {}
        turn_payload = _artifact_payload(turn_artifact) if turn_artifact is not None else {}
        created_at = _to_iso_datetime(
            getattr(user_artifact or turn_artifact, "created_at", None)
        ) or datetime.now(timezone.utc).isoformat()

        user_message = (
            turn_payload.get("user_message")
            or user_payload.get("user_message")
            or user_payload.get("text")
        )
        if user_message:
            messages.append(
                {
                    "msg_id": f"{conversation_id}:customer:{turn_no}",
                    "conversation_id": conversation_id,
                    "msg_type": "text",
                    "content": str(user_message),
                    "sender": user_payload.get("user_id") or turn_payload.get("user_id") or default_sender,
                    "sender_type": "customer",
                    "created_at": created_at,
                }
            )

        reply_message = turn_payload.get("reply_message")
        if reply_message:
            messages.append(
                {
                    "msg_id": f"{conversation_id}:agent:{turn_no}",
                    "conversation_id": conversation_id,
                    "msg_type": "text",
                    "content": str(reply_message),
                    "sender": turn_payload.get("reply_source") or "domain-service",
                    "sender_type": "agent",
                    "created_at": _to_iso_datetime(getattr(turn_artifact, "created_at", None))
                    or created_at,
                }
            )

    return messages


def _build_run_conversation_fact(
    run: Any,
    artifacts: List[Any],
    snapshot: Any = None,
) -> Optional[Dict[str, Any]]:
    metadata = run.metadata_json or {}
    relevant_artifacts = [
        artifact
        for artifact in artifacts
        if (artifact.route_key or "")
        in {
            "user_message_payload",
            "conversation_turn_payload",
            "reply_recommendation_payload",
        }
    ]
    ordered_artifacts = _sort_conversation_artifacts(relevant_artifacts)
    if not ordered_artifacts and not metadata.get("conversation_id"):
        return None

    latest_payload: Dict[str, Any] = {}
    for artifact in ordered_artifacts:
        payload = _artifact_payload(artifact)
        if payload:
            latest_payload = payload

    conversation_id = (
        latest_payload.get("conversation_id")
        or metadata.get("conversation_id")
        or f"conv_{str(run.id).replace('-', '')[:12]}"
    )
    user_id = latest_payload.get("user_id") or metadata.get("user_id")
    order_id = latest_payload.get("order_id") or metadata.get("order_id")

    if not conversation_id:
        return None

    messages = _rebuild_run_messages(conversation_id, ordered_artifacts, user_id)
    latest_turn_payload = {}
    for artifact in reversed(ordered_artifacts):
        if (artifact.route_key or "") == "conversation_turn_payload":
            latest_turn_payload = _artifact_payload(artifact)
            break

    snapshot_status = {}
    if snapshot is not None:
        snapshot_status = snapshot.conversation_state_json or {}

    created_at = _to_iso_datetime(
        getattr(ordered_artifacts[0], "created_at", None) if ordered_artifacts else run.created_at
    ) or datetime.now(timezone.utc).isoformat()
    updated_at = _to_iso_datetime(
        getattr(ordered_artifacts[-1], "created_at", None) if ordered_artifacts else run.updated_at
    ) or created_at

    status = _normalize_conversation_status(
        latest_turn_payload.get("conversation_status")
        or snapshot_status.get("status")
        or run.status.value
    )

    return {
        "id": conversation_id,
        "conversation_id": conversation_id,
        "platform": run.platform,
        "official_run_id": str(run.id),
        "customer_id": user_id,
        "customer_nick": user_id,
        "status": status,
        "status_text": status,
        "openid": user_id,
        "scene": "customer_service",
        "created_at": created_at,
        "updated_at": updated_at,
        "last_message_time": updated_at,
        "biz_id": order_id,
        "biz_type": "order" if order_id else "conversation",
        "biz_platform": _infer_order_platform(order_id) or run.platform,
        "external_biz_id": order_id,
        "message_count": len(messages),
        "messages": messages,
    }


def _list_run_conversations(
    platform: str,
    db: Session,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    run_repo = RunRepository(db)
    artifact_repo = ArtifactRepository(db)
    snapshot_repo = SnapshotRepository(db)

    runs = run_repo.list_by_platform(platform, limit=limit, offset=0)
    conversations: List[Dict[str, Any]] = []
    for run in runs:
        artifacts = artifact_repo.list_by_run(run.id)
        snapshot = snapshot_repo.get_latest(run.id)
        fact = _build_run_conversation_fact(run, artifacts, snapshot=snapshot)
        if fact is not None:
            conversations.append(fact)
    return conversations


def _find_run_conversation(
    platform: str,
    conversation_id: str,
    db: Session,
    run_id: Optional[UUID] = None,
) -> Optional[Dict[str, Any]]:
    run_repo = RunRepository(db)
    artifact_repo = ArtifactRepository(db)
    snapshot_repo = SnapshotRepository(db)

    candidate_runs: List[Any]
    if run_id is not None:
        run = run_repo.get_by_id(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Run not found")
        if run.platform != platform:
            raise HTTPException(status_code=400, detail="Run platform does not match query platform")
        candidate_runs = [run]
    else:
        candidate_runs = run_repo.list_by_platform(platform, limit=200, offset=0)

    for run in candidate_runs:
        artifacts = artifact_repo.list_by_run(run.id)
        snapshot = snapshot_repo.get_latest(run.id)
        fact = _build_run_conversation_fact(run, artifacts, snapshot=snapshot)
        if fact and fact["conversation_id"] == conversation_id:
            return fact
    return None


@router.get("/orders/{order_id}")
async def raw_get_order(
    order_id: str,
    platform: str = Query(..., description="Platform: taobao, douyin_shop, jd, xhs, kuaishou, wecom_kf"),
    scenario_key: str = Query(None, description="Scenario key (e.g. trade_wait_pay, trade_shipped)"),
    run_id: Optional[UUID] = Query(None, description="official-sim run UUID"),
    db: Session = Depends(get_db),
):
    try:
        if run_id:
            payload = _build_run_order_payload(run_id, platform, order_id, db)
            if payload is None:
                raise HTTPException(status_code=404, detail="Run order state not found")
            return RawQueryResponse(data=payload, source="run")

        if scenario_key:
            fixture = FixtureLoader.load(platform, scenario_key, "success")
            return RawQueryResponse(
                data=fixture.get("response", {}),
                source="fixture"
            )

        payload = _find_fixture_order_payload(platform, order_id)
        if payload is not None:
            return RawQueryResponse(data=payload, source="fixture")

        raise HTTPException(status_code=404, detail=f"No order fixture found for platform {platform}")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Order fixture not found")


@router.get("/shipments/{order_id}")
async def raw_get_shipment(
    order_id: str,
    platform: str = Query(..., description="Platform: taobao, douyin_shop, jd, xhs, kuaishou"),
    scenario_key: str = Query(None, description="Scenario key (e.g. trade_shipped)"),
    run_id: Optional[UUID] = Query(None, description="official-sim run UUID"),
    db: Session = Depends(get_db),
):
    try:
        if run_id:
            payload = _build_run_shipment_payload(run_id, platform, order_id, db)
            if payload is None:
                raise HTTPException(status_code=404, detail="Run shipment state not found")
            return RawQueryResponse(data=payload, source="run")

        if scenario_key:
            fixture = FixtureLoader.load(platform, scenario_key, "success")
            return RawQueryResponse(
                data=fixture.get("response", {}),
                source="fixture",
            )

        payload = _find_fixture_shipment_payload(platform, order_id)
        if payload is not None:
            return RawQueryResponse(data=payload, source="fixture")

        if _has_fixture_order_reference(platform, order_id):
            raise HTTPException(status_code=404, detail=f"No shipment fixture found for order {order_id}")

        key = SHIPMENT_SCENARIO_MAP.get(platform, "trade_shipped")
        fixture = FixtureLoader.load(platform, key, "success")
        return RawQueryResponse(
            data=fixture.get("response", {}),
            source="fixture",
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Shipment fixture not found for platform {platform}")


@router.get("/after-sales/by-order/{order_id}")
async def raw_get_after_sale_by_order(
    order_id: str,
    platform: str = Query(..., description="Platform: taobao, douyin_shop, jd, xhs, kuaishou"),
    run_id: Optional[UUID] = Query(None, description="official-sim run UUID"),
    db: Session = Depends(get_db),
):
    if run_id:
        payload = _build_run_after_sale_payload(run_id, platform, order_id, db)
        if payload is None:
            raise HTTPException(status_code=404, detail="Run after-sale state not found")
        return RawQueryResponse(
            data={"after_sale": payload, "order_id": order_id},
            source="run",
        )

    payload = _find_fixture_after_sale_payload_by_order(platform, order_id)
    if payload is None:
        raise HTTPException(status_code=404, detail=f"No after-sale fixture found for order {order_id}")

    return RawQueryResponse(
        data={"after_sale": payload, "order_id": order_id},
        source="fixture",
    )


@router.get("/after-sales/{after_sale_id}")
async def raw_get_after_sale(
    after_sale_id: str,
    platform: str = Query(..., description="Platform: taobao, douyin_shop, jd, xhs, kuaishou"),
    scenario_key: str = Query(None, description="Scenario key (e.g. refund_requested)"),
    run_id: Optional[UUID] = Query(None, description="official-sim run UUID"),
    db: Session = Depends(get_db),
):
    if run_id:
        payload = _build_run_after_sale_payload(run_id, platform, after_sale_id, db)
        if payload is None:
            raise HTTPException(status_code=404, detail="Run after-sale state not found")
        return RawQueryResponse(data={"after_sale": payload}, source="run")

    payload = _find_fixture_after_sale_payload(platform, after_sale_id)
    if payload is not None:
        return RawQueryResponse(data={"after_sale": payload}, source="fixture")

    try:
        key = scenario_key or REFUND_SCENARIO_MAP.get(platform, "refund_requested")
        fixture = FixtureLoader.load(platform, key, "success")
        payload = _normalize_after_sale_payload(
            platform,
            fixture,
            requested_identifier=str(after_sale_id),
        )
        if payload is None:
            raise HTTPException(status_code=404, detail=f"No after-sale fixture found for platform {platform}")
        return RawQueryResponse(data={"after_sale": payload}, source="fixture")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"After-sale fixture not found for platform {platform}")


@router.get("/conversations")
async def raw_list_conversations(
    platform: str = Query(..., description="Platform: wecom_kf"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    conversations = _list_run_conversations(platform, db, limit=limit)
    items = [
        {key: value for key, value in conversation.items() if key != "messages"}
        for conversation in conversations
    ]
    return RawQueryResponse(
        data={"items": items, "total": len(items)},
        source="run",
    )


@router.get("/conversations/{conversation_id}/messages")
async def raw_get_conversation_messages(
    conversation_id: str,
    platform: str = Query(..., description="Platform: wecom_kf"),
    run_id: Optional[UUID] = Query(None, description="official-sim run UUID"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    fact = _find_run_conversation(platform, conversation_id, db, run_id=run_id)
    if fact is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = list(fact.get("messages", []))[:limit]
    return RawQueryResponse(
        data={
            "conversation_id": conversation_id,
            "official_run_id": fact.get("official_run_id"),
            "messages": messages,
            "total": len(messages),
        },
        source="run",
    )


@router.get("/conversations/{conversation_id}")
async def raw_get_conversation(
    conversation_id: str,
    platform: str = Query(..., description="Platform: wecom_kf"),
    run_id: Optional[UUID] = Query(None, description="official-sim run UUID"),
    db: Session = Depends(get_db),
):
    fact = _find_run_conversation(platform, conversation_id, db, run_id=run_id)
    if fact is not None:
        payload = {key: value for key, value in fact.items() if key != "messages"}
        return RawQueryResponse(data=payload, source="run")

    return RawQueryResponse(
        data={
            "conversation_id": conversation_id,
            "platform": platform,
            "message": "Use /mock/wecom-kf/messages/sync for conversation data",
        },
        source="fixture",
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
