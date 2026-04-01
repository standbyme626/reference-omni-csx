import pytest
from fastapi.testclient import TestClient


def test_wecom_basic_session(client: TestClient):
    create_response = client.post(
        "/official-sim/runs",
        json={
            "platform": "wecom_kf",
            "scenario_name": "basic_session",
        },
    )
    assert create_response.status_code == 201
    run_id = create_response.json()["run_id"]

    advance = client.post(f"/official-sim/runs/{run_id}/advance", json={})
    assert advance.status_code == 200
    assert advance.json()["current_step"] == 1


def test_wecom_full_session(client: TestClient):
    create_response = client.post(
        "/official-sim/runs",
        json={
            "platform": "wecom_kf",
            "scenario_name": "full_session",
        },
    )
    assert create_response.status_code == 201
    run_id = create_response.json()["run_id"]

    advance1 = client.post(f"/official-sim/runs/{run_id}/advance", json={})
    assert advance1.status_code == 200
    assert advance1.json()["current_step"] == 1

    advance2 = client.post(f"/official-sim/runs/{run_id}/advance", json={})
    assert advance2.status_code == 200
    assert advance2.json()["current_step"] == 2


def test_wecom_session_expired(client: TestClient):
    create_response = client.post(
        "/official-sim/runs",
        json={
            "platform": "wecom_kf",
            "scenario_name": "session_expired",
        },
    )
    assert create_response.status_code == 201
    run_id = create_response.json()["run_id"]

    advance = client.post(f"/official-sim/runs/{run_id}/advance", json={})
    assert advance.status_code == 200


def test_wecom_advance_creates_artifacts(client: TestClient):
    create_response = client.post(
        "/official-sim/runs",
        json={
            "platform": "wecom_kf",
            "scenario_name": "basic_session",
        },
    )
    run_id = create_response.json()["run_id"]

    client.post(f"/official-sim/runs/{run_id}/advance", json={})

    artifacts_response = client.get(f"/official-sim/runs/{run_id}/artifacts")
    assert artifacts_response.status_code == 200
    artifacts = artifacts_response.json()
    assert len(artifacts) >= 2


def test_wecom_callback_artifact(client: TestClient):
    create_response = client.post(
        "/official-sim/runs",
        json={
            "platform": "wecom_kf",
            "scenario_name": "basic_session",
        },
    )
    run_id = create_response.json()["run_id"]

    client.post(f"/official-sim/runs/{run_id}/advance", json={})

    artifacts_response = client.get(f"/official-sim/runs/{run_id}/artifacts?step_no=1")
    assert artifacts_response.status_code == 200
    artifacts = artifacts_response.json()
    assert len(artifacts) >= 1


def test_wecom_scenario_in_metadata(client: TestClient):
    create_response = client.post(
        "/official-sim/runs",
        json={
            "platform": "wecom_kf",
            "scenario_name": "full_session",
        },
    )
    run_id = create_response.json()["run_id"]

    run_response = client.get(f"/official-sim/runs/{run_id}")
    run_data = run_response.json()
    assert run_data["metadata"]["scenario_name"] == "full_session"


def test_wecom_msg_code_expired_error(client: TestClient):
    create_response = client.post(
        "/official-sim/runs",
        json={
            "platform": "wecom_kf",
            "scenario_name": "basic_session",
        },
    )
    run_id = create_response.json()["run_id"]

    inject_response = client.post(
        f"/official-sim/runs/{run_id}/inject-error",
        json={"error_code": "msg_code_expired"},
    )
    assert inject_response.status_code == 200
    data = inject_response.json()
    assert data["error_code"] == "msg_code_expired"
    assert data["http_status"] == 400
    assert data["retryable"] is True


def test_wecom_conversation_closed_error(client: TestClient):
    create_response = client.post(
        "/official-sim/runs",
        json={
            "platform": "wecom_kf",
            "scenario_name": "basic_session",
        },
    )
    run_id = create_response.json()["run_id"]

    inject_response = client.post(
        f"/official-sim/runs/{run_id}/inject-error",
        json={"error_code": "conversation_closed"},
    )
    assert inject_response.status_code == 200
    data = inject_response.json()
    assert data["error_code"] == "conversation_closed"
    assert data["http_status"] == 410


def test_wecom_permission_denied_error(client: TestClient):
    create_response = client.post(
        "/official-sim/runs",
        json={
            "platform": "wecom_kf",
            "scenario_name": "basic_session",
        },
    )
    run_id = create_response.json()["run_id"]

    inject_response = client.post(
        f"/official-sim/runs/{run_id}/inject-error",
        json={"error_code": "permission_denied"},
    )
    assert inject_response.status_code == 200
    data = inject_response.json()
    assert data["error_code"] == "permission_denied"
    assert data["http_status"] == 403
