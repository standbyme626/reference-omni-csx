# Odoo 数据种子计划

## 概述

本文档描述如何为 Odoo ERP 生成可导入的种子数据，用于客服中台的 ERP 数据集成测试。

## 数据来源组合

### 第一层：Odoo 官方 Demo

Odoo 官方仓库中的 demo 数据：

- `addons/sale/data/sale_demo.xml` - 销售订单示例
- `addons/sale_stock/data/sale_order_demo.xml` - 销售订单+发货示例
- `addons/stock/data/stock_demo.xml` - 库存示例

### 第二层：OCA 模块

OCA (Odoo Community Association) 提供的扩展模块：

- `sale-workflow` - 销售流程增强
- `stock-logistics-workflow` - 物流流程增强

### 第三层：公开电商数据集

- Olist 巴西电商数据集 (~10万订单)
- Mendeley 南亚电商订单数据
- Instacart 购物篮数据

## 导入顺序

1. **基础数据** (master_data/)
   - `res.partner.csv` - 客户/供应商
   - `product.template.csv` - 商品模板
   - `product.product.csv` - 商品变体

2. **库存数据** (inventory_data/)
   - `stock.quant.csv` - 库存数量
   - `stock.location.csv` - 库位

3. **交易数据** (transaction_data/)
   - `sale.order.csv` - 销售订单
   - `sale.order.line.csv` - 订单行

4. **异常数据** (exception_data/)
   - 订单异常
   - 库存异常
   - 发货异常

## 字段映射

### External ID 策略

所有关联字段使用 External ID 格式：

```
product_0001
customer_0001
order_0001
```

### 商品字段映射

| Odoo 字段 | 种子数据字段 | 说明 |
|-----------|--------------|------|
| id | External ID | 唯一标识 |
| name | name | 商品名称 |
| default_code | SKU | SKU 编码 |
| list_price | price | 销售价格 |
| standard_price | cost | 成本价格 |
| type | "product" | 商品类型 |

### 订单字段映射

| Odoo 字段 | 种子数据字段 | 说明 |
|-----------|--------------|------|
| id | External ID | 唯一标识 |
| name | order_reference | 订单编号 |
| partner_id | customer_id | 客户 External ID |
| date_order | order_date | 订单日期 |
| state | status | 订单状态 |
| client_order_ref | source_order_id | 原始外部订单参考 |

### 显式映射资产

除 Odoo 自然字段外，当前还补充一条显式映射资产链，用于把仿真平台订单号稳定挂到导入后的 Odoo 单据：

1. `convert_to_odoo.py` 生成：
   - `sale.order.csv`
   - `platform_order_link_seed.json`
2. `import_to_odoo.py` 导入后生成：
   - `data/runtime/odoo_order_links.json`
   - 如目标环境已经存在旧导入的 `sale.order`，可额外执行：
     - `python scripts/data_tools/import_to_odoo.py --backfill-existing-orders --sale-order-limit 500`
     - 作用：回填现有 `sale.order.client_order_ref`，并为映射订单补建最小 `stock.picking`

说明：

- `platform_order_link_seed.json` 不是官方真相，也不是 Odoo 原生字段，而是“平台仿真订单号 -> Odoo 导入订单”的显式 seed。
- `data/runtime/odoo_order_links.json` 则是导入完成后、带有真实 Odoo 单据 ID / 单据名的运行态映射。
- 这样做的目的不是伪装成天然主数据，而是让平台订单号和 ERP 单据之间的关系可追溯、可复用、可重启持久化。

## 使用方法

### 生成种子数据

```bash
cd scripts/erp_seed_builder
python build_all.py
# 可选：python build_all.py --output-dir ../../artifacts/odoo_seed
```

### 导入 Odoo

1. 进入 Odoo 后台
2. 设置 -> 技术 -> 导入
3. 按顺序导入 CSV 文件

## 数据规模建议

| 数据类型 | 数量 |
|----------|------|
| 商品 | 100-500 |
| 客户 | 500-1000 |
| 订单 | 1000-5000 |
| 库存记录 | 200-1000 |

## 注意事项

1. 所有金额使用字符串格式，避免浮点精度问题
2. 时间字段使用 ISO 8601 格式
3. 关联字段使用 External ID
4. 导入前备份数据库
