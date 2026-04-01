import pytest
from fastapi.testclient import TestClient


def test_report_empty_run(client: TestClient):
    create_response = client.post(
        "/official-sim/runs",
        json={"platform": "taobao", "scenario_name": "wait_ship_basic"},
    )
    run_id = create_response.json()["run_id"]

    report_response = client.get(f"/official-sim/runs/{run_id}/report")
    assert report_response.status_code == 200
    data = report_response.json()
    assert data["run_id"] == run_id
    assert data["platform"] == "taobao"
    assert data["total_steps"] == 0
    assert data["total_artifacts"] == 0
    assert data["total_pushes"] == 0
    assert data["total_errors"] == 0


def test_report_after_advance(client: TestClient):
    create_response = client.post(
        "/official-sim/runs",
        json={"platform": "taobao", "scenario_name": "wait_ship_basic"},
    )
    run_id = create_response.json()["run_id"]

    client.post(f"/official-sim/runs/{run_id}/advance", json={})

    report_response = client.get(f"/official-sim/runs/{run_id}/report")
    assert report_response.status_code == 200
    data = report_response.json()
    assert data["total_steps"] == 1
    assert data["total_artifacts"] >= 1
    assert data["scenario_name"] == "wait_ship_basic"


def test_report_with_errors(client: TestClient):
    create_response = client.post(
        "/official-sim/runs",
        json={"platform": "taobao", "scenario_name": "wait_ship_basic"},
    )
    run_id = create_response.json()["run_id"]

    client.post(f"/official-sim/runs/{run_id}/advance", json={})
    client.post(
        f"/official-sim/runs/{run_id}/inject-error",
        json={"error_code": "token_expired"},
    )

    report_response = client.get(f"/official-sim/runs/{run_id}/report")
    assert report_response.status_code == 200
    data = report_response.json()
    assert data["total_errors"] == 1
    assert len(data["errors"]) == 1
    assert data["errors"][0]["error_code"] == "token_expired"


def test_report_not_found(client: TestClient):
    report_response = client.get(
        "/official-sim/runs/00000000-0000-0000-0000-000000000000/report"
    )
    assert report_response.status_code == 404


def test_report_full_flow(client: TestClient):
    create_response = client.post(
        "/official-sim/runs",
        json={"platform": "taobao", "scenario_name": "full_flow"},
    )
    run_id = create_response.json()["run_id"]

    for _ in range(3):
        client.post(f"/official-sim/runs/{run_id}/advance", json={})

    report_response = client.get(f"/official-sim/runs/{run_id}/report")
    assert report_response.status_code == 200
    data = report_response.json()
    assert data["total_steps"] == 3
    assert len(data["steps"]) == 3
    assert data["scenario_name"] == "full_flow"


def test_report_with_pushes(client: TestClient):
    create_response = client.post(
        "/official-sim/runs",
        json={"platform": "taobao", "scenario_name": "wait_ship_basic"},
    )
    run_id = create_response.json()["run_id"]

    client.post(f"/official-sim/runs/{run_id}/advance", json={})

    report_response = client.get(f"/official-sim/runs/{run_id}/report")
    assert report_response.status_code == 200
    data = report_response.json()
    assert data["total_pushes"] >= 0
    assert isinstance(data["artifacts"], list)
