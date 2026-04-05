import pytest
from app.services.conversation_domain_service import ConversationDomainService
from app.services.official_sim_provider import OfficialSimProxyProvider
from models.unified import Platform


class FakeOfficialConversationProvider(OfficialSimProxyProvider):
    def __init__(self):
        pass

    def search_conversations(self, limit: int = 100):
        return {
            "items": [
                {
                    "id": "conv_run_001",
                    "platform": "wecom_kf",
                    "customer_id": "wecom_user_001",
                    "customer_nick": "张三",
                    "status": "active",
                    "biz_id": "JD_ORDER_001",
                    "biz_type": "order",
                    "biz_platform": "jd",
                    "official_run_id": "00000000-0000-0000-0000-000000000123",
                }
            ],
            "total": 1,
        }

    def get_conversation(self, conversation_id: str, official_run_id: str | None = None):
        return {
            "conversation_id": conversation_id,
            "status": "active",
            "customer_id": "wecom_user_001",
            "customer_nick": "张三",
            "biz_id": "JD_ORDER_001",
            "biz_type": "order",
            "biz_platform": "jd",
            "official_run_id": official_run_id,
        }

    def list_messages(
        self,
        conversation_id: str,
        limit: int = 100,
        official_run_id: str | None = None,
    ):
        self.captured = {
            "conversation_id": conversation_id,
            "limit": limit,
            "official_run_id": official_run_id,
        }
        return {
            "conversation_id": conversation_id,
            "messages": [
                {
                    "msg_id": "msg_001",
                    "sender_type": "customer",
                    "content": "订单怎么还没发货",
                    "created_at": "2026-04-02T10:00:00+08:00",
                }
            ],
            "total": 1,
        }


class FakeGateway:
    def __init__(self, provider):
        self.provider = provider

    def get_provider(self, platform):
        if platform == Platform.WECOM_KF:
            return self.provider
        return None

    def get_conversation(self, platform, conversation_id, official_run_id=None):
        return self.provider.get_conversation(conversation_id, official_run_id=official_run_id)


def test_search_conversations_prefers_official_run_source():
    provider = FakeOfficialConversationProvider()
    service = ConversationDomainService(FakeGateway(provider))

    result = service.search_conversations("all", {}, skip=0, limit=20)

    assert result["total"] == 1
    assert result["items"][0]["id"] == "conv_run_001"
    assert result["items"][0]["official_run_id"] == "00000000-0000-0000-0000-000000000123"
    assert result["items"][0]["biz_id"] == "JD_ORDER_001"


def test_get_conversation_messages_uses_official_run_id_from_search_index():
    provider = FakeOfficialConversationProvider()
    service = ConversationDomainService(FakeGateway(provider))

    result = service.get_conversation_messages("wecom_kf", "conv_run_001", limit=50)

    assert result["total"] == 1
    assert provider.captured["conversation_id"] == "conv_run_001"
    assert provider.captured["limit"] == 50
    assert provider.captured["official_run_id"] == "00000000-0000-0000-0000-000000000123"


def test_resolve_business_reference_bridges_wecom_run_to_order_platform():
    provider = FakeOfficialConversationProvider()
    service = ConversationDomainService(FakeGateway(provider))

    resolved = service.resolve_business_reference(
        "wecom_kf",
        "JD_ORDER_001",
        official_run_id="00000000-0000-0000-0000-000000000123",
    )

    assert resolved["requested_platform"] == "wecom_kf"
    assert resolved["requested_biz_id"] == "JD_ORDER_001"
    assert resolved["effective_platform"] == "jd"
    assert resolved["effective_biz_id"] == "98765432101231"
    assert resolved["biz_platform"] == "jd"
    assert resolved["external_biz_id"] == "JD_ORDER_001"


def test_search_conversations_falls_back_to_fixture_wecom_conversations():
    service = ConversationDomainService(FakeGateway(None))

    result = service.search_conversations("wecom_kf", {}, skip=0, limit=50)

    by_id = {item["conversation_id"]: item for item in result["items"]}
    assert by_id["CONV_WK_005"]["biz_platform"] == "taobao"
    assert by_id["CONV_WK_006"]["biz_platform"] == "douyin_shop"
    assert by_id["CONV_WK_007"]["biz_platform"] == "xhs"
    assert by_id["CONV_WK_008"]["biz_platform"] == "kuaishou"


@pytest.mark.parametrize(
    ("conversation_id", "expected_platform", "expected_order_id"),
    [
        ("CONV_WK_005", "taobao", "12345678901234"),
        ("CONV_WK_006", "douyin_shop", "6912558345648290202"),
        ("CONV_WK_007", "xhs", "XHS12345678901232"),
        ("CONV_WK_008", "kuaishou", "KS12345678901234"),
    ],
)
def test_resolve_business_reference_falls_back_to_fixture_conversation_links(
    conversation_id: str,
    expected_platform: str,
    expected_order_id: str,
):
    service = ConversationDomainService(FakeGateway(None))

    resolved = service.resolve_business_reference("wecom_kf", conversation_id)

    assert resolved["requested_platform"] == "wecom_kf"
    assert resolved["requested_biz_id"] == conversation_id
    assert resolved["effective_platform"] == expected_platform
    assert resolved["biz_platform"] == expected_platform
    assert resolved["effective_biz_id"] == expected_order_id


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
def test_resolve_business_reference_canonicalizes_all_supported_ecommerce_aliases(
    biz_id: str,
    expected_platform: str,
    expected_order_id: str,
):
    provider = FakeOfficialConversationProvider()
    service = ConversationDomainService(FakeGateway(provider))

    resolved = service.resolve_business_reference("wecom_kf", biz_id)

    assert resolved["requested_platform"] == "wecom_kf"
    assert resolved["requested_biz_id"] == biz_id
    assert resolved["biz_platform"] == expected_platform
    assert resolved["effective_platform"] == expected_platform
    assert resolved["effective_biz_id"] == expected_order_id
    assert resolved["external_biz_id"] == biz_id
