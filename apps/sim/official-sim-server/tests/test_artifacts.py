from fastapi.testclient import TestClient


def test_list_artifacts_empty(client: TestClient):
    create_response = client.post(
        "/official-sim/runs",
        json={
            "platform": "taobao",
            "scenario_name": "wait_ship_basic",
        },
    )
    run_id = create_response.json()["run_id"]

    artifacts_response = client.get(f"/official-sim/runs/{run_id}/artifacts")
    assert artifacts_response.status_code == 200
    artifacts = artifacts_response.json()
    assert artifacts == []


def test_list_artifacts_with_data(client: TestClient):
    create_response = client.post(
        "/official-sim/runs",
        json={
            "platform": "taobao",
            "scenario_name": "wait_ship_basic",
        },
    )
    run_id = create_response.json()["run_id"]

    client.post(f"/official-sim/runs/{run_id}/advance", json={})

    artifacts_response = client.get(f"/official-sim/runs/{run_id}/artifacts")
    assert artifacts_response.status_code == 200


def test_list_artifacts_filter_by_step(client: TestClient):
    create_response = client.post(
        "/official-sim/runs",
        json={
            "platform": "taobao",
            "scenario_name": "wait_ship_basic",
        },
    )
    run_id = create_response.json()["run_id"]

    client.post(f"/official-sim/runs/{run_id}/advance", json={})
    client.post(f"/official-sim/runs/{run_id}/advance", json={})

    artifacts_step1 = client.get(f"/official-sim/runs/{run_id}/artifacts?step_no=1")
    assert artifacts_step1.status_code == 200

    artifacts_step2 = client.get(f"/official-sim/runs/{run_id}/artifacts?step_no=2")
    assert artifacts_step2.status_code == 200


def test_list_pushes_empty(client: TestClient):
    create_response = client.post(
        "/official-sim/runs",
        json={
            "platform": "taobao",
            "scenario_name": "wait_ship_basic",
        },
    )
    run_id = create_response.json()["run_id"]

    pushes_response = client.get(f"/official-sim/runs/{run_id}/pushes")
    assert pushes_response.status_code == 200
    pushes = pushes_response.json()
    assert pushes == []


def test_list_pushes_not_found(client: TestClient):
    fake_id = "00000000-0000-0000-0000-000000000000"
    pushes_response = client.get(f"/official-sim/runs/{fake_id}/pushes")
    assert pushes_response.status_code == 404


def test_replay_push_not_found(client: TestClient):
    create_response = client.post(
        "/official-sim/runs",
        json={
            "platform": "taobao",
            "scenario_name": "wait_ship_basic",
        },
    )
    run_id = create_response.json()["run_id"]

    fake_push_id = "00000000-0000-0000-0000-000000000000"
    replay_response = client.post(
        f"/official-sim/runs/{run_id}/replay-push",
        json={"push_id": fake_push_id},
    )
    assert replay_response.status_code == 404


def test_advance_run_creates_artifact(client: TestClient):
    create_response = client.post(
        "/official-sim/runs",
        json={
            "platform": "taobao",
            "scenario_name": "wait_ship_basic",
        },
    )
    run_id = create_response.json()["run_id"]

    client.post(f"/official-sim/runs/{run_id}/advance", json={})

    artifacts_response = client.get(f"/official-sim/runs/{run_id}/artifacts")
    assert artifacts_response.status_code == 200
    artifacts = artifacts_response.json()
    assert isinstance(artifacts, list)


def test_create_user_sim_artifacts_and_query(client: TestClient):
    create_response = client.post(
        "/official-sim/runs",
        json={
            "platform": "taobao",
            "scenario_name": "wait_ship_basic",
        },
    )
    run_id = create_response.json()["run_id"]

    user_msg = client.post(
        f"/official-sim/runs/{run_id}/artifacts",
        json={
            "artifact_kind": "user_message_payload",
            "turn_no": 1,
            "payload": {
                "text": "我要退款",
                "intent": "ask_refund",
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
                "user_message": "我要退款",
                "reply_message": "已为您处理退款申请",
            },
        },
    )
    assert turn_payload.status_code == 201

    reco_payload = client.post(
        f"/official-sim/runs/{run_id}/artifacts",
        json={
            "artifact_kind": "reply_recommendation_payload",
            "turn_no": 1,
            "payload": {
                "reply_type": "after_sale_status",
                "confidence": 0.92,
            },
        },
    )
    assert reco_payload.status_code == 201

    all_artifacts = client.get(f"/official-sim/runs/{run_id}/artifacts")
    assert all_artifacts.status_code == 200
    route_keys = {a.get("route_key") for a in all_artifacts.json()}
    assert "user_message_payload" in route_keys
    assert "conversation_turn_payload" in route_keys
    assert "reply_recommendation_payload" in route_keys

    filtered = client.get(
        f"/official-sim/runs/{run_id}/artifacts",
        params={"route_key": "user_message_payload"},
    )
    assert filtered.status_code == 200
    assert all(item.get("route_key") == "user_message_payload" for item in filtered.json())


def test_create_user_sim_artifact_also_records_structured_event(client: TestClient):
    create_response = client.post(
        "/official-sim/runs",
        json={
            "platform": "wecom_kf",
            "scenario_name": "basic_session",
        },
    )
    run_id = create_response.json()["run_id"]

    artifact_response = client.post(
        f"/official-sim/runs/{run_id}/artifacts",
        json={
            "artifact_kind": "user_message_payload",
            "turn_no": 1,
            "payload": {
                "conversation_id": "conv_evt_001",
                "user_message": "订单还没发货",
                "intent": "ask_shipment",
            },
        },
    )
    assert artifact_response.status_code == 201

    events_response = client.get(f"/official-sim/runs/{run_id}/events")
    assert events_response.status_code == 200
    events = events_response.json()
    matched = [event for event in events if event["event_type"] == "user_message_payload"]
    assert matched
    assert matched[0]["source_type"] == "user_sim_artifact"
    assert matched[0]["payload"]["conversation_id"] == "conv_evt_001"
