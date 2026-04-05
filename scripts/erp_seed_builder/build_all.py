import argparse
import csv
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import random
import string

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "artifacts" / "odoo_seed"


class ProductBuilder:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.products: List[Dict[str, Any]] = []
    
    def generate_products(self, count: int = 100) -> List[Dict[str, Any]]:
        categories = ["电子产品", "服装", "食品", "家居", "美妆", "运动", "图书", "玩具"]
        
        for i in range(count):
            category = random.choice(categories)
            product = {
                "id": f"product_{i+1:04d}",
                "name": f"{category}商品_{i+1:04d}",
                "default_code": f"SKU_{i+1:04d}",
                "categ_id": f"cat_{categories.index(category)+1}",
                "list_price": round(random.uniform(10, 1000), 2),
                "standard_price": round(random.uniform(5, 500), 2),
                "type": "product",
                "sale_ok": True,
                "purchase_ok": True,
                "active": True,
            }
            self.products.append(product)
        
        return self.products
    
    def to_csv(self, filename: str = "product.template.csv"):
        filepath = self.output_dir / filename
        
        fieldnames = [
            "External ID", "Name", "Internal Reference", "Category",
            "Sales Price", "Cost", "Product Type", "Can be Sold",
            "Can be Purchased", "Active",
        ]
        
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for p in self.products:
                writer.writerow({
                    "External ID": p["id"],
                    "Name": p["name"],
                    "Internal Reference": p["default_code"],
                    "Category": p["categ_id"],
                    "Sales Price": p["list_price"],
                    "Cost": p["standard_price"],
                    "Product Type": p["type"],
                    "Can be Sold": p["sale_ok"],
                    "Can be Purchased": p["purchase_ok"],
                    "Active": p["active"],
                })
        
        return filepath


class PartnerBuilder:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.partners: List[Dict[str, Any]] = []
    
    def generate_customers(self, count: int = 500) -> List[Dict[str, Any]]:
        first_names = ["张", "李", "王", "刘", "陈", "杨", "赵", "黄", "周", "吴"]
        last_names = ["伟", "芳", "娜", "秀英", "敏", "静", "丽", "强", "磊", "军"]
        provinces = ["浙江省", "江苏省", "广东省", "北京市", "上海市", "四川省", "湖北省", "山东省"]
        cities = ["杭州市", "南京市", "广州市", "北京市", "上海市", "成都市", "武汉市", "济南市"]
        
        for i in range(count):
            name = f"{random.choice(first_names)}{random.choice(last_names)}"
            province_idx = random.randint(0, len(provinces) - 1)
            
            partner = {
                "id": f"customer_{i+1:04d}",
                "name": name,
                "phone": f"1{random.choice(['3', '5', '7', '8', '9'])}{random.randint(100000000, 999999999)}",
                "email": f"{name.lower()}@example.com",
                "street": f"{random.randint(1, 999)}号",
                "city": cities[province_idx],
                "state_id": provinces[province_idx],
                "zip": f"{random.randint(100000, 999999)}",
                "customer_rank": random.randint(1, 10),
                "supplier_rank": 0,
                "is_company": False,
            }
            self.partners.append(partner)
        
        return self.partners
    
    def to_csv(self, filename: str = "res.partner.csv"):
        filepath = self.output_dir / filename
        
        fieldnames = [
            "External ID", "Name", "Phone", "Email", "Street",
            "City", "State", "Zip", "Customer Rank", "Supplier Rank", "Is a Company",
        ]
        
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for p in self.partners:
                writer.writerow({
                    "External ID": p["id"],
                    "Name": p["name"],
                    "Phone": p["phone"],
                    "Email": p["email"],
                    "Street": p["street"],
                    "City": p["city"],
                    "State": p["state_id"],
                    "Zip": p["zip"],
                    "Customer Rank": p["customer_rank"],
                    "Supplier Rank": p["supplier_rank"],
                    "Is a Company": p["is_company"],
                })
        
        return filepath


class OrderBuilder:
    def __init__(self, output_dir: Path, products: List[Dict], partners: List[Dict]):
        self.output_dir = output_dir
        self.products = products
        self.partners = partners
        self.orders: List[Dict[str, Any]] = []
        self.order_lines: List[Dict[str, Any]] = []
    
    def generate_orders(self, count: int = 1000) -> List[Dict[str, Any]]:
        statuses = ["draft", "sent", "sale", "done", "cancel"]
        status_weights = [10, 20, 40, 25, 5]
        
        base_date = datetime.now() - timedelta(days=365)
        
        for i in range(count):
            customer = random.choice(self.partners)
            status = random.choices(statuses, weights=status_weights)[0]
            order_date = base_date + timedelta(days=random.randint(0, 365))
            
            num_lines = random.randint(1, 5)
            lines = []
            total = 0
            
            for j in range(num_lines):
                product = random.choice(self.products)
                quantity = random.randint(1, 10)
                price = product["list_price"]
                subtotal = quantity * price
                total += subtotal
                
                line = {
                    "id": f"order_line_{i+1:04d}_{j+1}",
                    "order_id": f"order_{i+1:04d}",
                    "product_id": product["id"],
                    "name": product["name"],
                    "product_uom_qty": quantity,
                    "price_unit": price,
                    "price_subtotal": subtotal,
                }
                lines.append(line)
                self.order_lines.append(line)
            
            order = {
                "id": f"order_{i+1:04d}",
                "name": f"SO{i+1:05d}",
                "partner_id": customer["id"],
                "date_order": order_date.strftime("%Y-%m-%d %H:%M:%S"),
                "state": status,
                "amount_total": round(total, 2),
                "amount_untaxed": round(total / 1.13, 2),
                "amount_tax": round(total - total / 1.13, 2),
            }
            self.orders.append(order)
        
        return self.orders
    
    def to_csv(self, order_filename: str = "sale.order.csv", line_filename: str = "sale.order.line.csv"):
        order_filepath = self.output_dir / order_filename
        line_filepath = self.output_dir / line_filename
        
        order_fieldnames = [
            "External ID", "Order Reference", "Customer", "Order Date",
            "Status", "Total", "Untaxed Amount", "Tax Amount",
        ]
        
        with open(order_filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=order_fieldnames)
            writer.writeheader()
            
            for o in self.orders:
                writer.writerow({
                    "External ID": o["id"],
                    "Order Reference": o["name"],
                    "Customer": o["partner_id"],
                    "Order Date": o["date_order"],
                    "Status": o["state"],
                    "Total": o["amount_total"],
                    "Untaxed Amount": o["amount_untaxed"],
                    "Tax Amount": o["amount_tax"],
                })
        
        line_fieldnames = [
            "External ID", "Order", "Product", "Description",
            "Quantity", "Unit Price", "Subtotal",
        ]
        
        with open(line_filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=line_fieldnames)
            writer.writeheader()
            
            for l in self.order_lines:
                writer.writerow({
                    "External ID": l["id"],
                    "Order": l["order_id"],
                    "Product": l["product_id"],
                    "Description": l["name"],
                    "Quantity": l["product_uom_qty"],
                    "Unit Price": l["price_unit"],
                    "Subtotal": l["price_subtotal"],
                })
        
        return order_filepath, line_filepath


class InventoryBuilder:
    def __init__(self, output_dir: Path, products: List[Dict]):
        self.output_dir = output_dir
        self.products = products
        self.quants: List[Dict[str, Any]] = []

    def generate_inventory(self) -> List[Dict[str, Any]]:
        warehouses = ["WH_MAIN", "WH_EAST", "WH_WEST", "WH_NORTH", "WH_SOUTH"]
        locations = ["LOC_A01", "LOC_A02", "LOC_B01", "LOC_B02", "LOC_C01"]

        for product in self.products:
            num_warehouses = random.randint(1, 3)
            selected_warehouses = random.sample(warehouses, num_warehouses)

            for wh in selected_warehouses:
                quant = {
                    "id": f"quant_{product['id']}_{wh}",
                    "product_id": product["id"],
                    "location_id": f"{wh}/{random.choice(locations)}",
                    "quantity": random.randint(0, 500),
                    "reserved_quantity": random.randint(0, 50),
                }
                quant["available_quantity"] = quant["quantity"] - quant["reserved_quantity"]
                self.quants.append(quant)

        return self.quants

    def to_csv(self, filename: str = "stock.quant.csv"):
        filepath = self.output_dir / filename

        fieldnames = [
            "External ID", "Product", "Location", "Quantity",
            "Reserved Quantity", "Available Quantity",
        ]

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for q in self.quants:
                writer.writerow({
                    "External ID": q["id"],
                    "Product": q["product_id"],
                    "Location": q["location_id"],
                    "Quantity": q["quantity"],
                    "Reserved Quantity": q["reserved_quantity"],
                    "Available Quantity": q["available_quantity"],
                })

        return filepath


class OrderAuditBuilder:
    def __init__(self, output_dir: Path, orders: List[Dict]):
        self.output_dir = output_dir
        self.orders = orders
        self.audits: List[Dict[str, Any]] = []

    def generate_audits(self) -> List[Dict[str, Any]]:
        auditors = ["auditor_001", "auditor_002", "auditor_003", "auditor_004"]
        statuses = ["pending", "approved", "rejected"]

        for order in self.orders:
            status = random.choices(statuses, weights=[20, 70, 10])[0]
            audited_at = None

            if status != "pending":
                audit_date = datetime.now() - timedelta(days=random.randint(0, 30))
                audited_at = audit_date.strftime("%Y-%m-%d %H:%M:%S")

            audit = {
                "id": f"audit_{order['id']}",
                "order_id": order["id"],
                "audit_status": status,
                "audit_notes": self._get_audit_notes(status),
                "audited_by": random.choice(auditors) if status != "pending" else "",
                "audited_at": audited_at,
            }
            self.audits.append(audit)

        return self.audits

    def _get_audit_notes(self, status: str) -> str:
        notes_map = {
            "pending": "等待财务审核",
            "approved": "订单审核通过，可以发货",
            "rejected": "订单审核拒绝，需要修改",
        }
        return notes_map.get(status, "")

    def to_csv(self, filename: str = "order_audit.csv"):
        filepath = self.output_dir / filename

        fieldnames = [
            "External ID", "Order", "Audit Status", "Audit Notes",
            "Audited By", "Audited At",
        ]

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for a in self.audits:
                writer.writerow({
                    "External ID": a["id"],
                    "Order": a["order_id"],
                    "Audit Status": a["audit_status"],
                    "Audit Notes": a["audit_notes"],
                    "Audited By": a["audited_by"],
                    "Audited At": a["audited_at"] or "",
                })

        return filepath


class OrderExceptionBuilder:
    def __init__(self, output_dir: Path, orders: List[Dict]):
        self.output_dir = output_dir
        self.orders = orders
        self.exceptions: List[Dict[str, Any]] = []

    def generate_exceptions(self) -> List[Dict[str, Any]]:
        exception_types = [
            "inventory_shortage",
            "address_issue",
            "payment_delay",
            "product_unavailable",
            "price_mismatch",
        ]
        severity_map = {
            "inventory_shortage": "medium",
            "address_issue": "high",
            "payment_delay": "low",
            "product_unavailable": "high",
            "price_mismatch": "medium",
        }

        for order in self.orders:
            if random.random() < 0.15:
                num_exceptions = random.randint(1, 3)
                for j in range(num_exceptions):
                    exc_type = random.choice(exception_types)
                    exception = {
                        "id": f"exc_{order['id']}_{j+1}",
                        "order_id": order["id"],
                        "exception_type": exc_type,
                        "severity": severity_map[exc_type],
                        "description": self._get_description(exc_type),
                        "status": random.choice(["open", "resolved"]),
                        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "resolved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S") if random.random() > 0.5 else "",
                    }
                    self.exceptions.append(exception)

        return self.exceptions

    def _get_description(self, exc_type: str) -> str:
        desc_map = {
            "inventory_shortage": "库存不足，需要补货",
            "address_issue": "收货地址不完整或无法送达",
            "payment_delay": "支付超时，需要重新支付",
            "product_unavailable": "商品已下架或缺货",
            "price_mismatch": "价格存在差异，需要核实",
        }
        return desc_map.get(exc_type, "其他异常")

    def to_csv(self, filename: str = "order_exception.csv"):
        filepath = self.output_dir / filename

        fieldnames = [
            "External ID", "Order", "Exception Type", "Severity",
            "Description", "Status", "Created At", "Resolved At",
        ]

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for e in self.exceptions:
                writer.writerow({
                    "External ID": e["id"],
                    "Order": e["order_id"],
                    "Exception Type": e["exception_type"],
                    "Severity": e["severity"],
                    "Description": e["description"],
                    "Status": e["status"],
                    "Created At": e["created_at"],
                    "Resolved At": e["resolved_at"] or "",
                })

        return filepath


class FulfillmentBuilder:
    def __init__(self, output_dir: Path, orders: List[Dict]):
        self.output_dir = output_dir
        self.orders = orders
        self.pickings: List[Dict[str, Any]] = []
        self.moves: List[Dict[str, Any]] = []

    def generate_fulfillment(self) -> tuple:
        warehouses = ["WH_MAIN", "WH_EAST", "WH_WEST"]
        statuses = ["pending", "assigned", "picking", "done", "cancel"]

        for order in self.orders:
            if order["state"] in ["sale", "done"]:
                status = random.choices(statuses, weights=[20, 20, 30, 25, 5])[0]
                scheduled_date = (datetime.now() + timedelta(days=random.randint(1, 7))).strftime("%Y-%m-%d")
                actual_date = None

                if status == "done":
                    actual_date = (datetime.now() + timedelta(days=random.randint(1, 5))).strftime("%Y-%m-%d")

                picking = {
                    "id": f"picking_{order['id']}",
                    "order_id": order["id"],
                    "status": status,
                    "warehouse": random.choice(warehouses),
                    "scheduled_date": scheduled_date,
                    "actual_date": actual_date,
                }
                self.pickings.append(picking)

                for j in range(random.randint(1, 3)):
                    move = {
                        "id": f"move_{order['id']}_{j+1}",
                        "picking_id": picking["id"],
                        "product_id": f"product_{random.randint(1, 100):04d}",
                        "location_id": f"{picking['warehouse']}/LOC_{random.choice(['A', 'B', 'C'])}{random.randint(1, 9):02d}",
                        "quantity": random.randint(1, 10),
                        "state": "done" if status == "done" else "pending",
                    }
                    self.moves.append(move)

        return self.pickings, self.moves

    def to_csv(self, picking_filename: str = "stock.picking.csv", move_filename: str = "stock.move.csv"):
        picking_filepath = self.output_dir / picking_filename
        move_filepath = self.output_dir / move_filename

        picking_fieldnames = [
            "External ID", "Order", "Status", "Warehouse",
            "Scheduled Date", "Actual Date",
        ]

        with open(picking_filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=picking_fieldnames)
            writer.writeheader()

            for p in self.pickings:
                writer.writerow({
                    "External ID": p["id"],
                    "Order": p["order_id"],
                    "Status": p["status"],
                    "Warehouse": p["warehouse"],
                    "Scheduled Date": p["scheduled_date"],
                    "Actual Date": p["actual_date"] or "",
                })

        move_fieldnames = [
            "External ID", "Picking", "Product", "Location",
            "Quantity", "State",
        ]

        with open(move_filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=move_fieldnames)
            writer.writeheader()

            for m in self.moves:
                writer.writerow({
                    "External ID": m["id"],
                    "Picking": m["picking_id"],
                    "Product": m["product_id"],
                    "Location": m["location_id"],
                    "Quantity": m["quantity"],
                    "State": m["state"],
                })

        return picking_filepath, move_filepath


def build_all(output_dir: str = str(DEFAULT_OUTPUT_DIR)):
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    generated_files = []

    print("Building products...")
    product_builder = ProductBuilder(output_path)
    products = product_builder.generate_products(100)
    product_file = product_builder.to_csv()
    generated_files.append(("product.template.csv", product_file))
    print(f"  Created: {product_file.name}")

    print("Building partners...")
    partner_builder = PartnerBuilder(output_path)
    partners = partner_builder.generate_customers(500)
    partner_file = partner_builder.to_csv()
    generated_files.append(("res.partner.csv", partner_file))
    print(f"  Created: {partner_file.name}")

    print("Building orders...")
    order_builder = OrderBuilder(output_path, products, partners)
    orders = order_builder.generate_orders(1000)
    order_file, line_file = order_builder.to_csv()
    generated_files.append(("sale.order.csv", order_file))
    generated_files.append(("sale.order.line.csv", line_file))
    print(f"  Created: {order_file.name}, {line_file.name}")

    print("Building inventory...")
    inventory_builder = InventoryBuilder(output_path, products)
    inventory_builder.generate_inventory()
    inventory_file = inventory_builder.to_csv()
    generated_files.append(("stock.quant.csv", inventory_file))
    print(f"  Created: {inventory_file.name}")

    print("Building order audits...")
    audit_builder = OrderAuditBuilder(output_path, orders)
    audit_builder.generate_audits()
    audit_file = audit_builder.to_csv()
    generated_files.append(("order_audit.csv", audit_file))
    print(f"  Created: {audit_file.name}")

    print("Building order exceptions...")
    exception_builder = OrderExceptionBuilder(output_path, orders)
    exception_builder.generate_exceptions()
    exception_file = exception_builder.to_csv()
    generated_files.append(("order_exception.csv", exception_file))
    print(f"  Created: {exception_file.name}")

    print("Building fulfillment...")
    fulfillment_builder = FulfillmentBuilder(output_path, orders)
    fulfillment_builder.generate_fulfillment()
    picking_file, move_file = fulfillment_builder.to_csv()
    generated_files.append(("stock.picking.csv", picking_file))
    generated_files.append(("stock.move.csv", move_file))
    print(f"  Created: {picking_file.name}, {move_file.name}")

    print("\n" + "=" * 60)
    print("SEED BUILDER COMPLETE")
    print("=" * 60)
    print(f"\nGenerated files:")
    for filename, filepath in generated_files:
        print(f"  - {filename}")
    print(f"\nTotal: {len(generated_files)} files")
    print(f"Location: {output_path.absolute()}")
    print("=" * 60)

    return {
        "products": len(products),
        "partners": len(partners),
        "orders": len(orders),
        "order_lines": len(order_builder.order_lines),
        "quants": len(inventory_builder.quants),
        "audits": len(audit_builder.audits),
        "exceptions": len(exception_builder.exceptions),
        "pickings": len(fulfillment_builder.pickings),
        "moves": len(fulfillment_builder.moves),
        "files": [f[0] for f in generated_files],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Odoo seed CSV files.")
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory where generated CSV files will be written.",
    )
    args = parser.parse_args()
    build_all(args.output_dir)
