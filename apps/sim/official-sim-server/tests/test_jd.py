import pytest
from fastapi.testclient import TestClient


def test_jd_profile_exists():
    from app.platforms.jd.profile import JdOrderStatus, ORDER_SCENARIOS
    assert JdOrderStatus.CREATED.value == "created"
    assert "basic_order" in ORDER_SCENARIOS
    assert "full_flow" in ORDER_SCENARIOS
    assert "refund_flow" in ORDER_SCENARIOS


def test_jd_order_status_transitions():
    from app.platforms.jd.profile import (
        JdOrderStatus,
        JD_ORDER_STATUS_TRANSITIONS,
        validate_status_transition,
    )
    assert JdOrderStatus.CREATED in JD_ORDER_STATUS_TRANSITIONS
    assert JdOrderStatus.PAID in JD_ORDER_STATUS_TRANSITIONS[JdOrderStatus.CREATED]
    assert validate_status_transition(JdOrderStatus.CREATED, JdOrderStatus.PAID) is True
    assert validate_status_transition(JdOrderStatus.CREATED, JdOrderStatus.FINISHED) is False


def test_jd_order_payload():
    from app.platforms.jd.profile import get_default_order_payload, JdOrderStatus

    payload = get_default_order_payload("JD_ORDER_001", JdOrderStatus.PAID)
    assert payload["order_id"] == "JD_ORDER_001"
    assert payload["status"] == "paid"
    assert "receiver" in payload
    assert payload["receiver"]["name"] == "王五"


def test_jd_shipment_payload():
    from app.platforms.jd.profile import get_default_shipment_payload, JdShipmentStatus

    payload = get_default_shipment_payload("JD_ORDER_001", "JD_SHIP_001", JdShipmentStatus.SHIPPED)
    assert payload["order_id"] == "JD_ORDER_001"
    assert payload["shipment_id"] == "JD_SHIP_001"
    assert payload["status"] == "shipped"
    assert "nodes" in payload
    assert len(payload["nodes"]) == 3


def test_jd_refund_payload():
    from app.platforms.jd.profile import get_default_refund_payload, JdRefundStatus

    payload = get_default_refund_payload("JD_ORDER_001", "JD_REF_001", JdRefundStatus.APPLIED)
    assert payload["order_id"] == "JD_ORDER_001"
    assert payload["refund_id"] == "JD_REF_001"
    assert payload["status"] == "applied"


def test_jd_push_payload():
    from app.platforms.jd.profile import get_default_push_payload

    payload = get_default_push_payload("order_status_changed", "JD_ORDER_001")
    assert payload["event_type"] == "order_status_changed"
    assert payload["order_id"] == "JD_ORDER_001"


def test_jd_basic_order_scenario():
    from app.platforms.jd.profile import ORDER_SCENARIOS

    scenario = ORDER_SCENARIOS["basic_order"]
    assert scenario["initial_order_status"] == "created"
    assert len(scenario["steps"]) == 1
    assert scenario["steps"][0]["action"] == "pay"


def test_jd_full_flow_scenario():
    from app.platforms.jd.profile import ORDER_SCENARIOS

    scenario = ORDER_SCENARIOS["full_flow"]
    assert scenario["initial_order_status"] == "created"
    assert len(scenario["steps"]) == 3
    assert scenario["steps"][0]["action"] == "pay"
    assert scenario["steps"][1]["action"] == "ship"
    assert scenario["steps"][2]["action"] == "receive"
