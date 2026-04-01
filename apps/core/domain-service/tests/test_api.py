import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


class TestHealthEndpoint:
    def test_healthz(self):
        response = client.get("/healthz")
        
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        assert response.json()["service"] == "domain-service"


class TestOrdersAPI:
    def test_get_order_not_found(self):
        response = client.get("/api/orders/taobao/NONEXISTENT_ORDER")
        
        assert response.status_code == 404


class TestShipmentsAPI:
    def test_get_shipment_not_found(self):
        response = client.get("/api/shipments/taobao/NONEXISTENT_ORDER")
        
        assert response.status_code == 404


class TestAfterSalesAPI:
    def test_get_after_sale_not_found(self):
        response = client.get("/api/after-sales/taobao/NONEXISTENT_ID")
        
        assert response.status_code == 404


class TestContextAPI:
    def test_build_context(self):
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


class TestRecommendationsAPI:
    def test_get_reply_recommendations(self):
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
    def test_check_reply(self):
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
    
    def test_check_reply_short(self):
        response = client.post(
            "/api/quality/check-reply",
            json={
                "reply_content": "好的",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["score"] < 100


class TestRiskAPI:
    def test_check_order(self):
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
    
    def test_get_rules(self):
        response = client.get("/api/risk/rules")
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "0"
        assert "rules" in data["data"]
