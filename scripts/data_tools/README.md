# data_tools

数据转换与导入脚本（本地运行工具）。

脚本：
- `convert_to_chinese.py`
- `convert_to_odoo.py`
- `import_to_odoo.py`
- `odoo_seed_mapping.py`

说明：
- 原位置在 `data/`，已统一迁移到 `scripts/data_tools/`。
- 数据 canonical 路径：
  - 原始：`data/raw/olist`
  - 中文转换：`data/processed/olist_cn`
  - Odoo 导入：`data/staging/odoo_import`
- Odoo 映射资产：
  - 导数阶段生成 `data/staging/odoo_import/platform_order_link_seed.json`
  - 导入阶段生成 `data/runtime/odoo_order_links.json`
- 真实 Odoo 既有库回填：
  - `python scripts/data_tools/import_to_odoo.py --backfill-existing-orders --sale-order-limit 500`
  - 作用：对当前 Odoo 已存在的导入批次回填 `sale.order.client_order_ref`，并为映射订单补建最小 `stock.picking`
