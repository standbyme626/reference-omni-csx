from app.services.after_sale_service import AfterSaleService
from fastapi.testclient import TestClient
from app.models.unified import Platform


def _get_app():
    from app.main import app as domain_app

    return domain_app


def _get_after_sale_service_dependency():
    from app.dependencies import get_after_sale_service

    return get_after_sale_service


class FakeGateway:
    def __init__(self):
        self.captured = {}

    def get_refund(self, platform, refund_id, official_run_id=None):
        self.captured["refund"] = (platform, refund_id, official_run_id)
        return {
            "after_sale_id": refund_id,
            "order_id": "TB_ORDER_003",
            "status": "refunding",
            "reason": "尺码不合适",
            "refund_amount": "599.00",
            "created_at": "2026-03-29T12:00:00+08:00",
            "updated_at": "2026-03-29T12:00:00+08:00",
        }

    def get_refund_by_order(self, platform, order_id, official_run_id=None):
        self.captured["by_order"] = (platform, order_id, official_run_id)
        return {
            "after_sale_id": "taobao:12345678901234:after_sale",
            "canonical_after_sale_id": "taobao:12345678901234:after_sale",
            "external_after_sale_id": "12345678901234",
            "order_id": "TB_ORDER_003",
            "external_order_id": "12345678901234",
            "requested_order_id": order_id,
            "status": "refunding",
            "reason": "尺码不合适",
            "refund_amount": "599.00",
            "created_at": "2026-03-29T12:00:00+08:00",
            "updated_at": "2026-03-29T12:00:00+08:00",
        }


def test_get_after_sale_by_order_uses_gateway_order_lookup():
    gateway = FakeGateway()
    service = AfterSaleService(gateway)

    result = service.get_after_sale_by_order(
        "taobao",
        "TB_ORDER_003",
        official_run_id="run-123",
    )

    assert gateway.captured["by_order"] == (
        Platform.TAOBAO,
        "TB_ORDER_003",
        "run-123",
    )
    assert result["after_sale_id"] == "taobao:12345678901234:after_sale"
    assert result["external_after_sale_id"] == "12345678901234"
    assert result["external_order_id"] == "12345678901234"
    assert result["requested_order_id"] == "TB_ORDER_003"
    assert result["status"] == "refunding"


def test_after_sale_by_order_route_forwards_official_run_id():
    class FakeService:
        def __init__(self):
            self.calls = []

        def get_after_sale_by_order(self, platform, order_id, official_run_id=None):
            self.calls.append((platform, order_id, official_run_id))
            return {
                "after_sale_id": "jd:98765432101234:after_sale",
                "canonical_after_sale_id": "jd:98765432101234:after_sale",
                "external_after_sale_id": "8820123456789",
                "order_id": "98765432101234",
                "external_order_id": "98765432101234",
                "requested_order_id": order_id,
                "platform": platform,
                "status": "refunding",
                "status_text": "退款中",
                "type": "refund",
                "reason": "商品损坏",
                "description": None,
                "refund_amount": "9999.00",
                "created_at": "2026-03-29T10:30:00+08:00",
                "updated_at": "2026-03-29T10:30:00+08:00",
            }

    fake_service = FakeService()
    app = _get_app()
    dependency = _get_after_sale_service_dependency()
    app.dependency_overrides[dependency] = lambda: fake_service
    client = TestClient(app)

    try:
        response = client.get(
            "/api/after-sales/jd/by-order/98765432101234",
            params={"official_run_id": "run-456"},
        )
    finally:
        app.dependency_overrides.pop(dependency, None)

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["after_sale"]["after_sale_id"] == "jd:98765432101234:after_sale"
    assert payload["data"]["after_sale"]["requested_order_id"] == "98765432101234"
    assert fake_service.calls == [("jd", "98765432101234", "run-456")]
