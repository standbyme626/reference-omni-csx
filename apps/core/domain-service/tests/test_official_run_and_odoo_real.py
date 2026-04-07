import socket
from datetime import datetime

import pytest
from app.adapters.registry import bootstrap_default_registry
from app.core.config import settings
from app.services.context_resolver import ContextResolver
from app.services.official_sim_provider import (
    OfficialSimNotFoundError,
    OfficialSimProxyProvider,
)
from app.services.platform_gateway_service import PlatformGatewayService
from app.models.unified import Platform

from providers.odoo.mock.provider import OrderAuditSnapshot
from providers.odoo.provider import OdooProvider, OdooProviderMode


def _official_sim_available():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect(("localhost", 8001))
        return True
    except (ConnectionRefusedError, OSError):
        return False
    finally:
        s.close()


pytestmark = pytest.mark.skipif(
    not _official_sim_available(), reason="official-sim server not running"
)


def test_gateway_forwards_official_run_id_to_official_sim_provider(monkeypatch):
    original_mode = settings.default_provider_mode
    settings.default_provider_mode = "official_sim"

    try:
        gateway = PlatformGatewayService(bootstrap_default_registry())
        provider = gateway.get_provider(Platform.TAOBAO)
        assert isinstance(provider, OfficialSimProxyProvider)

        captured = {}

        def fake_get_order(order_id, official_run_id=None):
            captured["order_id"] = order_id
            captured["official_run_id"] = official_run_id
            return {
                "trade": {
                    "tid": order_id,
                    "status": "WAIT_SELLER_SEND_GOODS",
                    "total_fee": "199.00",
                    "payment": "199.00",
                    "receiver_name": "张三",
                    "created": "2026-03-01T10:00:00",
                    "modified": "2026-03-01T10:00:00",
                },
                "orders": {"order": []},
            }

        monkeypatch.setattr(provider, "get_order", fake_get_order)

        gateway.get_order(Platform.TAOBAO, "TB_ORDER_001", official_run_id="run-123")

        assert captured == {
            "order_id": "TB_ORDER_001",
            "official_run_id": "run-123",
        }
    finally:
        settings.default_provider_mode = original_mode


def test_business_context_tracks_sources_and_propagates_official_run_id():
    captured = {}

    class FakeOrderService:
        def get_order(self, platform, order_id, official_run_id=None):
            captured["order"] = official_run_id
            return {
                "order_id": order_id,
                "status": "wait_ship",
                "total_amount": "299.00",
                "products": [{"product_id": "SKU_001"}],
                "created_at": "2026-03-29T10:00:00+08:00",
            }

    class FakeShipmentService:
        def get_shipment(self, platform, order_id, official_run_id=None):
            captured["shipment"] = official_run_id
            raise ValueError("shipment not found")

    class FakeAfterSaleService:
        def get_after_sale_by_order(self, platform, order_id, official_run_id=None):
            captured["after_sale"] = official_run_id
            raise ValueError("after-sale not found")

    class FakeConversationService:
        def resolve_business_reference(self, platform, biz_id, official_run_id=None):
            return {
                "requested_platform": platform,
                "requested_biz_id": biz_id,
                "effective_platform": platform,
                "effective_biz_id": biz_id,
                "official_run_id": official_run_id,
            }

        def get_conversation(self, platform, conversation_id):
            return {"conversation_id": conversation_id}

    class FakePushEventsService:
        def get_push_events(self, official_run_id):
            return []

        def apply_state(self, context, events):
            pass

    class FakeRiskEvaluator:
        def evaluate(self, context):
            return {"level": "low"}

    class FakeReplyGenerator:
        def generate_replies(self, context, intent=None):
            return []

        def generate_actions(self, context):
            return []

        def evaluate_escalation(self, context, reason=None):
            return {"escalate": False}

    resolver = ContextResolver(
        order_service=FakeOrderService(),
        shipment_service=FakeShipmentService(),
        after_sale_service=FakeAfterSaleService(),
        conversation_service=FakeConversationService(),
        odoo_provider=OdooProvider(mode=OdooProviderMode.MOCK),
        push_events_service=FakePushEventsService(),
        risk_evaluator=FakeRiskEvaluator(),
        reply_generator=FakeReplyGenerator(),
    )

    context = resolver.get_context("taobao", "TB_ORDER_001", official_run_id="run-456")

    assert captured == {
        "order": "run-456",
        "shipment": "run-456",
        "after_sale": "run-456",
    }
    assert context["data_sources"]["order_snapshot"] == "official_sim_run"
    assert any(
        error["source"] == "shipment_snapshot" for error in context["source_errors"]
    )
    assert any(
        error["source"] == "after_sale_snapshot" for error in context["source_errors"]
    )


def test_odoo_real_sync_bridge_uses_async_provider():
    class FakeRealProvider:
        async def get_order_audit(self, order_id):
            return OrderAuditSnapshot(
                order_id=order_id,
                audit_status="approved",
                audit_notes="ok",
                audited_by="tester",
                audited_at=datetime(2026, 4, 2, 12, 0, 0),
            )

    provider = OdooProvider(mode=OdooProviderMode.MOCK)
    provider.mode = OdooProviderMode.REAL
    provider._real_provider = FakeRealProvider()

    audit = provider.get_order_audit("42")

    assert audit is not None
    assert audit.order_id == "42"
    assert audit.audit_status == "approved"


def test_official_sim_request_json_preserves_404_detail(monkeypatch):
    class DummyResponse:
        status_code = 404
        text = '{"detail":"Run shipment state not found"}'

        @staticmethod
        def json():
            return {"detail": "Run shipment state not found"}

    class DummyClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def request(self, method, url, params=None, json=None):
            return DummyResponse()

    monkeypatch.setattr("app.services.official_sim_provider.httpx.Client", DummyClient)

    provider = OfficialSimProxyProvider("taobao", base_url="http://official-sim.test")

    with pytest.raises(OfficialSimNotFoundError, match="Run shipment state not found"):
        provider._request_json("GET", "/official-sim/raw/shipments/ORDER_001")


def test_official_sim_provider_normalizes_jd_shipment_payload(monkeypatch):
    provider = OfficialSimProxyProvider("jd", base_url="http://official-sim.test")

    def fake_request_json(method, path, params=None, json_body=None):
        assert method == "GET"
        assert path == "/official-sim/raw/shipments/98765432101234"
        assert params == {"platform": "jd"}
        return {
            "data": {
                "jingdong_order_search_responce": {
                    "orderId": 98765432101234,
                    "orderStatus": 33040,
                    "orderStartTime": "2026-03-29 10:00:00",
                    "orderPurchaseTime": "2026-03-29 10:05:00",
                    "orderStatusTime": "2026-03-29 14:00:00",
                    "deliveryCarrierName": "顺丰速运",
                    "deliveryBillNo": "SF1234567890",
                    "deliveryConfirmTime": None,
                }
            }
        }

    monkeypatch.setattr(provider, "_request_json", fake_request_json)

    shipment = provider.get_shipment("98765432101234")

    assert shipment["order_id"] == "98765432101234"
    assert shipment["status"] == "shipped"
    assert shipment["company"] == "顺丰速运"
    assert shipment["tracking_no"] == "SF1234567890"
    assert shipment["created_at"] == "2026-03-29T10:05:00"
    assert shipment["updated_at"] == "2026-03-29T14:00:00"
    assert shipment["nodes"][0]["node"] == "订单创建"
    assert (
        shipment["nodes"][-1]["description"] == "承运商 顺丰速运，运单号 SF1234567890"
    )


@pytest.mark.parametrize(
    (
        "platform",
        "order_id",
        "response_data",
        "expected_status",
        "expected_company",
        "expected_tracking_no",
    ),
    [
        (
            "taobao",
            "12345678901234",
            {
                "trade": {
                    "tid": 12345678901234,
                    "status": "WAIT_BUYER_CONFIRM_GOODS",
                    "consign_time": "2026-03-29 14:00:00",
                    "modified": "2026-03-29 14:30:00",
                    "orders": {
                        "order": [
                            {
                                "logistics_company": "顺丰速运",
                                "invoice_no": "SF1234567890",
                            }
                        ]
                    },
                }
            },
            "shipped",
            "顺丰速运",
            "SF1234567890",
        ),
        (
            "douyin_shop",
            "6912558345648290211",
            {
                "order": {
                    "order_id": "6912558345648290211",
                    "update_time": 1743267600,
                    "consign_time": 1743267600,
                    "delivery_info": {
                        "company_name": "顺丰速运",
                        "tracking_no": "SF1234567890",
                        "delivery_status": 100,
                        "delivery_status_desc": "已发货",
                    },
                }
            },
            "shipped",
            "顺丰速运",
            "SF1234567890",
        ),
        (
            "xhs",
            "XHS12345678901234",
            {
                "order": {
                    "orderId": "XHS12345678901234",
                    "deliveryTime": 1743267600,
                    "logistics": {
                        "logisticsCompany": "顺丰速运",
                        "trackingNo": "SF1234567890",
                        "status": "delivering",
                    },
                }
            },
            "in_transit",
            "顺丰速运",
            "SF1234567890",
        ),
        (
            "kuaishou",
            "KS12345678901235",
            {
                "order": {
                    "orderId": "KS12345678901235",
                    "deliveryTime": 1743264000,
                    "deliveryStatus": 20,
                    "logistics": {
                        "company": "顺丰速运",
                        "trackingNo": "SF1234567890",
                        "status": "in_transit",
                    },
                }
            },
            "in_transit",
            "顺丰速运",
            "SF1234567890",
        ),
    ],
)
def test_official_sim_provider_normalizes_platform_shipment_payloads(
    monkeypatch,
    platform: str,
    order_id: str,
    response_data,
    expected_status: str,
    expected_company: str,
    expected_tracking_no: str,
):
    provider = OfficialSimProxyProvider(platform, base_url="http://official-sim.test")

    def fake_request_json(method, path, params=None, json_body=None):
        assert method == "GET"
        assert path == f"/official-sim/raw/shipments/{order_id}"
        assert params == {"platform": platform}
        return {"data": response_data}

    monkeypatch.setattr(provider, "_request_json", fake_request_json)

    shipment = provider.get_shipment(order_id)

    assert shipment["order_id"] == order_id
    assert shipment["status"] == expected_status
    assert shipment["company"] == expected_company
    assert shipment["tracking_no"] == expected_tracking_no


def test_official_sim_provider_get_order_accepts_alias_identifier(monkeypatch):
    provider = OfficialSimProxyProvider("jd", base_url="http://official-sim.test")

    def fake_request_json(method, path, params=None, json_body=None):
        assert method == "GET"
        assert path == "/official-sim/raw/orders/JD_ORDER_003"
        return {
            "data": {
                "jingdong_order_search_responce": {
                    "orderId": 98765432101234,
                    "orderStatus": 32000,
                }
            }
        }

    monkeypatch.setattr(provider, "_request_json", fake_request_json)

    order = provider.get_order("JD_ORDER_003")

    assert order["jingdong_order_search_responce"]["orderId"] == 98765432101234


def test_official_sim_provider_get_refund_by_order_normalizes_stable_identifiers(
    monkeypatch,
):
    provider = OfficialSimProxyProvider("taobao", base_url="http://official-sim.test")

    def fake_request_json(method, path, params=None, json_body=None):
        assert method == "GET"
        assert path == "/official-sim/raw/after-sales/by-order/TB_ORDER_003"
        assert params == {"platform": "taobao"}
        return {
            "data": {
                "after_sale": {
                    "after_sale_id": "taobao:12345678901234:after_sale",
                    "canonical_after_sale_id": "taobao:12345678901234:after_sale",
                    "external_after_sale_id": "12345678901234",
                    "refund_id": "12345678901234",
                    "order_id": "TB_ORDER_003",
                    "external_order_id": "12345678901234",
                    "requested_order_id": "TB_ORDER_003",
                    "status": "refunding",
                    "reason": "尺码不合适",
                    "refund_amount": "599.00",
                    "created_at": "2026-03-29T12:00:00+08:00",
                    "updated_at": "2026-03-29T12:00:00+08:00",
                }
            }
        }

    monkeypatch.setattr(provider, "_request_json", fake_request_json)

    refund = provider.get_refund_by_order("TB_ORDER_003")

    assert refund["after_sale_id"] == "taobao:12345678901234:after_sale"
    assert refund["canonical_after_sale_id"] == "taobao:12345678901234:after_sale"
    assert refund["external_after_sale_id"] == "12345678901234"
    assert refund["order_id"] == "TB_ORDER_003"
    assert refund["requested_order_id"] == "TB_ORDER_003"
    assert refund["status"] == "refunding"


def test_official_sim_provider_get_refund_by_order_accepts_alias_identifier(
    monkeypatch,
):
    provider = OfficialSimProxyProvider("taobao", base_url="http://official-sim.test")

    def fake_request_json(method, path, params=None, json_body=None):
        assert method == "GET"
        assert path == "/official-sim/raw/after-sales/by-order/TB_ORDER_003"
        return {
            "data": {
                "after_sale": {
                    "after_sale_id": "taobao:12345678901234:after_sale",
                    "canonical_after_sale_id": "taobao:12345678901234:after_sale",
                    "external_after_sale_id": "12345678901234",
                    "refund_id": "12345678901234",
                    "order_id": "12345678901234",
                    "external_order_id": "12345678901234",
                    "requested_order_id": "TB_ORDER_003",
                    "status": "refunding",
                    "reason": "尺码不合适",
                    "refund_amount": "599.00",
                    "created_at": "2026-03-29T12:00:00+08:00",
                    "updated_at": "2026-03-29T12:00:00+08:00",
                }
            }
        }

    monkeypatch.setattr(provider, "_request_json", fake_request_json)

    refund = provider.get_refund_by_order("TB_ORDER_003")

    assert refund["after_sale_id"] == "taobao:12345678901234:after_sale"
    assert refund["order_id"] == "12345678901234"
    assert refund["requested_order_id"] == "TB_ORDER_003"


def test_official_sim_provider_get_refund_accepts_canonical_identifier(monkeypatch):
    provider = OfficialSimProxyProvider("taobao", base_url="http://official-sim.test")

    def fake_request_json(method, path, params=None, json_body=None):
        assert method == "GET"
        assert path == "/official-sim/raw/after-sales/taobao:12345678901234:after_sale"
        return {
            "data": {
                "after_sale": {
                    "after_sale_id": "taobao:12345678901234:after_sale",
                    "canonical_after_sale_id": "taobao:12345678901234:after_sale",
                    "external_after_sale_id": "12345678901234",
                    "refund_id": "12345678901234",
                    "order_id": "TB_ORDER_003",
                    "external_order_id": "12345678901234",
                    "status": "refunding",
                    "reason": "尺码不合适",
                    "refund_amount": "599.00",
                    "created_at": "2026-03-29T12:00:00+08:00",
                    "updated_at": "2026-03-29T12:00:00+08:00",
                }
            }
        }

    monkeypatch.setattr(provider, "_request_json", fake_request_json)

    refund = provider.get_refund("taobao:12345678901234:after_sale")

    assert refund["after_sale_id"] == "taobao:12345678901234:after_sale"
    assert refund["external_after_sale_id"] == "12345678901234"
    assert refund["status"] == "refunding"
