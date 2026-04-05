import pytest
from fastapi.testclient import TestClient


def test_raw_get_order_matches_explicit_fixture_id(client: TestClient):
    response = client.get("/official-sim/raw/orders/12345678901234?platform=taobao")

    assert response.status_code == 200
    payload = response.json()
    assert payload["source"] == "fixture"
    assert str(payload["data"]["trade"]["tid"]) == "12345678901234"


def test_raw_get_order_not_found_returns_404(client: TestClient):
    response = client.get("/official-sim/raw/orders/NONEXISTENT_ORDER?platform=taobao")

    assert response.status_code == 404


def test_raw_get_order_run_aware_uses_run_status_and_requested_order_id(client: TestClient):
    create_response = client.post(
        "/official-sim/runs",
        json={
            "platform": "taobao",
            "scenario_name": "wait_ship_basic",
        },
    )
    run_id = create_response.json()["run_id"]

    advance_response = client.post(f"/official-sim/runs/{run_id}/advance", json={})
    assert advance_response.status_code == 200

    response = client.get(
        f"/official-sim/raw/orders/TB_ORDER_CTX_001?platform=taobao&run_id={run_id}"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["source"] == "run"
    assert str(payload["data"]["trade"]["tid"]) == "TB_ORDER_CTX_001"
    assert payload["data"]["trade"]["status"] == "WAIT_SELLER_SEND_GOODS"


def test_raw_get_shipment_run_aware_returns_shipment_when_run_is_shipped(client: TestClient):
    create_response = client.post(
        "/official-sim/runs",
        json={
            "platform": "taobao",
            "scenario_name": "shipped_to_finished",
        },
    )
    run_id = create_response.json()["run_id"]

    response = client.get(
        f"/official-sim/raw/shipments/TB_ORDER_SHIP_001?platform=taobao&run_id={run_id}"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["source"] == "run"
    assert payload["data"]["order_id"] == "TB_ORDER_SHIP_001"
    assert payload["data"]["tracking_no"] == "SF1234567890"


@pytest.mark.parametrize(
    ("platform", "order_id", "company", "tracking_no"),
    [
        ("taobao", "12345678901234", "顺丰速运", "SF1234567890"),
        ("douyin_shop", "6912558345648290211", "顺丰速运", "SF1234567890"),
        ("xhs", "XHS12345678901234", "顺丰速运", "SF1234567890"),
        ("kuaishou", "KS12345678901235", "顺丰速运", "SF1234567890"),
    ],
)
def test_raw_get_shipment_fixture_supports_public_order_samples(
    client: TestClient,
    platform: str,
    order_id: str,
    company: str,
    tracking_no: str,
):
    response = client.get(f"/official-sim/raw/shipments/{order_id}?platform={platform}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["source"] == "fixture"
    data = payload["data"]

    if "trade" in data:
        order = data["trade"]["orders"]["order"][0]
        assert order["logistics_company"] == company
        assert order["invoice_no"] == tracking_no
    elif "order" in data:
        order = data["order"]
        logistics = order.get("logistics") or order.get("delivery_info") or {}
        assert (
            logistics.get("logisticsCompany")
            or logistics.get("company")
            or logistics.get("company_name")
        ) == company
        assert (logistics.get("trackingNo") or logistics.get("tracking_no")) == tracking_no
    else:
        pytest.fail(f"unexpected shipment payload: {data}")


@pytest.mark.parametrize(
    ("platform", "order_id", "expected_status"),
    [
        ("taobao", "12345678901234", "WAIT_BUYER_CONFIRM_GOODS"),
        ("douyin_shop", "6912558345648290211", 100),
        ("xhs", "XHS12345678901234", "delivering"),
        ("kuaishou", "KS12345678901235", 4),
    ],
)
def test_raw_get_order_prefers_shipped_fixture_for_public_samples(
    client: TestClient,
    platform: str,
    order_id: str,
    expected_status,
):
    response = client.get(f"/official-sim/raw/orders/{order_id}?platform={platform}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["source"] == "fixture"
    data = payload["data"]

    if "trade" in data:
        assert data["trade"]["status"] == expected_status
    else:
        actual_status = data["order"].get("order_status") or data["order"].get("orderStatus")
        assert actual_status == expected_status


def test_raw_get_order_refunding_alias_still_returns_order_payload(client: TestClient):
    response = client.get("/official-sim/raw/orders/KS_ORDER_003?platform=kuaishou")

    assert response.status_code == 200
    payload = response.json()
    assert payload["source"] == "fixture"
    data = payload["data"]
    assert "order" in data
    assert "refund" not in data
    assert data["order"]["orderId"]


@pytest.mark.parametrize(
    ("platform", "requested_order_id", "expected_external_order_id"),
    [
        ("taobao", "TB_ORDER_001", "12345678901231"),
        ("taobao", "TB_ORDER_002", "12345678901232"),
        ("taobao", "TB_ORDER_003", "12345678901234"),
        ("douyin_shop", "DS_ORDER_001", "6912558345648290201"),
        ("douyin_shop", "DS_ORDER_003", "6912558345648290211"),
        ("jd", "JD_ORDER_001", "98765432101231"),
        ("jd", "JD_ORDER_002", "98765432101237"),
        ("xhs", "XHS_ORDER_001", "XHS12345678901231"),
        ("xhs", "XHS_ORDER_003", "XHS12345678901234"),
        ("kuaishou", "KS_ORDER_001", "KS12345678901231"),
        ("kuaishou", "KS_ORDER_002", "KS12345678901235"),
    ],
)
def test_raw_get_order_alias_returns_unique_official_order_id(
    client: TestClient,
    platform: str,
    requested_order_id: str,
    expected_external_order_id: str,
):
    response = client.get(f"/official-sim/raw/orders/{requested_order_id}?platform={platform}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["source"] == "fixture"
    data = payload["data"]

    if "trade" in data:
        assert str(data["trade"]["tid"]) == expected_external_order_id
    elif "order" in data:
        assert str(data["order"].get("order_id") or data["order"].get("orderId")) == expected_external_order_id
    else:
        assert str(data["jingdong_order_search_responce"]["orderId"]) == expected_external_order_id


def test_raw_get_shipment_known_order_without_shipment_returns_404(client: TestClient):
    response = client.get("/official-sim/raw/shipments/KS12345678901234?platform=kuaishou")

    assert response.status_code == 404


def test_raw_get_after_sale_run_aware_returns_404_when_run_has_no_refund(client: TestClient):
    create_response = client.post(
        "/official-sim/runs",
        json={
            "platform": "taobao",
            "scenario_name": "wait_ship_basic",
        },
    )
    run_id = create_response.json()["run_id"]

    client.post(f"/official-sim/runs/{run_id}/advance", json={})

    response = client.get(
        f"/official-sim/raw/after-sales/TB_ORDER_CTX_001?platform=taobao&run_id={run_id}"
    )

    assert response.status_code == 404


def test_raw_get_after_sale_run_aware_returns_refund_when_run_is_refunding(client: TestClient):
    create_response = client.post(
        "/official-sim/runs",
        json={
            "platform": "jd",
            "scenario_name": "refund_flow",
        },
    )
    run_id = create_response.json()["run_id"]

    advance_response = client.post(f"/official-sim/runs/{run_id}/advance", json={})
    assert advance_response.status_code == 200

    response = client.get(
        f"/official-sim/raw/after-sales/JD_AFTER_SALE_001?platform=jd&run_id={run_id}"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["source"] == "run"
    assert payload["data"]["after_sale"]["order_id"] == "JD_AFTER_SALE_001"
    assert payload["data"]["after_sale"]["status"] == "refunding"
    assert payload["data"]["after_sale"]["after_sale_id"] == "jd:JD_AFTER_SALE_001:after_sale"


def test_raw_get_after_sale_by_order_returns_fixture_refund_with_stable_identifier(client: TestClient):
    response = client.get("/official-sim/raw/after-sales/by-order/TB_ORDER_003?platform=taobao")

    assert response.status_code == 200
    payload = response.json()
    assert payload["source"] == "fixture"
    after_sale = payload["data"]["after_sale"]
    assert after_sale["order_id"] == "TB_ORDER_003"
    assert after_sale["external_order_id"] == "12345678901234"
    assert after_sale["status"] == "refunding"
    assert after_sale["after_sale_id"] == "taobao:12345678901234:after_sale"
    assert after_sale["requested_order_id"] == "TB_ORDER_003"


def test_raw_get_after_sale_accepts_canonical_identifier(client: TestClient):
    response = client.get(
        "/official-sim/raw/after-sales/taobao:12345678901234:after_sale?platform=taobao"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["source"] == "fixture"
    after_sale = payload["data"]["after_sale"]
    assert after_sale["after_sale_id"] == "taobao:12345678901234:after_sale"
    assert after_sale["order_id"] == "TB_ORDER_003"
    assert after_sale["external_order_id"] == "12345678901234"


def test_raw_list_conversations_run_aware_includes_user_sim_run(client: TestClient):
    create_response = client.post(
        "/official-sim/runs",
        json={
            "platform": "wecom_kf",
            "scenario_name": "basic_session",
            "metadata": {
                "conversation_id": "conv_run_001",
                "order_id": "JD_ORDER_001",
                "user_id": "wecom_user_001",
            },
        },
    )
    run_id = create_response.json()["run_id"]

    artifact_response = client.post(
        f"/official-sim/runs/{run_id}/artifacts",
        json={
            "artifact_kind": "conversation_turn_payload",
            "turn_no": 1,
            "payload": {
                "conversation_id": "conv_run_001",
                "user_id": "wecom_user_001",
                "order_id": "JD_ORDER_001",
                "user_message": "我的订单怎么还没发货？",
                "reply_message": "正在为您查询发货状态。",
                "reply_source": "domain-service",
                "conversation_status": "running",
            },
        },
    )
    assert artifact_response.status_code == 201

    response = client.get("/official-sim/raw/conversations?platform=wecom_kf")

    assert response.status_code == 200
    payload = response.json()
    assert payload["source"] == "run"
    assert payload["data"]["total"] >= 1
    items = payload["data"]["items"]
    matched = [item for item in items if item["conversation_id"] == "conv_run_001"]
    assert matched
    assert matched[0]["official_run_id"] == run_id
    assert matched[0]["biz_id"] == "JD_ORDER_001"


def test_raw_get_conversation_and_messages_run_aware_reconstructs_turns(client: TestClient):
    create_response = client.post(
        "/official-sim/runs",
        json={
            "platform": "wecom_kf",
            "scenario_name": "basic_session",
            "metadata": {
                "conversation_id": "conv_run_002",
                "order_id": "JD_ORDER_002",
                "user_id": "wecom_user_002",
            },
        },
    )
    run_id = create_response.json()["run_id"]

    user_msg = client.post(
        f"/official-sim/runs/{run_id}/artifacts",
        json={
            "artifact_kind": "user_message_payload",
            "turn_no": 1,
            "payload": {
                "conversation_id": "conv_run_002",
                "user_id": "wecom_user_002",
                "order_id": "JD_ORDER_002",
                "user_message": "我要退款",
                "intent": "ask_refund",
                "emotion": "impatient",
            },
        },
    )
    assert user_msg.status_code == 201

    turn_payload = client.post(
        f"/official-sim/runs/{run_id}/artifacts",
        json={
            "artifact_kind": "conversation_turn_payload",
            "turn_no": 1,
            "payload": {
                "conversation_id": "conv_run_002",
                "user_id": "wecom_user_002",
                "order_id": "JD_ORDER_002",
                "user_message": "我要退款",
                "reply_message": "已为您登记退款申请。",
                "reply_source": "domain-service",
                "conversation_status": "running",
            },
        },
    )
    assert turn_payload.status_code == 201

    conversation_response = client.get(
        f"/official-sim/raw/conversations/conv_run_002?platform=wecom_kf&run_id={run_id}"
    )
    assert conversation_response.status_code == 200
    conversation_payload = conversation_response.json()
    assert conversation_payload["source"] == "run"
    assert conversation_payload["data"]["conversation_id"] == "conv_run_002"
    assert conversation_payload["data"]["official_run_id"] == run_id
    assert conversation_payload["data"]["biz_id"] == "JD_ORDER_002"
    assert conversation_payload["data"]["message_count"] == 2

    messages_response = client.get(
        f"/official-sim/raw/conversations/conv_run_002/messages?platform=wecom_kf&run_id={run_id}"
    )
    assert messages_response.status_code == 200
    messages_payload = messages_response.json()
    assert messages_payload["source"] == "run"
    assert messages_payload["data"]["conversation_id"] == "conv_run_002"
    assert messages_payload["data"]["total"] == 2
    assert messages_payload["data"]["messages"][0]["sender_type"] == "customer"
    assert messages_payload["data"]["messages"][0]["content"] == "我要退款"
    assert messages_payload["data"]["messages"][1]["sender_type"] == "agent"
    assert messages_payload["data"]["messages"][1]["content"] == "已为您登记退款申请。"
