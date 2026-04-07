import socket

import pytest
from fastapi.testclient import TestClient


def _official_sim_available():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect(("localhost", 8001))
        return True
    except (ConnectionRefusedError, OSError):
        return False
    finally:
        s.close()


@pytest.fixture
def client():
    from app.main import app as domain_app

    with TestClient(domain_app) as test_client:
        yield test_client


class TestHealthEndpoint:
    def test_healthz(self, client: TestClient):
        response = client.get("/healthz")

        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        assert response.json()["service"] == "domain-service"


class TestOrdersAPI:
    @pytest.mark.skipif(not _official_sim_available(), reason="official-sim server not running")
    def test_get_order_not_found(self, client: TestClient):
        response = client.get("/api/orders/taobao/NONEXISTENT_ORDER")

        assert response.status_code == 404


class TestShipmentsAPI:
    @pytest.mark.skipif(not _official_sim_available(), reason="official-sim server not running")
    def test_get_shipment_not_found(self, client: TestClient):
        response = client.get("/api/shipments/taobao/NONEXISTENT_ORDER")

        assert response.status_code == 404


class TestAfterSalesAPI:
    @pytest.mark.skipif(not _official_sim_available(), reason="official-sim server not running")
    def test_get_after_sale_not_found(self, client: TestClient):
        response = client.get("/api/after-sales/taobao/NONEXISTENT_ID")

        assert response.status_code == 404


class TestContextAPI:
    def test_build_context(self, client: TestClient):
        response = client.post(
            "/api/context/build",
            json={
                "platform": "taobao",
                "biz_id": "TEST_ORDER_001",
                "biz_type": "order",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "0"
        assert "data" in data


class TestConversationsAPI:
    def test_list_conversations_has_items(self, client: TestClient):
        response = client.get("/api/conversations/")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "0"
        assert data["data"]["total"] >= 1
        assert len(data["data"]["items"]) >= 1

    def test_get_conversation_recommendations(self, client: TestClient):
        response = client.get("/api/conversations/CONV_WK_001/recommendations")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestRecommendationsAPI:
    def test_get_reply_recommendations(self, client: TestClient):
        response = client.post(
            "/api/recommendations/reply",
            json={
                "platform": "taobao",
                "biz_id": "TEST_ORDER_001",
                "biz_type": "order",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "0"
        assert "candidates" in data["data"]


class TestQualityAPI:
    def test_check_reply(self, client: TestClient):
        response = client.post(
            "/api/quality/check-reply",
            json={
                "reply_content": "您好，请问有什么可以帮您的？",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "0"
        assert "score" in data["data"]

    def test_check_reply_short(self, client: TestClient):
        response = client.post(
            "/api/quality/check-reply",
            json={
                "reply_content": "好的",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["score"] < 100

    def test_get_quality_results(self, client: TestClient):
        response = client.get("/api/quality/results")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "0"
        assert isinstance(data["data"]["items"], list)

    def test_get_quality_alerts(self, client: TestClient):
        response = client.get("/api/quality/alerts")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "0"
        assert isinstance(data["data"]["items"], list)


class TestRiskAPI:
    def test_check_order(self, client: TestClient):
        response = client.post(
            "/api/risk/check-order",
            json={
                "order_data": {
                    "order_id": "TEST_001",
                    "status": "wait_ship",
                    "total_amount": "299.00",
                },
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "0"
        assert "level" in data["data"]

    def test_get_rules(self, client: TestClient):
        response = client.get("/api/risk/rules")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "0"
        assert "rules" in data["data"]

    def test_get_risk_cases(self, client: TestClient):
        response = client.get("/api/risk/cases")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "0"
        assert isinstance(data["data"]["items"], list)

    def test_get_risk_blacklist(self, client: TestClient):
        response = client.get("/api/risk/blacklist")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "0"
        assert isinstance(data["data"]["items"], list)


class TestCompatRoutesAPI:
    def test_get_management_voc_topics(self, client: TestClient):
        response = client.get("/api/management/voc-topics")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "0"
        assert isinstance(data["data"]["items"], list)

    def test_get_customer_profile(self, client: TestClient):
        response = client.get("/api/customers/1/profile")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "0"
        assert data["data"]["customer_id"] == 1

    def test_get_kb_documents(self, client: TestClient):
        response = client.get("/api/kb/documents")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "0"
        assert isinstance(data["data"]["items"], list)
