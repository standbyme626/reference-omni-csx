from datetime import datetime
from types import SimpleNamespace

import pytest
from app.adapters.registry import bootstrap_default_registry
from app.services.context_resolver import ContextResolver
from app.services.conversation_service import ConversationService
from app.services.recommendation_service import RecommendationService
from app.services.reply_generator import ReplyGenerator
from app.services.risk_evaluator import RiskEvaluator
from app.services.push_events_service import PushEventsService


class FakeOrderService:
    def __init__(self):
        self.calls = []

    def get_order(self, platform, order_id, official_run_id=None):
        self.calls.append((platform, order_id, official_run_id))
        return {
            "order_id": order_id,
            "status": "wait_ship",
            "total_amount": "199.00",
            "products": [{"product_id": "sku_001"}],
            "created_at": "2026-04-03T00:00:00+08:00",
        }


class FakeShipmentService:
    def __init__(self):
        self.calls = []

    def get_shipment(self, platform, order_id, official_run_id=None):
        self.calls.append((platform, order_id, official_run_id))
        return {
            "shipment_id": "SHIP_001",
            "status": "draft",
            "company": "SF",
            "tracking_no": "SF123456",
        }


class FakeAfterSaleService:
    def get_after_sale_by_order(self, platform, order_id, official_run_id=None):
        return {"error": "none"}


class FakeConversationService:
    def resolve_business_reference(self, platform, biz_id, official_run_id=None):
        return {
            "requested_platform": platform,
            "requested_biz_id": biz_id,
            "effective_platform": "jd",
            "effective_biz_id": "98765432101234",
            "biz_platform": "jd",
            "external_biz_id": "JD_ORDER_003",
            "official_run_id": official_run_id,
        }

    def get_conversation(self, platform, conversation_id, official_run_id=None):
        return {
            "conversation_id": conversation_id,
            "platform": platform,
            "official_run_id": official_run_id,
        }


class FakeOdooProvider:
    def __init__(self):
        self.audit_calls = []
        self.fulfillment_calls = []

    def get_inventory(self, product_id):
        return None

    def get_order_audit(self, order_id, platform=None):
        self.audit_calls.append((order_id, platform))
        return SimpleNamespace(
            order_id=order_id,
            audit_status="pending",
            audit_notes=order_id,
            audited_by="Mitchell Admin",
            audited_at=datetime.fromisoformat("2026-04-03T00:00:00+08:00"),
        )

    def get_order_exceptions(self, order_id):
        return []

    def get_fulfillment(self, order_id, platform=None):
        self.fulfillment_calls.append((order_id, platform))
        return SimpleNamespace(
            order_id=order_id,
            status="draft",
            warehouse="WH/库存",
            picking_id="33",
            scheduled_date=datetime.fromisoformat("2026-04-03T00:00:00+08:00"),
            actual_date=None,
        )


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
        order_status = context.get("order_snapshot", {}).get("status", "unknown")
        return [
            {
                "reply_type": "order_status",
                "content": f"Your order is {order_status}",
                "score": 0.9,
            }
        ]

    def generate_actions(self, context):
        return [{"action_type": "view_order", "label": "View Order"}]

    def evaluate_escalation(self, context, reason=None):
        return {"escalate": False}


def test_build_order_context_bridges_wecom_order_to_effective_platform():
    order_service = FakeOrderService()
    shipment_service = FakeShipmentService()
    after_sale_service = FakeAfterSaleService()
    conversation_service = FakeConversationService()
    odoo_provider = FakeOdooProvider()
    push_events_service = FakePushEventsService()
    risk_evaluator = FakeRiskEvaluator()
    reply_generator = FakeReplyGenerator()
    resolver = ContextResolver(
        order_service=order_service,
        shipment_service=shipment_service,
        after_sale_service=after_sale_service,
        conversation_service=conversation_service,
        odoo_provider=odoo_provider,
        push_events_service=push_events_service,
        risk_evaluator=risk_evaluator,
        reply_generator=reply_generator,
    )

    context = resolver.build_context(
        platform="wecom_kf",
        biz_id="JD_ORDER_003",
        biz_type="order",
        options={},
        official_run_id="00000000-0000-0000-0000-000000000123",
    )

    assert context["resolved_biz_reference"]["effective_platform"] == "jd"
    assert context["resolved_biz_reference"]["effective_biz_id"] == "98765432101234"
    assert context["order_snapshot"]["order_id"] == "98765432101234"
    assert context["data_sources"]["order_snapshot"] == "linked_platform_provider"
    assert context["data_sources"]["shipment_snapshot"] == "linked_platform_provider"
    assert order_service.calls == [("jd", "98765432101234", None)]
    assert shipment_service.calls == [("jd", "98765432101234", None)]
    assert odoo_provider.audit_calls == [("98765432101234", "jd")]
    assert odoo_provider.fulfillment_calls == [("98765432101234", "jd")]


class FakeContextService:
    def get_context(self, platform, biz_id, official_run_id=None):
        return {
            "context_id": "ctx_001",
            "platform": platform,
            "biz_id": biz_id,
            "official_run_id": official_run_id,
            "order_snapshot": {"status": "wait_ship"},
            "shipment_snapshot": {"tracking_no": "SF123456", "company": "SF"},
            "after_sale_snapshot": None,
            "risk_flags": {"level": "low"},
        }


def test_reply_recommendations_support_user_sim_intent_aliases():
    context_resolver = FakeContextService()
    reply_generator = ReplyGenerator()
    service = RecommendationService(context_resolver, reply_generator)

    result = service.get_reply_recommendations(
        platform="wecom_kf",
        biz_id="JD_ORDER_003",
        intent="ask_order_status",
        official_run_id="00000000-0000-0000-0000-000000000123",
    )

    assert result["candidates"][0]["reply_type"] == "order_status"
    assert "wait_ship" in result["candidates"][0]["content"]


class FakeRefundOnlyContextService:
    def get_context(self, platform, biz_id, official_run_id=None):
        return {
            "context_id": "ctx_refund_only",
            "platform": platform,
            "biz_id": biz_id,
            "official_run_id": official_run_id,
            "order_snapshot": {"status": "shipped"},
            "shipment_snapshot": {},
            "after_sale_snapshot": {"status": "refunding", "status_text": "退款中"},
            "risk_flags": {"level": "low"},
        }


def test_reply_recommendations_do_not_leak_after_sale_for_shipment_intent():
    context_resolver = FakeRefundOnlyContextService()
    reply_generator = ReplyGenerator()
    service = RecommendationService(context_resolver, reply_generator)

    result = service.get_reply_recommendations(
        platform="taobao",
        biz_id="12345678901234",
        intent="ask_shipment",
    )

    assert result["candidates"][0]["reply_type"] == "general_greeting"


class EmptyGateway:
    def get_provider(self, platform):
        return None


@pytest.mark.parametrize(
    ("biz_id", "expected_platform", "expected_order_id"),
    [
        ("TB_ORDER_003", "taobao", "12345678901234"),
        ("DS_ORDER_003", "douyin_shop", "6912558345648290211"),
        ("JD_ORDER_003", "jd", "98765432101234"),
        ("XHS_ORDER_003", "xhs", "XHS12345678901234"),
        ("KS_ORDER_002", "kuaishou", "KS12345678901235"),
        ("KS_ORDER_003", "kuaishou", "KS12345678901234"),
    ],
)
def test_build_order_context_bridges_wecom_aliases_to_effective_platform_id(
    biz_id: str,
    expected_platform: str,
    expected_order_id: str,
):
    order_service = FakeOrderService()
    shipment_service = FakeShipmentService()
    odoo_provider = FakeOdooProvider()
    resolver = ContextResolver(
        order_service=order_service,
        shipment_service=shipment_service,
        after_sale_service=FakeAfterSaleService(),
        conversation_service=ConversationService(
            EmptyGateway(), bootstrap_default_registry()
        ),
        odoo_provider=odoo_provider,
        push_events_service=FakePushEventsService(),
        risk_evaluator=FakeRiskEvaluator(),
        reply_generator=FakeReplyGenerator(),
    )

    context = resolver.build_context(
        platform="wecom_kf",
        biz_id=biz_id,
        biz_type="order",
        options={},
        official_run_id="00000000-0000-0000-0000-000000000456",
    )

    assert context["resolved_biz_reference"]["effective_platform"] == expected_platform
    assert context["resolved_biz_reference"]["effective_biz_id"] == expected_order_id
    assert context["resolved_biz_reference"]["external_biz_id"] == biz_id
    assert order_service.calls == [(expected_platform, expected_order_id, None)]
    assert shipment_service.calls == [(expected_platform, expected_order_id, None)]
    assert odoo_provider.audit_calls == [(expected_order_id, expected_platform)]
    assert odoo_provider.fulfillment_calls == [(expected_order_id, expected_platform)]
