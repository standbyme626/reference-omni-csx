"""
Odoo 数据导入脚本
通过 XML-RPC API 导入数据
"""
import argparse
import json
import os
import time
import xmlrpc.client
from pathlib import Path

import pandas as pd

try:
    from scripts.data_tools.odoo_seed_mapping import (
        build_created_orders_from_existing_live_batch,
        build_seed_client_order_ref_updates,
        build_runtime_platform_order_links,
        merge_link_payload,
    )
except ModuleNotFoundError:
    from odoo_seed_mapping import (
        build_created_orders_from_existing_live_batch,
        build_seed_client_order_ref_updates,
        build_runtime_platform_order_links,
        merge_link_payload,
    )

ODOO_URL = "http://localhost:8069"
DB_NAME = "olist_db"
ADMIN_PASSWORD = "admin"

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(
    os.getenv(
        "PLATFORM_SIM_DATA_ODOO_IMPORT",
        str(REPO_ROOT / "data" / "staging" / "odoo_import"),
    )
)
RUNTIME_LINK_FILE = REPO_ROOT / "data" / "runtime" / "odoo_order_links.json"
SEED_LINK_FILE = DATA_DIR / "platform_order_link_seed.json"


def connect():
    common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common")
    models = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object")
    return common, models


def authenticate(common):
    print("认证登录...")
    uid = common.authenticate(DB_NAME, "admin", ADMIN_PASSWORD, {})
    if uid:
        print(f"  登录成功, UID: {uid}")
    else:
        print("  登录失败")
    return uid


def install_modules(models, uid):
    print("安装必要模块...")
    modules = ["sale_management", "stock", "account"]
    
    for module in modules:
        try:
            module_ids = models.execute_kw(
                DB_NAME, uid, ADMIN_PASSWORD,
                "ir.module.module", "search",
                [[["name", "=", module]]]
            )
            if module_ids:
                models.execute_kw(
                    DB_NAME, uid, ADMIN_PASSWORD,
                    "ir.module.module", "button_immediate_install",
                    [module_ids]
                )
                print(f"  安装模块: {module}")
                time.sleep(3)
        except Exception as e:
            print(f"  模块 {module}: {str(e)[:80]}")


def import_categories(models, uid):
    print("导入产品分类...")
    df = pd.read_csv(f"{DATA_DIR}/product.category.csv")
    
    cat_map = {}
    for _, row in df.iterrows():
        try:
            cat_id = models.execute_kw(
                DB_NAME, uid, ADMIN_PASSWORD,
                "product.category", "create",
                [{"name": row["name"]}]
            )
            cat_map[row["name"]] = cat_id
        except Exception:
            existing = models.execute_kw(
                DB_NAME, uid, ADMIN_PASSWORD,
                "product.category", "search",
                [[["name", "=", row["name"]]]]
            )
            if existing:
                cat_map[row["name"]] = existing[0]
    
    print(f"  完成: {len(cat_map)} 条分类")
    return cat_map


def import_products(models, uid, cat_map, limit=500):
    print(f"导入产品（限制 {limit} 条）...")
    df = pd.read_csv(f"{DATA_DIR}/product.product.csv")
    
    total = 0
    for _, row in df.head(limit).iterrows():
        try:
            cat_name = row.get("categ_id", "")
            categ_id = cat_map.get(cat_name, False)
            
            models.execute_kw(
                DB_NAME, uid, ADMIN_PASSWORD,
                "product.product", "create",
                [{
                    "name": row["name"],
                    "default_code": row.get("default_code", ""),
                    "categ_id": categ_id,
                    "type": "consu",
                    "list_price": 0,
                }]
            )
            total += 1
            if total % 50 == 0:
                print(f"  已导入 {total} 条产品", end="\r")
        except Exception:
            pass
    
    print(f"  完成: {total} 条产品")


def import_partners(models, uid, limit=2000):
    print(f"导入联系人（限制 {limit} 条）...")
    df = pd.read_csv(f"{DATA_DIR}/res.partner.csv")
    
    total = 0
    partner_map = {}
    for _, row in df.head(limit).iterrows():
        try:
            partner_id = models.execute_kw(
                DB_NAME, uid, ADMIN_PASSWORD,
                "res.partner", "create",
                [{
                    "name": row["name"],
                    "customer_rank": int(row.get("customer_rank", 0)),
                    "supplier_rank": int(row.get("supplier_rank", 0)),
                    "city": str(row.get("city", "")) if pd.notna(row.get("city")) else "",
                    "zip": str(row.get("zip", "")) if pd.notna(row.get("zip")) else "",
                }]
            )
            partner_map[row["id"]] = partner_id
            total += 1
            if total % 100 == 0:
                print(f"  已导入 {total} 条联系人", end="\r")
        except Exception:
            existing = models.execute_kw(
                DB_NAME, uid, ADMIN_PASSWORD,
                "res.partner", "search",
                [[["name", "=", row["name"]]]],
                {"limit": 1}
            )
            if existing:
                partner_map[row["id"]] = existing[0]
    
    print(f"  完成: {total} 条联系人")
    return partner_map


def import_sale_orders(models, uid, partner_map, limit=1000):
    print(f"导入销售订单（限制 {limit} 条）...")

    partners = list(partner_map.values())
    if not partners:
        partners = models.execute_kw(
            DB_NAME, uid, ADMIN_PASSWORD,
            "res.partner", "search",
            [[]], {"limit": 5000}
        )
    if not partners:
        print("  没有联系人，跳过订单导入")
        return {}

    df = pd.read_csv(f"{DATA_DIR}/sale.order.csv")
    created_orders = {}
    total = 0
    for _, row in df.head(limit).iterrows():
        external_id = row["id"]
        try:
            partner_id = partner_map.get(row.get("partner_id"))
            if not partner_id:
                partner_idx = hash(external_id) % len(partners)
                partner_id = partners[partner_idx]

            values = {
                "partner_id": partner_id,
                "date_order": row.get("date_order", ""),
                "name": row.get("name", ""),
                "client_order_ref": row.get("client_order_ref", ""),
                "note": row.get("note", ""),
            }

            order_id = models.execute_kw(
                DB_NAME, uid, ADMIN_PASSWORD,
                "sale.order", "create",
                [values]
            )
            created_orders[external_id] = {
                "odoo_order_id": str(order_id),
                "odoo_order_name": str(values["name"] or order_id),
            }
            total += 1
            if total % 50 == 0:
                print(f"  已导入 {total} 条订单", end="\r")
        except Exception:
            search_domain = [["|", ["name", "=", row.get("name", "")], ["client_order_ref", "=", row.get("client_order_ref", "")]]]
            existing = models.execute_kw(
                DB_NAME, uid, ADMIN_PASSWORD,
                "sale.order", "search_read",
                search_domain,
                {"fields": ["id", "name"], "limit": 1}
            )
            if existing:
                created_orders[external_id] = {
                    "odoo_order_id": str(existing[0]["id"]),
                    "odoo_order_name": str(existing[0].get("name", "")),
                }
    
    print(f"  完成: {total} 条订单")
    return created_orders


def write_runtime_order_links(created_orders):
    if not created_orders or not SEED_LINK_FILE.exists():
        return 0

    try:
        seed_payload = json.loads(SEED_LINK_FILE.read_text(encoding="utf-8"))
    except Exception:
        return 0

    runtime_links = build_runtime_platform_order_links(seed_payload, created_orders)
    if not runtime_links.get("links"):
        return 0

    try:
        existing_payload = json.loads(RUNTIME_LINK_FILE.read_text(encoding="utf-8")) if RUNTIME_LINK_FILE.exists() else {"links": {}}
    except Exception:
        existing_payload = {"links": {}}

    merged_payload = merge_link_payload(existing_payload, runtime_links)
    RUNTIME_LINK_FILE.parent.mkdir(parents=True, exist_ok=True)
    RUNTIME_LINK_FILE.write_text(
        json.dumps(merged_payload, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(f"  写入运行态平台订单映射: {len(runtime_links['links'])} 条")
    return len(runtime_links["links"])


def _get_outgoing_picking_defaults(models, uid):
    existing_pickings = models.execute_kw(
        DB_NAME,
        uid,
        ADMIN_PASSWORD,
        "stock.picking",
        "search_read",
        [[]],
        {
            "fields": ["picking_type_id", "location_id", "location_dest_id", "move_type"],
            "order": "id asc",
            "limit": 1,
        },
    )
    if existing_pickings:
        picking = existing_pickings[0]
        return {
            "picking_type_id": picking["picking_type_id"][0] if picking.get("picking_type_id") else False,
            "location_id": picking["location_id"][0] if picking.get("location_id") else False,
            "location_dest_id": picking["location_dest_id"][0] if picking.get("location_dest_id") else False,
            "move_type": picking.get("move_type") or "direct",
        }

    picking_types = models.execute_kw(
        DB_NAME,
        uid,
        ADMIN_PASSWORD,
        "stock.picking.type",
        "search_read",
        [[["code", "=", "outgoing"]]],
        {
            "fields": ["id", "default_location_src_id", "default_location_dest_id"],
            "order": "id asc",
            "limit": 1,
        },
    )
    if not picking_types:
        raise RuntimeError("No outgoing stock.picking.type found for backfill")

    picking_type = picking_types[0]
    location_dest_id = False
    if picking_type.get("default_location_dest_id"):
        location_dest_id = picking_type["default_location_dest_id"][0]
    else:
        customer_locations = models.execute_kw(
            DB_NAME,
            uid,
            ADMIN_PASSWORD,
            "stock.location",
            "search_read",
            [[["complete_name", "=", "Partners/Customers"]]],
            {"fields": ["id"], "limit": 1},
        )
        location_dest_id = customer_locations[0]["id"] if customer_locations else False

    return {
        "picking_type_id": picking_type["id"],
        "location_id": (
            picking_type["default_location_src_id"][0]
            if picking_type.get("default_location_src_id")
            else False
        ),
        "location_dest_id": location_dest_id,
        "move_type": "direct",
    }


def _ensure_pickings_for_sale_orders(models, uid, updates, live_orders_by_id):
    order_names = sorted({update["odoo_order_name"] for update in updates})
    if not order_names:
        return {}

    pickings = models.execute_kw(
        DB_NAME,
        uid,
        ADMIN_PASSWORD,
        "stock.picking",
        "search_read",
        [[["origin", "in", order_names]]],
        {"fields": ["id", "name", "origin"], "order": "id asc"},
    )
    picking_by_origin = {}
    for picking in pickings:
        origin = picking.get("origin")
        if origin and origin not in picking_by_origin:
            picking_by_origin[str(origin)] = picking

    missing_updates = [update for update in updates if update["odoo_order_name"] not in picking_by_origin]
    if not missing_updates:
        return picking_by_origin

    defaults = _get_outgoing_picking_defaults(models, uid)
    for update in missing_updates:
        live_order = live_orders_by_id.get(update["odoo_order_id"])
        if not live_order:
            continue

        values = {
            "picking_type_id": defaults["picking_type_id"],
            "location_id": defaults["location_id"],
            "location_dest_id": defaults["location_dest_id"],
            "move_type": defaults["move_type"],
            "origin": update["odoo_order_name"],
            "scheduled_date": live_order.get("date_order"),
        }
        partner = live_order.get("partner_id")
        if partner:
            values["partner_id"] = partner[0]

        picking_id = models.execute_kw(
            DB_NAME,
            uid,
            ADMIN_PASSWORD,
            "stock.picking",
            "create",
            [values],
        )
        created = models.execute_kw(
            DB_NAME,
            uid,
            ADMIN_PASSWORD,
            "stock.picking",
            "search_read",
            [[["id", "=", picking_id]]],
            {"fields": ["id", "name", "origin"], "limit": 1},
        )
        if created:
            picking_by_origin[update["odoo_order_name"]] = created[0]

    return picking_by_origin


def backfill_existing_sale_orders(models, uid, limit=500):
    if not SEED_LINK_FILE.exists():
        print("  缺少平台订单映射 seed，跳过现有订单回填")
        return {"updated_orders": 0, "runtime_links": 0}

    seed_payload = json.loads(SEED_LINK_FILE.read_text(encoding="utf-8"))
    staged_sale_orders = pd.read_csv(f"{DATA_DIR}/sale.order.csv").to_dict(orient="records")
    live_sale_orders = models.execute_kw(
        DB_NAME,
        uid,
        ADMIN_PASSWORD,
        "sale.order",
        "search_read",
        [[]],
        {
            "fields": ["id", "name", "partner_id", "client_order_ref", "date_order", "create_date"],
            "order": "id asc",
        },
    )

    created_orders = build_created_orders_from_existing_live_batch(
        sale_order_rows=staged_sale_orders,
        live_sale_orders=live_sale_orders,
        limit=limit,
    )
    updates = build_seed_client_order_ref_updates(seed_payload, created_orders)
    if not updates:
        print("  没有可回填的平台订单映射")
        return {"updated_orders": 0, "runtime_links": 0}

    live_order_refs = {
        str(row["id"]): row.get("client_order_ref")
        for row in live_sale_orders
        if row.get("id") is not None
    }
    live_orders_by_id = {
        str(row["id"]): row
        for row in live_sale_orders
        if row.get("id") is not None
    }

    updated_orders = 0
    for update in updates:
        order_id = int(update["odoo_order_id"])
        current_ref = live_order_refs.get(update["odoo_order_id"])
        if current_ref == update["platform_order_id"]:
            continue

        models.execute_kw(
            DB_NAME,
            uid,
            ADMIN_PASSWORD,
            "sale.order",
            "write",
            [[order_id], {"client_order_ref": update["platform_order_id"]}],
        )
        live_order_refs[update["odoo_order_id"]] = update["platform_order_id"]
        created_orders[update["sale_order_external_id"]]["client_order_ref"] = update["platform_order_id"]
        updated_orders += 1

    picking_by_origin = _ensure_pickings_for_sale_orders(models, uid, updates, live_orders_by_id)

    for update in updates:
        picking = picking_by_origin.get(update["odoo_order_name"])
        if not picking:
            continue
        created_orders[update["sale_order_external_id"]].update(
            {
                "odoo_picking_id": str(picking["id"]),
                "odoo_picking_name": str(picking["name"]),
                "odoo_picking_origin": str(picking["origin"]),
            }
        )

    runtime_link_count = write_runtime_order_links(created_orders)
    print(
        f"  现有订单回填完成: 更新 client_order_ref {updated_orders} 条, "
        f"写入运行态映射 {runtime_link_count} 条"
    )
    return {
        "updated_orders": updated_orders,
        "runtime_links": runtime_link_count,
    }


def verify_data(models, uid):
    print("\n验证导入数据...")
    
    models_to_check = [
        ("product.category", "产品分类"),
        ("product.product", "产品"),
        ("res.partner", "联系人"),
        ("sale.order", "销售订单"),
    ]
    
    for model, name in models_to_check:
        try:
            count = models.execute_kw(
                DB_NAME, uid, ADMIN_PASSWORD,
                model, "search_count",
                [[]]
            )
            print(f"  ✓ {name}: {count} 条记录")
        except Exception as e:
            print(f"  ✗ {name}: {e}")


def parse_args():
    parser = argparse.ArgumentParser(description="Import or backfill Odoo data")
    parser.add_argument(
        "--backfill-existing-orders",
        action="store_true",
        help="Backfill current live sale.order records instead of creating new rows",
    )
    parser.add_argument(
        "--sale-order-limit",
        type=int,
        default=500,
        help="How many staged sale.order rows correspond to the live import batch",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    print("=" * 50)
    print("Odoo 数据导入")
    print("=" * 50)
    
    common, models = connect()
    uid = authenticate(common)
    
    if not uid:
        print("认证失败，请检查数据库是否已创建")
        return

    if args.backfill_existing_orders:
        print("\n回填现有销售订单...")
        backfill_existing_sale_orders(models, uid, limit=args.sale_order_limit)
        verify_data(models, uid)
        print("\n" + "=" * 50)
        print("现有订单回填完成！")
        print(f"访问地址: {ODOO_URL}")
        print(f"数据库: {DB_NAME}")
        print("=" * 50)
        return
    
    print("\n安装模块...")
    install_modules(models, uid)
    
    print("\n开始导入数据...")
    cat_map = import_categories(models, uid)
    import_products(models, uid, cat_map, limit=500)
    partner_map = import_partners(models, uid, limit=2000)
    created_orders = import_sale_orders(models, uid, partner_map, limit=args.sale_order_limit)
    write_runtime_order_links(created_orders)
    
    verify_data(models, uid)
    
    print("\n" + "=" * 50)
    print("导入完成！")
    print(f"访问地址: {ODOO_URL}")
    print(f"数据库: {DB_NAME}")
    print("用户名: admin")
    print(f"密码: {ADMIN_PASSWORD}")
    print("=" * 50)


if __name__ == "__main__":
    main()
