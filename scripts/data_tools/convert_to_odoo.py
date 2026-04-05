"""
Olist 数据集转换为 Odoo 导入格式
生成可直接导入 Odoo 的 CSV 文件
"""
import json
import os
from pathlib import Path

import pandas as pd

try:
    from scripts.data_tools.odoo_seed_mapping import (
        build_platform_order_link_seed,
        collect_platform_fixture_orders,
    )
except ModuleNotFoundError:
    from odoo_seed_mapping import (
        build_platform_order_link_seed,
        collect_platform_fixture_orders,
    )

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(
    os.getenv(
        "PLATFORM_SIM_DATA_OLIST_CN",
        str(REPO_ROOT / "data" / "processed" / "olist_cn"),
    )
)
OUTPUT_DIR = Path(
    os.getenv(
        "PLATFORM_SIM_DATA_ODOO_IMPORT",
        str(REPO_ROOT / "data" / "staging" / "odoo_import"),
    )
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def convert_partners():
    """转换客户数据为 Odoo res.partner 格式"""
    print("转换客户数据为 Odoo 格式...")
    
    customers = pd.read_csv(f"{DATA_DIR}/olist_customers_dataset_cn.csv")
    sellers = pd.read_csv(f"{DATA_DIR}/olist_sellers_dataset_cn.csv")
    
    partners = []
    
    for _, row in customers.iterrows():
        partners.append({
            "id": f"res_partner_customer_{row['customer_id'][:8]}",
            "name": f"客户_{row['customer_id'][:8]}",
            "customer_rank": 1,
            "supplier_rank": 0,
            "city": row['customer_city'],
            "state_id": row['customer_state'],
            "zip": str(row['customer_zip_code_prefix']),
            "country_id": "中国",
            "type": "contact",
            "is_company": False,
        })
    
    for _, row in sellers.iterrows():
        partners.append({
            "id": f"res_partner_seller_{row['seller_id'][:8]}",
            "name": f"卖家_{row['seller_id'][:8]}",
            "customer_rank": 0,
            "supplier_rank": 1,
            "city": row['seller_city'],
            "state_id": row['seller_state'],
            "zip": str(row['seller_zip_code_prefix']),
            "country_id": "中国",
            "type": "contact",
            "is_company": True,
        })
    
    df = pd.DataFrame(partners)
    df.to_csv(f"{OUTPUT_DIR}/res.partner.csv", index=False, encoding="utf-8-sig")
    print(f"  完成: {len(df)} 条联系人记录")
    return df


def convert_product_categories():
    """转换产品分类为 Odoo product.category 格式"""
    print("转换产品分类为 Odoo 格式...")
    
    products = pd.read_csv(f"{DATA_DIR}/olist_products_dataset_cn.csv")
    
    categories = products['product_category_name'].dropna().unique()
    
    cat_df = []
    for i, cat in enumerate(categories):
        cat_df.append({
            "id": f"product_category_{i}",
            "name": cat,
            "parent_id": "",
            "complete_name": cat,
        })
    
    df = pd.DataFrame(cat_df)
    df.to_csv(f"{OUTPUT_DIR}/product.category.csv", index=False, encoding="utf-8-sig")
    print(f"  完成: {len(df)} 条分类记录")
    return df


def convert_products():
    """转换产品数据为 Odoo product.product 格式"""
    print("转换产品数据为 Odoo 格式...")
    
    products = pd.read_csv(f"{DATA_DIR}/olist_products_dataset_cn.csv")
    categories = pd.read_csv(f"{OUTPUT_DIR}/product.category.csv")
    
    cat_map = {row['name']: row['id'] for _, row in categories.iterrows()}
    
    prods = []
    for _, row in products.iterrows():
        cat_name = row.get('product_category_name', '')
        categ_id = cat_map.get(cat_name, '') if pd.notna(cat_name) else ''
        
        prods.append({
            "id": f"product_product_{row['product_id'][:8]}",
            "name": f"产品_{row['product_id'][:8]}",
            "default_code": row['product_id'][:12],
            "categ_id": categ_id,
            "type": "consu",
            "sale_ok": True,
            "purchase_ok": True,
            "list_price": 0,
            "standard_price": 0,
            "weight": row.get('product_weight_g', 0) / 1000 if pd.notna(row.get('product_weight_g')) else 0,
            "volume": (row.get('product_length_cm', 0) * row.get('product_height_cm', 0) * row.get('product_width_cm', 0)) / 1000000,
            "description_sale": f"产品名称长度: {row.get('product_name_lenght', 'N/A')}, 描述长度: {row.get('product_description_lenght', 'N/A')}, 图片数量: {row.get('product_photos_qty', 'N/A')}",
            "active": True,
        })
    
    df = pd.DataFrame(prods)
    df.to_csv(f"{OUTPUT_DIR}/product.product.csv", index=False, encoding="utf-8-sig")
    print(f"  完成: {len(df)} 条产品记录")
    return df


def convert_sale_orders():
    """转换订单数据为 Odoo sale.order 格式"""
    print("转换订单数据为 Odoo 格式...")
    
    orders = pd.read_csv(f"{DATA_DIR}/olist_orders_dataset_cn.csv")
    customers = pd.read_csv(f"{DATA_DIR}/olist_customers_dataset_cn.csv")
    payments = pd.read_csv(f"{DATA_DIR}/olist_order_payments_dataset_cn.csv")
    
    payment_totals = payments.groupby('order_id')['payment_value'].sum().to_dict()
    
    customer_map = {row['customer_id']: row['customer_id'][:8] for _, row in customers.iterrows()}
    
    status_map = {
        "已送达": "sale",
        "已发货": "sale",
        "已取消": "cancel",
        "已开票": "sale",
        "处理中": "draft",
        "已创建": "draft",
        "已批准": "sent",
        "不可用": "cancel",
    }
    
    sale_orders = []
    for _, row in orders.iterrows():
        customer_ref = customer_map.get(row['customer_id'], row['customer_id'][:8])
        order_date = pd.to_datetime(row['order_purchase_timestamp']).strftime('%Y-%m-%d') if pd.notna(row['order_purchase_timestamp']) else ''
        
        sale_orders.append({
            "id": f"sale_order_{row['order_id'][:8]}",
            "name": f"SO{row['order_id'][:8].upper()}",
            "partner_id": f"res_partner_customer_{customer_ref}",
            "date_order": order_date,
            "state": status_map.get(row['order_status'], "draft"),
            "amount_total": payment_totals.get(row['order_id'], 0),
            "currency_id": "CNY",
            "company_id": "Your Company",
            "client_order_ref": row["order_id"],
            "note": f"原始状态: {row['order_status']}",
        })
    
    df = pd.DataFrame(sale_orders)
    df.to_csv(f"{OUTPUT_DIR}/sale.order.csv", index=False, encoding="utf-8-sig")
    print(f"  完成: {len(df)} 条销售订单记录")

    fixture_orders = collect_platform_fixture_orders()
    seed_payload = build_platform_order_link_seed(
        sale_order_rows=df.to_dict(orient="records"),
        fixture_orders=fixture_orders,
    )
    (OUTPUT_DIR / "platform_order_link_seed.json").write_text(
        json.dumps(seed_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"  生成平台订单映射 seed: {len(seed_payload['links'])} 条")
    return df


def convert_sale_order_lines():
    """转换订单明细为 Odoo sale.order.line 格式"""
    print("转换订单明细为 Odoo 格式...")
    
    order_items = pd.read_csv(f"{DATA_DIR}/olist_order_items_dataset_cn.csv")
    
    lines = []
    for _, row in order_items.iterrows():
        lines.append({
            "id": f"sale_order_line_{row['order_item_id']}_{row['order_id'][:8]}",
            "order_id": f"sale_order_{row['order_id'][:8]}",
            "product_id": f"product_product_{row['product_id'][:8]}",
            "name": f"产品_{row['product_id'][:8]}",
            "product_uom_qty": 1,
            "product_uom": "Units",
            "price_unit": row.get('price', 0),
            "price_subtotal": row.get('price', 0),
            "price_total": row.get('price', 0) + row.get('freight_value', 0),
        })
    
    df = pd.DataFrame(lines)
    df.to_csv(f"{OUTPUT_DIR}/sale.order.line.csv", index=False, encoding="utf-8-sig")
    print(f"  完成: {len(df)} 条订单明细记录")
    return df


def convert_account_moves():
    """转换为 Odoo 发票格式 (account.move)"""
    print("转换发票数据为 Odoo 格式...")
    
    orders = pd.read_csv(f"{DATA_DIR}/olist_orders_dataset_cn.csv")
    customers = pd.read_csv(f"{DATA_DIR}/olist_customers_dataset_cn.csv")
    payments = pd.read_csv(f"{DATA_DIR}/olist_order_payments_dataset_cn.csv")
    
    payment_totals = payments.groupby('order_id')['payment_value'].sum().to_dict()
    payment_types = payments.groupby('order_id')['payment_type'].first().to_dict()
    
    customer_map = {row['customer_id']: row['customer_id'][:8] for _, row in customers.iterrows()}
    
    payment_ref_map = {
        "信用卡": "credit_card",
        "银行汇票": "bank_transfer",
        "代金券": "voucher",
        "借记卡": "debit_card",
    }
    
    invoices = []
    inv_count = 0
    for _, row in orders.iterrows():
        if row['order_status'] in ['已送达', '已开票']:
            inv_count += 1
            customer_ref = customer_map.get(row['customer_id'], row['customer_id'][:8])
            invoice_date = pd.to_datetime(row['order_purchase_timestamp']).strftime('%Y-%m-%d') if pd.notna(row['order_purchase_timestamp']) else ''
            
            invoices.append({
                "id": f"account_move_{row['order_id'][:8]}",
                "name": f"INV/{inv_count:06d}",
                "move_type": "out_invoice",
                "partner_id": f"res_partner_customer_{customer_ref}",
                "invoice_date": invoice_date,
                "amount_total": payment_totals.get(row['order_id'], 0),
                "amount_untaxed": payment_totals.get(row['order_id'], 0) / 1.13,
                "amount_tax": payment_totals.get(row['order_id'], 0) - payment_totals.get(row['order_id'], 0) / 1.13,
                "currency_id": "CNY",
                "state": "posted",
                "payment_reference": payment_ref_map.get(payment_types.get(row['order_id'], ''), 'bank_transfer'),
            })
    
    df = pd.DataFrame(invoices)
    df.to_csv(f"{OUTPUT_DIR}/account.move.csv", index=False, encoding="utf-8-sig")
    print(f"  完成: {len(df)} 条发票记录")
    return df


def create_import_readme():
    """创建导入说明文档"""
    readme = """# Odoo 数据导入说明

## 导入顺序

请按以下顺序导入数据：

1. **product.category.csv** - 产品分类
2. **product.product.csv** - 产品
3. **res.partner.csv** - 联系人（客户和供应商）
4. **sale.order.csv** - 销售订单
5. **sale.order.line.csv** - 销售订单明细
6. **account.move.csv** - 发票
7. **platform_order_link_seed.json** - 平台订单号到 Odoo 订单 seed 映射

## 导入步骤

### 方法一：通过 Odoo 界面导入

1. 进入 Odoo 后台
2. 进入对应模块（如：销售 → 产品 → 产品）
3. 点击"导入"按钮
4. 选择对应的 CSV 文件
5. 映射字段（Odoo 会自动识别大部分字段）
6. 点击"导入"

### 方法二：通过 CSV 直接导入

1. 确保已安装所需模块：销售、库存、会计
2. 进入 设置 → 技术 → 数据库结构 → 导入
3. 选择模型和 CSV 文件进行导入

## 字段说明

### res.partner (联系人)
- `id`: 外部标识符
- `name`: 名称
- `customer_rank`: 客户等级（1=是客户）
- `supplier_rank`: 供应商等级（1=是供应商）
- `city`: 城市
- `state_id`: 省份
- `zip`: 邮编

### product.product (产品)
- `id`: 外部标识符
- `name`: 产品名称
- `default_code`: 内部参考
- `categ_id`: 产品分类
- `list_price`: 销售价格
- `standard_price`: 成本价

### sale.order (销售订单)
- `id`: 外部标识符
- `name`: 订单编号
- `partner_id`: 客户
- `date_order`: 订单日期
- `state`: 状态
- `client_order_ref`: 原始外部订单参考

### platform_order_link_seed.json
- 用于把仿真平台中的典型订单号稳定挂到导入后的 Odoo 单据
- 不伪装成 Odoo 官方字段，而是作为显式映射 seed

### sale.order.line (订单明细)
- `order_id`: 关联订单
- `product_id`: 产品
- `product_uom_qty`: 数量
- `price_unit`: 单价

## 注意事项

1. 导入前请确保已安装所需模块
2. 首次导入建议先导入少量数据测试
3. 如遇字段映射问题，可在 Odoo 中手动调整
4. 导入后检查数据关联是否正确

## 数据统计

- 客户数量: 99,441
- 卖家数量: 3,095
- 产品数量: 32,951
- 产品分类: ~70
- 订单数量: 99,441
- 订单明细: 112,650
- 发票数量: ~96,000
"""
    
    with open(f"{OUTPUT_DIR}/README.md", "w", encoding="utf-8") as f:
        f.write(readme)
    print("  创建导入说明文档")


def main():
    print("=" * 50)
    print("Olist 数据集转换为 Odoo 导入格式")
    print("=" * 50)
    
    convert_product_categories()
    convert_products()
    convert_partners()
    convert_sale_orders()
    convert_sale_order_lines()
    convert_account_moves()
    create_import_readme()
    
    print("\n" + "=" * 50)
    print(f"转换完成！输出目录: {OUTPUT_DIR}")
    print("=" * 50)


if __name__ == "__main__":
    main()
