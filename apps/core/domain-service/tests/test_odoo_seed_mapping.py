from scripts.data_tools.odoo_seed_mapping import (
    build_created_orders_from_existing_live_batch,
    build_platform_order_link_seed,
    build_runtime_platform_order_links,
    build_seed_client_order_ref_updates,
    collect_platform_fixture_orders,
    merge_link_payload,
)


def test_collect_platform_fixture_orders_reads_known_order_ids():
    fixture_orders = collect_platform_fixture_orders()
    keys = {f"{item['platform']}:{item['platform_order_id']}" for item in fixture_orders}

    assert "taobao:12345678901231" in keys
    assert "jd:98765432101234" in keys
    assert "taobao:12345678901234" in keys
    assert "douyin_shop:6912558345648290211" in keys
    assert "xhs:XHS12345678901234" in keys
    assert "kuaishou:KS12345678901234" in keys
    assert len(keys) >= 45


def test_build_platform_order_link_seed_assigns_sale_orders_to_fixture_orders():
    seed = build_platform_order_link_seed(
        sale_order_rows=[
            {"id": "sale_order_a", "name": "SOA"},
            {"id": "sale_order_b", "name": "SOB"},
        ],
        fixture_orders=[
            {"platform": "jd", "platform_order_id": "98765432101234", "fixture_path": "a.json"},
            {"platform": "taobao", "platform_order_id": "12345678901234", "fixture_path": "b.json"},
        ],
    )

    assert seed["links"]["jd:98765432101234"]["sale_order_external_id"] == "sale_order_a"
    assert seed["links"]["jd:98765432101234"]["sale_order_name"] == "SOA"
    assert seed["links"]["taobao:12345678901234"]["sale_order_external_id"] == "sale_order_b"
    assert seed["links"]["taobao:12345678901234"]["sale_order_name"] == "SOB"


def test_build_runtime_platform_order_links_promotes_seed_to_runtime_links():
    runtime_payload = build_runtime_platform_order_links(
        seed_payload={
            "links": {
                "jd:98765432101234": {
                    "platform": "jd",
                    "platform_order_id": "98765432101234",
                    "sale_order_external_id": "sale_order_a",
                    "sale_order_name": "SOA",
                    "fixture_path": "a.json",
                }
            }
        },
        created_orders_by_external_id={
            "sale_order_a": {
                "odoo_order_id": "24",
                "odoo_order_name": "SOA",
            }
        },
    )

    assert runtime_payload["links"]["jd:98765432101234"] == {
        "platform": "jd",
        "platform_order_id": "98765432101234",
        "odoo_order_id": "24",
        "odoo_order_name": "SOA",
        "odoo_picking_id": None,
        "odoo_picking_name": None,
        "odoo_picking_origin": None,
        "sale_order_external_id": "sale_order_a",
        "fixture_path": "a.json",
        "link_strategy": "seed_imported",
    }


def test_build_created_orders_from_existing_live_batch_uses_last_live_rows():
    created_orders = build_created_orders_from_existing_live_batch(
        sale_order_rows=[
            {"id": "sale_order_a", "name": "SOA"},
            {"id": "sale_order_b", "name": "SOB"},
        ],
        live_sale_orders=[
            {"id": "11", "name": "S00011", "client_order_ref": False},
            {"id": "24", "name": "S00024", "client_order_ref": False},
            {"id": "25", "name": "S00025", "client_order_ref": False},
        ],
        limit=2,
    )

    assert created_orders == {
        "sale_order_a": {
            "odoo_order_id": "24",
            "odoo_order_name": "S00024",
            "client_order_ref": False,
        },
        "sale_order_b": {
            "odoo_order_id": "25",
            "odoo_order_name": "S00025",
            "client_order_ref": False,
        },
    }


def test_build_seed_client_order_ref_updates_targets_seeded_live_orders():
    updates = build_seed_client_order_ref_updates(
        seed_payload={
            "links": {
                "jd:98765432101234": {
                    "platform": "jd",
                    "platform_order_id": "98765432101234",
                    "sale_order_external_id": "sale_order_a",
                },
                "taobao:12345678901234": {
                    "platform": "taobao",
                    "platform_order_id": "12345678901234",
                    "sale_order_external_id": "sale_order_b",
                },
            }
        },
        created_orders_by_external_id={
            "sale_order_a": {"odoo_order_id": "24", "odoo_order_name": "S00024"},
            "sale_order_b": {"odoo_order_id": "25", "odoo_order_name": "S00025"},
        },
    )

    assert updates == [
        {
            "platform": "jd",
            "platform_order_id": "98765432101234",
            "sale_order_external_id": "sale_order_a",
            "odoo_order_id": "24",
            "odoo_order_name": "S00024",
        },
        {
            "platform": "taobao",
            "platform_order_id": "12345678901234",
            "sale_order_external_id": "sale_order_b",
            "odoo_order_id": "25",
            "odoo_order_name": "S00025",
        },
    ]


def test_merge_link_payload_drops_unknown_key_when_platform_link_arrives():
    merged = merge_link_payload(
        existing={
            "links": {
                "unknown:98765432101234": {
                    "platform": "unknown",
                    "platform_order_id": "98765432101234",
                    "odoo_order_id": "24",
                    "odoo_order_name": "S00024",
                }
            }
        },
        incoming={
            "links": {
                "jd:98765432101234": {
                    "platform": "jd",
                    "platform_order_id": "98765432101234",
                    "odoo_order_id": "29",
                    "odoo_order_name": "S00029",
                }
            }
        },
    )

    assert "unknown:98765432101234" not in merged["links"]
    assert merged["links"]["jd:98765432101234"]["odoo_order_id"] == "29"
