"""
Odoo 数据导入脚本
通过 XML-RPC API 导入数据
"""
import xmlrpc.client
import pandas as pd
import time
import os

ODOO_URL = "http://localhost:8069"
DB_NAME = "olist_db"
ADMIN_PASSWORD = "admin"

DATA_DIR = "/home/kkk/Project/platform-sim/data/odoo_import"


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
        except Exception as e:
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
    for _, row in df.head(limit).iterrows():
        try:
            models.execute_kw(
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
            total += 1
            if total % 100 == 0:
                print(f"  已导入 {total} 条联系人", end="\r")
        except Exception:
            pass
    
    print(f"  完成: {total} 条联系人")


def import_sale_orders(models, uid, limit=1000):
    print(f"导入销售订单（限制 {limit} 条）...")
    
    partners = models.execute_kw(
        DB_NAME, uid, ADMIN_PASSWORD,
        "res.partner", "search",
        [[]], {"limit": 5000}
    )
    
    if not partners:
        print("  没有联系人，跳过订单导入")
        return
    
    df = pd.read_csv(f"{DATA_DIR}/sale.order.csv")
    
    total = 0
    for _, row in df.head(limit).iterrows():
        try:
            partner_idx = hash(row["id"]) % len(partners)
            partner_id = partners[partner_idx]
            
            models.execute_kw(
                DB_NAME, uid, ADMIN_PASSWORD,
                "sale.order", "create",
                [{
                    "partner_id": partner_id,
                    "date_order": row.get("date_order", ""),
                }]
            )
            total += 1
            if total % 50 == 0:
                print(f"  已导入 {total} 条订单", end="\r")
        except Exception:
            pass
    
    print(f"  完成: {total} 条订单")


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


def main():
    print("=" * 50)
    print("Odoo 数据导入")
    print("=" * 50)
    
    common, models = connect()
    uid = authenticate(common)
    
    if not uid:
        print("认证失败，请检查数据库是否已创建")
        return
    
    print("\n安装模块...")
    install_modules(models, uid)
    
    print("\n开始导入数据...")
    cat_map = import_categories(models, uid)
    import_products(models, uid, cat_map, limit=500)
    import_partners(models, uid, limit=2000)
    import_sale_orders(models, uid, limit=500)
    
    verify_data(models, uid)
    
    print("\n" + "=" * 50)
    print("导入完成！")
    print(f"访问地址: {ODOO_URL}")
    print(f"数据库: {DB_NAME}")
    print(f"用户名: admin")
    print(f"密码: {ADMIN_PASSWORD}")
    print("=" * 50)


if __name__ == "__main__":
    main()
