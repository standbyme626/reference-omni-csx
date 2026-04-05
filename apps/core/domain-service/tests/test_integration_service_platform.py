from datetime import datetime

from app.services.integration_service import IntegrationService
from providers.odoo.mock.provider import FulfillmentSnapshot, OrderAuditSnapshot


class CapturingOdooProvider:
    def __init__(self):
        self.calls = []

    def get_order_audit(self, order_id: str, platform: str | None = None):
        self.calls.append(
            {
                "method": "get_order_audit",
                "order_id": order_id,
                "platform": platform,
            }
        )
        return OrderAuditSnapshot(
            order_id=order_id,
            audit_status="approved",
            audit_notes="ok",
            audited_by="tester",
            audited_at=datetime(2026, 4, 2, 10, 0, 0),
        )

    def get_fulfillment(self, order_id: str, platform: str | None = None):
        self.calls.append(
            {
                "method": "get_fulfillment",
                "order_id": order_id,
                "platform": platform,
            }
        )
        return FulfillmentSnapshot(
            order_id=order_id,
            status="assigned",
            warehouse="WH/Stock",
            picking_id="PICK-001",
            scheduled_date=datetime(2026, 4, 3, 10, 0, 0),
            actual_date=None,
        )


def test_get_order_audits_passes_platform_to_odoo_provider():
    provider = CapturingOdooProvider()
    service = IntegrationService(provider)

    result = service.get_order_audits("98765432101234", platform="jd")

    assert len(result) == 1
    assert provider.calls == [
        {
            "method": "get_order_audit",
            "order_id": "98765432101234",
            "platform": "jd",
        }
    ]


def test_get_fulfillment_passes_platform_to_odoo_provider():
    provider = CapturingOdooProvider()
    service = IntegrationService(provider)

    result = service.get_fulfillment("98765432101234", platform="jd")

    assert len(result) == 1
    assert provider.calls == [
        {
            "method": "get_fulfillment",
            "order_id": "98765432101234",
            "platform": "jd",
        }
    ]
