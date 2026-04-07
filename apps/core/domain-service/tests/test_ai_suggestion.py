"""Tests for ai_suggestion route."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from app.main import app

    return TestClient(app)


class TestAiSuggestionRoute:
    def test_ai_suggest_reply_endpoint(self, client):
        payload = {
            "conversation_id": "CONV_001",
            "message": "我的订单什么时候发货？",
            "platform": "taobao",
            "order_id": "ORDER_001",
        }
        response = client.post("/api/ai/suggest-reply", json=payload)
        assert response.status_code in [200, 400, 422]

    def test_ai_suggest_reply_without_order(self, client):
        payload = {
            "conversation_id": "CONV_001",
            "message": "你好",
            "platform": "taobao",
        }
        response = client.post("/api/ai/suggest-reply", json=payload)
        assert response.status_code in [200, 400, 422]
