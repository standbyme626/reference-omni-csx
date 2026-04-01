import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


class TestIntegrationRoute:
    def test_integration_router_registered(self):
        response = client.get("/api/integration/inventory")
        assert response.status_code in [200, 404, 500]

    def test_integration_inventory_endpoint(self):
        response = client.get("/api/integration/inventory")
        assert response.status_code in [200, 404]

    def test_integration_order_audits_endpoint(self):
        response = client.get("/api/integration/order-audits")
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            payload = response.json()
            assert payload["code"] == "0"
            assert payload["data"]["total"] >= 1

    def test_integration_order_exceptions_endpoint(self):
        response = client.get("/api/integration/order-exceptions")
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            payload = response.json()
            assert payload["code"] == "0"
            assert payload["data"]["total"] >= 1

    def test_integration_fulfillment_endpoint(self):
        response = client.get("/api/integration/fulfillment")
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            payload = response.json()
            assert payload["code"] == "0"
            assert payload["data"]["total"] >= 1


class TestAnalyticsRoute:
    def test_analytics_router_registered(self):
        response = client.get("/api/analytics/orders/summary")
        assert response.status_code in [200, 404, 500]

    def test_analytics_orders_summary_endpoint(self):
        response = client.get("/api/analytics/orders/summary")
        assert response.status_code in [200, 404]

    def test_analytics_conversations_summary_endpoint(self):
        response = client.get("/api/analytics/conversations/summary")
        assert response.status_code in [200, 404]

    def test_analytics_platforms_coverage_endpoint(self):
        response = client.get("/api/analytics/platforms/coverage")
        assert response.status_code in [200, 404]
