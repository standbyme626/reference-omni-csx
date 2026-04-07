"""Tests for analytics routes."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from app.main import app

    return TestClient(app)


class TestAnalyticsRoute:
    def test_analytics_summaries_endpoint(self, client):
        response = client.get("/api/analytics/summaries")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    def test_analytics_orders_summary_endpoint(self, client):
        response = client.get("/api/analytics/orders/summary")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    def test_analytics_conversations_summary_endpoint(self, client):
        response = client.get("/api/analytics/conversations/summary")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    def test_analytics_platforms_coverage_endpoint(self, client):
        response = client.get("/api/analytics/platforms/coverage")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
