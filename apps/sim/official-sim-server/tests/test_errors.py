import pytest
from fastapi.testclient import TestClient


def test_inject_error_token_expired(client: TestClient):
    create_response = client.post(
        "/official-sim/runs",
        json={
            "platform": "taobao",
            "scenario_name": "wait_ship_basic",
        },
    )
    run_id = create_response.json()["run_id"]

    inject_response = client.post(
        f"/official-sim/runs/{run_id}/inject-error",
        json={"error_code": "token_expired"},
    )
    assert inject_response.status_code == 200
    data = inject_response.json()
    assert data["error_code"] == "token_expired"
    assert data["http_status"] == 401
    assert data["retryable"] is True


def test_inject_error_resource_not_found(client: TestClient):
    create_response = client.post(
        "/official-sim/runs",
        json={
            "platform": "taobao",
            "scenario_name": "wait_ship_basic",
        },
    )
    run_id = create_response.json()["run_id"]

    inject_response = client.post(
        f"/official-sim/runs/{run_id}/inject-error",
        json={"error_code": "resource_not_found"},
    )
    assert inject_response.status_code == 200
    data = inject_response.json()
    assert data["error_code"] == "resource_not_found"
    assert data["http_status"] == 404
    assert data["retryable"] is False


def test_inject_error_unknown_code(client: TestClient):
    create_response = client.post(
        "/official-sim/runs",
        json={
            "platform": "taobao",
            "scenario_name": "wait_ship_basic",
        },
    )
    run_id = create_response.json()["run_id"]

    inject_response = client.post(
        f"/official-sim/runs/{run_id}/inject-error",
        json={"error_code": "unknown_error"},
    )
    assert inject_response.status_code == 400


def test_inject_error_creates_artifact(client: TestClient):
    create_response = client.post(
        "/official-sim/runs",
        json={
            "platform": "taobao",
            "scenario_name": "wait_ship_basic",
        },
    )
    run_id = create_response.json()["run_id"]

    inject_response = client.post(
        f"/official-sim/runs/{run_id}/inject-error",
        json={"error_code": "rate_limited"},
    )
    assert inject_response.status_code == 200
    artifact_id = inject_response.json()["artifact_id"]

    artifacts_response = client.get(f"/official-sim/runs/{run_id}/artifacts")
    assert artifacts_response.status_code == 200
    artifacts = artifacts_response.json()
    error_artifacts = [a for a in artifacts if a["artifact_type"] == "error_response_payload"]
    assert len(error_artifacts) >= 1


def test_inject_error_run_not_found(client: TestClient):
    fake_id = "00000000-0000-0000-0000-000000000000"
    inject_response = client.post(
        f"/official-sim/runs/{fake_id}/inject-error",
        json={"error_code": "token_expired"},
    )
    assert inject_response.status_code == 404
