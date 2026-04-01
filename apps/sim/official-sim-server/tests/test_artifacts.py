import pytest
from fastapi.testclient import TestClient
from uuid import UUID


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
