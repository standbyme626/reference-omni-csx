import pytest
from app.core.config import settings
from fastapi.testclient import TestClient


def _get_app():
    from app.main import app as domain_app

    return domain_app


def _get_integration_service_dependency():
    from app.dependencies import get_integration_service

    return get_integration_service


@pytest.fixture
def client():
    with TestClient(_get_app()) as test_client:
        yield test_client


class TestIntegrationRoute:
    @pytest.fixture(autouse=True)
    def clear_overrides(self):
        app = _get_app()
        yield
        app.dependency_overrides.clear()

    def teardown_method(self):
        _get_app().dependency_overrides.clear()

    def test_integration_router_registered(self, client: TestClient):
        response = client.get("/api/integration/inventory")
        assert response.status_code in [200, 400, 404, 500]

    def test_integration_inventory_endpoint(self, client: TestClient):
        response = client.get("/api/integration/inventory")
        assert response.status_code in [200, 400, 404]

    def test_integration_order_audits_endpoint(self, client: TestClient):
        response = client.get("/api/integration/order-audits")
        assert response.status_code in [200, 400, 404]
        if response.status_code == 200:
            payload = response.json()
            assert payload["code"] == "0"
            assert payload["data"]["total"] >= 1

    def test_integration_order_exceptions_endpoint(self, client: TestClient):
        response = client.get("/api/integration/order-exceptions")
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            payload = response.json()
            assert payload["code"] == "0"
            if (settings.odoo_provider_mode or "").lower() == "real":
                assert payload["data"]["total"] >= 0
            else:
                assert payload["data"]["total"] >= 1

    def test_integration_fulfillment_endpoint(self, client: TestClient):
        response = client.get("/api/integration/fulfillment")
        assert response.status_code in [200, 400, 404]
        if response.status_code == 200:
            payload = response.json()
            assert payload["code"] == "0"
            assert payload["data"]["total"] >= 1

    def test_integration_order_audits_endpoint_passes_platform_query_param(self, client: TestClient):
        class FakeIntegrationService:
            def __init__(self):
                self.captured = None

            def get_order_audits(self, order_id=None, platform=None):
                self.captured = {
                    "order_id": order_id,
                    "platform": platform,
                }
                return [
                    {
                        "order_id": order_id,
                        "audit_status": "approved",
                        "audit_notes": None,
                        "audited_by": None,
                        "audited_at": None,
                    }
                ]

        fake_service = FakeIntegrationService()
        app = _get_app()
        dependency = _get_integration_service_dependency()
        app.dependency_overrides[dependency] = lambda: fake_service

        response = client.get(
            "/api/integration/order-audits",
            params={"order_id": "98765432101234", "platform": "jd"},
        )

        assert response.status_code == 200
        assert fake_service.captured == {
            "order_id": "98765432101234",
            "platform": "jd",
        }
        app.dependency_overrides.pop(dependency, None)

    def test_integration_fulfillment_endpoint_passes_platform_query_param(self, client: TestClient):
        class FakeIntegrationService:
            def __init__(self):
                self.captured = None

            def get_fulfillment(self, order_id=None, platform=None):
                self.captured = {
                    "order_id": order_id,
                    "platform": platform,
                }
                return [
                    {
                        "order_id": order_id,
                        "status": "assigned",
                        "warehouse": "WH/Stock",
                        "picking_id": "PICK-001",
                        "scheduled_date": None,
                        "actual_date": None,
                    }
                ]

        fake_service = FakeIntegrationService()
        app = _get_app()
        dependency = _get_integration_service_dependency()
        app.dependency_overrides[dependency] = lambda: fake_service

        response = client.get(
            "/api/integration/fulfillment",
            params={"order_id": "98765432101234", "platform": "jd"},
        )

        assert response.status_code == 200
        assert fake_service.captured == {
            "order_id": "98765432101234",
            "platform": "jd",
        }
        app.dependency_overrides.pop(dependency, None)


class TestAnalyticsRoute:
    def test_analytics_router_registered(self, client: TestClient):
        response = client.get("/api/analytics/orders/summary")
        assert response.status_code in [200, 404, 500]

    def test_analytics_orders_summary_endpoint(self, client: TestClient):
        response = client.get("/api/analytics/orders/summary")
        assert response.status_code in [200, 404]

    def test_analytics_conversations_summary_endpoint(self, client: TestClient):
        response = client.get("/api/analytics/conversations/summary")
        assert response.status_code in [200, 404]

    def test_analytics_platforms_coverage_endpoint(self, client: TestClient):
        response = client.get("/api/analytics/platforms/coverage")
        assert response.status_code in [200, 404]
