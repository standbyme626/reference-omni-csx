import asyncio

from providers.odoo.real.link_resolver import OdooOrderLinkResolver


class FakeLinkResolverClient:
    def __init__(self):
        self.calls = []

    async def execute(self, model, method, args, kwargs=None):
        self.calls.append(
            {
                "model": model,
                "method": method,
                "args": args,
                "kwargs": kwargs or {},
            }
        )
        if model == "sale.order" and method == "search_read":
            domain = args[0]
            if domain:
                return []
            return [
                {"id": 24, "name": "S00024"},
                {"id": 25, "name": "S00025"},
                {"id": 26, "name": "S00026"},
            ]
        if model == "stock.picking" and method == "search_read":
            domain = args[0]
            if ("origin", "=", "S00024") in domain:
                return [{"id": 28, "name": "WH/OUT/00013", "origin": "S00024"}]
            return []
        return []


def test_order_link_resolver_persists_stable_mapping_for_platform_order(tmp_path):
    client = FakeLinkResolverClient()
    resolver = OdooOrderLinkResolver(client, link_file=tmp_path / "odoo_links.json")

    first = asyncio.run(resolver.resolve_order_link("jd", "98765432101234"))
    second = asyncio.run(resolver.resolve_order_link("jd", "98765432101234"))

    assert first is not None
    assert second is not None
    assert first == second
    assert first["platform"] == "jd"
    assert first["platform_order_id"] == "98765432101234"
    assert first["odoo_order_name"] in {"S00024", "S00025", "S00026"}
    assert (tmp_path / "odoo_links.json").exists()


def test_order_link_resolver_prefers_matching_picking_origin(tmp_path):
    client = FakeLinkResolverClient()
    resolver = OdooOrderLinkResolver(client, link_file=tmp_path / "odoo_links.json")

    link = asyncio.run(resolver.resolve_order_link("jd", "98765432101234"))

    assert link is not None
    if link["odoo_order_name"] == "S00024":
        assert link["odoo_picking_id"] == "28"
        assert link["odoo_picking_name"] == "WH/OUT/00013"
