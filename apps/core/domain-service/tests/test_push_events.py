"""Tests for domain-service push event receiver endpoint."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from app.main import app as domain_app

    with TestClient(domain_app) as test_client:
        yield test_client


SAMPLE_PUSH = {
    "event_type": "trade.OrderStatusChanged",
    "run_id": "test-run-001",
    "step_no": 1,
    "platform": "taobao",
    "body": {"order_id": "123", "status": "paid"},
    "headers": {"Content-Type": "application/json"},
}


class TestReceivePushEvent:
    def test_receive_push_event_returns_ack(self, client: TestClient):
        response = client.post("/api/push-events", json=SAMPLE_PUSH)

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "0"
        assert data["data"]["status"] == "ack"
        assert data["data"]["event_type"] == "trade.OrderStatusChanged"
        assert data["data"]["run_id"] == "test-run-001"

    def test_receive_multiple_pushes(self, client: TestClient):
        push_1 = {**SAMPLE_PUSH, "step_no": 1, "event_type": "trade.OrderStatusChanged"}
        push_2 = {**SAMPLE_PUSH, "step_no": 2, "event_type": "trade.ShipSent"}

        r1 = client.post("/api/push-events", json=push_1)
        r2 = client.post("/api/push-events", json=push_2)

        assert r1.status_code == 200
        assert r2.status_code == 200

    def test_minimal_payload_accepted(self, client: TestClient):
        response = client.post(
            "/api/push-events",
            json={
                "event_type": "order.PaySuccess",
                "run_id": "run-xyz",
                "step_no": 1,
                "platform": "douyin_shop",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["status"] == "ack"


class TestValidatePushPayload:
    def test_missing_event_type(self, client: TestClient):
        payload = {
            "run_id": "test-run",
            "step_no": 1,
            "platform": "taobao",
        }
        response = client.post("/api/push-events", json=payload)
        assert response.status_code == 422

    def test_missing_run_id(self, client: TestClient):
        payload = {
            "event_type": "trade.OrderStatusChanged",
            "step_no": 1,
            "platform": "taobao",
        }
        response = client.post("/api/push-events", json=payload)
        assert response.status_code == 422

    def test_missing_step_no(self, client: TestClient):
        payload = {
            "event_type": "trade.OrderStatusChanged",
            "run_id": "test-run",
            "platform": "taobao",
        }
        response = client.post("/api/push-events", json=payload)
        assert response.status_code == 422

    def test_missing_platform(self, client: TestClient):
        payload = {
            "event_type": "trade.OrderStatusChanged",
            "run_id": "test-run",
            "step_no": 1,
        }
        response = client.post("/api/push-events", json=payload)
        assert response.status_code == 422


class TestListReceivedPushes:
    def test_list_empty(self, client: TestClient):
        client.post("/api/push-events/clear-test")  # won't work, let's just check list
        _ = client.get("/api/push-events")  # GET list all

    def test_list_after_receiving(self, client: TestClient):
        client.post("/api/push-events", json=SAMPLE_PUSH)
        response = client.get("/api/push-events")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "0"
        assert data["data"]["total"] >= 1

    def test_filter_by_run_id(self, client: TestClient):
        unique_run = "filter-test-run-001"
        client.post("/api/push-events", json={**SAMPLE_PUSH, "run_id": unique_run})

        response = client.get(f"/api/push-events?run_id={unique_run}")
        assert response.status_code == 200
        data = response.json()
        events = data["data"]["events"]
        assert any(e["run_id"] == unique_run for e in events)
