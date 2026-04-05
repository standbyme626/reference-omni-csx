from app.adapters.registry import bootstrap_default_registry
from app.services.after_sale_domain_service import AfterSaleDomainService
from app.services.order_domain_service import OrderDomainService
from app.services.shipment_domain_service import ShipmentDomainService

from providers.utils.sim_identity import get_primary_order_id, iter_order_id_aliases


class FakeGateway:
    def get_order(self, platform, order_id, official_run_id=None):
        return {
            "order_id": order_id,
            "status": "WAIT_SELLER_SEND_GOODS",
            "status_text": "等待卖家发货",
            "total_amount": "299.00",
            "pay_amount": "299.00",
            "freight": "0.00",
            "receiver": {
                "name": "张三",
                "phone": "138****1234",
                "address": "浙江省杭州市余杭区文一西路999号",
            },
            "products": [],
            "created_at": "2026-03-29T10:00:00+08:00",
            "updated_at": "2026-03-29T10:05:00+08:00",
        }

    def get_shipment(self, platform, order_id, official_run_id=None):
        return {
            "shipment_id": f"SHIP_{order_id}",
            "order_id": order_id,
            "status": "in_transit",
            "company": "顺丰速运",
            "tracking_no": "SF1234567890",
            "nodes": [],
            "created_at": "2026-03-29T14:00:00+08:00",
            "updated_at": "2026-03-29T14:30:00+08:00",
        }

    def get_refund(self, platform, refund_id, official_run_id=None):
        return {
            "after_sale_id": "taobao:12345678901234:after_sale",
            "canonical_after_sale_id": "taobao:12345678901234:after_sale",
            "external_after_sale_id": "12345678901234",
            "order_id": "TB_ORDER_003",
            "external_order_id": "12345678901234",
            "requested_order_id": "TB_ORDER_003",
            "status": "refunding",
            "status_text": "退款中",
            "reason": "尺码不合适",
            "refund_amount": "599.00",
            "created_at": "2026-03-29T12:00:00+08:00",
            "updated_at": "2026-03-29T12:05:00+08:00",
        }

    def get_refund_by_order(self, platform, order_id, official_run_id=None):
        return self.get_refund(platform, order_id, official_run_id=official_run_id)


def test_order_service_attaches_requested_external_and_canonical_ids():
    service = OrderDomainService(FakeGateway(), bootstrap_default_registry())

    order = service.get_order("taobao", "TB_ORDER_003")

    assert order["order_id"] == "TB_ORDER_003"
    assert order["requested_order_id"] == "TB_ORDER_003"
    assert order["external_order_id"] == "12345678901234"
    assert order["canonical_order_id"] == "taobao:12345678901234:order"


def test_shipment_service_attaches_requested_external_and_canonical_ids():
    service = ShipmentDomainService(FakeGateway())

    shipment = service.get_shipment("taobao", "TB_ORDER_003")

    assert shipment["order_id"] == "TB_ORDER_003"
    assert shipment["requested_order_id"] == "TB_ORDER_003"
    assert shipment["external_order_id"] == "12345678901234"
    assert shipment["canonical_order_id"] == "taobao:12345678901234:order"
    assert shipment["canonical_shipment_id"] == "taobao:12345678901234:shipment"


def test_after_sale_service_attaches_canonical_order_identity():
    service = AfterSaleDomainService(FakeGateway())

    after_sale = service.get_after_sale_by_order("taobao", "TB_ORDER_003")

    assert after_sale["after_sale_id"] == "taobao:12345678901234:after_sale"
    assert after_sale["order_id"] == "TB_ORDER_003"
    assert after_sale["requested_order_id"] == "TB_ORDER_003"
    assert after_sale["external_order_id"] == "12345678901234"
    assert after_sale["canonical_order_id"] == "taobao:12345678901234:order"


def test_sim_identity_reads_unique_external_ids_from_user_fixtures():
    assert get_primary_order_id("taobao", "TB_ORDER_001") == "12345678901231"
    assert get_primary_order_id("taobao", "TB_ORDER_002") == "12345678901232"
    assert get_primary_order_id("taobao", "TB_ORDER_003") == "12345678901234"
    assert get_primary_order_id("douyin_shop", "DS_ORDER_001") == "6912558345648290201"
    assert get_primary_order_id("jd", "JD_ORDER_001") == "98765432101231"
    assert get_primary_order_id("xhs", "XHS_ORDER_001") == "XHS12345678901231"
    assert get_primary_order_id("kuaishou", "KS_ORDER_001") == "KS12345678901231"


def test_sim_identity_supports_reverse_lookup_from_external_order_ids():
    assert "TB_ORDER_001" in iter_order_id_aliases("taobao", "12345678901231")
    assert "DS_ORDER_001" in iter_order_id_aliases("douyin_shop", "6912558345648290201")
    assert "JD_ORDER_001" in iter_order_id_aliases("jd", "98765432101231")
    assert "XHS_ORDER_001" in iter_order_id_aliases("xhs", "XHS12345678901231")
    assert "KS_ORDER_001" in iter_order_id_aliases("kuaishou", "KS12345678901231")
