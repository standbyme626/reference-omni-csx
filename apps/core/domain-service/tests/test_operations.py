"""Tests for operations routes: risk_flags, audit_logs, followup_tasks, campaigns, tags."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from app.main import app

    return TestClient(app)


class TestRiskFlags:
    def test_list_risk_flags(self, client):
        response = client.get("/api/risk-flags")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "items" in data["data"]

    def test_list_risk_flags_filter_by_status(self, client):
        response = client.get("/api/risk-flags?status=active")
        assert response.status_code == 200

    def test_list_risk_flags_filter_by_customer(self, client):
        response = client.get("/api/risk-flags?customer_id=1")
        assert response.status_code == 200

    def test_create_risk_flag(self, client):
        payload = {
            "customer_id": 10,
            "conversation_id": 20,
            "risk_type": "test_risk",
            "risk_level": "low",
            "description": "Test risk flag",
        }
        response = client.post("/api/risk-flags", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["customer_id"] == 10
        assert data["data"]["status"] == "active"

    def test_resolve_risk_flag(self, client):
        response = client.post("/api/risk-flags/1/resolve")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["status"] == "resolved"

    def test_dismiss_risk_flag(self, client):
        response = client.post("/api/risk-flags/1/dismiss")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["status"] == "dismissed"


class TestAuditLogs:
    def test_list_audit_logs(self, client):
        response = client.get("/api/audit-logs")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "items" in data["data"]

    def test_list_audit_logs_filter_by_entity_type(self, client):
        response = client.get("/api/audit-logs?entity_type=platform")
        assert response.status_code == 200

    def test_list_audit_logs_filter_by_entity_id(self, client):
        response = client.get("/api/audit-logs?entity_id=jd")
        assert response.status_code == 200

    def test_create_audit_log(self, client):
        payload = {
            "action": "test_action",
            "actor_type": "agent",
            "actor_id": "test_agent",
            "target_type": "order",
            "target_id": "ORDER_001",
            "detail": "Test audit log",
        }
        response = client.post("/api/audit-logs", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["action"] == "test_action"


class TestFollowupTasks:
    def test_list_followup_tasks(self, client):
        response = client.get("/api/follow-up/tasks")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "items" in data["data"]

    def test_list_followup_tasks_filter_by_status(self, client):
        response = client.get("/api/follow-up/tasks?status=pending")
        assert response.status_code == 200

    def test_list_followup_tasks_filter_by_conversation(self, client):
        response = client.get("/api/follow-up/tasks?conversation_id=CONV_WK_001")
        assert response.status_code == 200

    def test_list_followup_tasks_pagination(self, client):
        response = client.get("/api/follow-up/tasks?page=1&size=10")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["page"] == 1
        assert data["data"]["size"] == 10

    def test_close_followup_task(self, client):
        response = client.post("/api/follow-up/tasks/FOLLOW_001/close")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["status"] == "closed"

    def test_execute_followup_task(self, client):
        response = client.post("/api/follow-up/tasks/FOLLOW_001/execute")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["status"] == "completed"


class TestCampaigns:
    def test_list_campaigns(self, client):
        response = client.get("/api/operation-campaigns")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert data["data"]["total"] == 3


class TestTags:
    def test_list_tags(self, client):
        response = client.get("/api/tags")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    def test_list_tags_filter_by_category(self, client):
        response = client.get("/api/tags?category=customer")
        assert response.status_code == 200
        data = response.json()
        assert all(t["category"] == "customer" for t in data["data"]["items"])
