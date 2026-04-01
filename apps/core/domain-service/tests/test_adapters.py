import pytest
from datetime import datetime

from adapters.platform_adapter import (
    TaobaoAdapter,
    DouyinShopAdapter,
    JDAdapter,
    XhsAdapter,
    KuaishouAdapter,
    WecomKfAdapter,
)
from models.unified import Platform, OrderStatus


class TestTaobaoAdapter:
    def test_to_unified_order(self):
        platform_data = {
            "trade": {
                "tid": "TB_ORDER_001",
                "status": "WAIT_SELLER_SEND_GOODS",
                "total_fee": "299.00",
                "payment": "299.00",
                "receiver_name": "张三",
                "receiver_phone": "138****0000",
                "receiver_address": "浙江省杭州市余杭区",
                "created": "2026-03-01T10:00:00",
                "modified": "2026-03-29T12:00:00",
            },
            "orders": {
                "order": [
                    {
                        "oid": "TB_ITEM_001",
                        "title": "测试商品",
                        "price": "299.00",
                        "num": 1,
                    }
                ]
            },
        }
        
        unified = TaobaoAdapter.to_unified_order(platform_data)
        
        assert unified.order_id == "TB_ORDER_001"
        assert unified.platform == Platform.TAOBAO
        assert unified.status == OrderStatus.WAIT_SHIP
        assert unified.total_amount == "299.00"
        assert unified.receiver.name == "张三"
        assert len(unified.products) == 1
    
    def test_from_unified_order(self):
        from models.unified import UnifiedOrder, UnifiedAddress, UnifiedProduct
        
        unified = UnifiedOrder(
            order_id="TB_ORDER_001",
            platform=Platform.TAOBAO,
            status=OrderStatus.WAIT_SHIP,
            total_amount="299.00",
            pay_amount="299.00",
            receiver=UnifiedAddress(name="张三", phone="138****0000", address="浙江省杭州市"),
            products=[UnifiedProduct(product_id="001", name="测试商品", price="299.00", quantity=1)],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        platform_data = TaobaoAdapter.from_unified_order(unified)
        
        assert platform_data["trade"]["tid"] == "TB_ORDER_001"
        assert platform_data["trade"]["status"] == "wait_ship"


class TestJDAdapter:
    def test_to_unified_order(self):
        platform_data = {
            "order_id": "JD_ORDER_001",
            "status": "wait_seller_delivery",
            "total_amount": "199.00",
            "pay_amount": "199.00",
            "freight": "0.00",
            "receiver": {
                "name": "李四",
                "phone": "139****0000",
                "address": "北京市朝阳区",
            },
            "items": [
                {
                    "item_id": "JD_ITEM_001",
                    "name": "京东商品",
                    "price": "199.00",
                    "quantity": 1,
                }
            ],
            "create_time": "2026-03-01T10:00:00",
            "update_time": "2026-03-29T12:00:00",
        }
        
        unified = JDAdapter.to_unified_order(platform_data)
        
        assert unified.order_id == "JD_ORDER_001"
        assert unified.platform == Platform.JD
        assert unified.status == OrderStatus.WAIT_SHIP
        assert unified.total_amount == "199.00"
        assert unified.receiver.name == "李四"


class TestXhsAdapter:
    def test_to_unified_order(self):
        platform_data = {
            "order_id": "XHS_ORDER_001",
            "status": "delivering",
            "total_amount": "149.99",
            "pay_amount": "149.99",
            "freight": "0.00",
            "receiver": {
                "name": "王五",
                "phone": "137****0000",
                "address": "广东省广州市天河区",
            },
            "items": [
                {
                    "item_id": "XHS_ITEM_001",
                    "name": "小红书商品",
                    "price": "149.99",
                    "quantity": 1,
                }
            ],
            "create_time": "2026-03-01T10:00:00",
            "update_time": "2026-03-29T12:00:00",
        }
        
        unified = XhsAdapter.to_unified_order(platform_data)
        
        assert unified.order_id == "XHS_ORDER_001"
        assert unified.platform == Platform.XHS
        assert unified.status == OrderStatus.IN_TRANSIT


class TestKuaishouAdapter:
    def test_to_unified_order(self):
        platform_data = {
            "order_id": "KS_ORDER_001",
            "status": "delivered",
            "total_amount": "129.99",
            "pay_amount": "129.99",
            "freight": "0.00",
            "receiver": {
                "name": "赵六",
                "phone": "136****0000",
                "address": "四川省成都市锦江区",
            },
            "products": [
                {
                    "product_id": "KS_ITEM_001",
                    "name": "快手商品",
                    "price": "129.99",
                    "quantity": 1,
                }
            ],
            "create_time": "2026-03-01T10:00:00",
            "update_time": "2026-03-29T12:00:00",
        }
        
        unified = KuaishouAdapter.to_unified_order(platform_data)
        
        assert unified.order_id == "KS_ORDER_001"
        assert unified.platform == Platform.KUAISHOU
        assert unified.status == OrderStatus.FINISHED
