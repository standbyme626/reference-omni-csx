from datetime import datetime

from adapters.platform_adapter import (
    DouyinShopAdapter,
    JDAdapter,
    KuaishouAdapter,
    TaobaoAdapter,
    XhsAdapter,
)
from app.models.unified import OrderStatus, Platform


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
        from app.models.unified import UnifiedAddress, UnifiedOrder, UnifiedProduct
        
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

    def test_to_unified_order_from_official_wait_pay_fixture_uses_zero_paid_amount(self):
        platform_data = {
            "jingdong_order_search_responce": {
                "orderId": 98765432101234,
                "orderStatus": 31000,
                "orderStartTime": "2026-03-29 10:00:00",
                "orderStatusTime": "2026-03-29 10:00:00",
                "orderPurchaseTime": None,
                "buyerFullName": "张三",
                "buyerMobile": "138****0000",
                "buyerFullAddress": "浙江省杭州市余杭区文一西路999号",
                "orderTotalMoney": 19900,
                "orderBuyerPayableMoney": 19900,
                "orderFreightMoney": 0,
                "product": [
                    {
                        "skuId": 100012345678,
                        "skuName": "京东仿真商品A",
                        "jdPrice": 9900,
                        "num": 2,
                    }
                ],
            }
        }

        unified = JDAdapter.to_unified_order(platform_data)

        assert unified.status == OrderStatus.WAIT_PAY
        assert unified.total_amount == "199.00"
        assert unified.pay_amount == "0.00"
        assert unified.products[0].price == "99.00"

    def test_to_unified_order_from_official_shipped_fixture_maps_shipped_status(self):
        platform_data = {
            "jingdong_order_search_responce": {
                "orderId": 98765432101234,
                "orderStatus": 33040,
                "orderStartTime": "2026-03-29 10:00:00",
                "orderStatusTime": "2026-03-29 14:00:00",
                "orderPurchaseTime": "2026-03-29 10:05:00",
                "buyerFullName": "张三",
                "buyerMobile": "138****0000",
                "buyerFullAddress": "浙江省杭州市余杭区文一西路999号",
                "orderTotalMoney": 19900,
                "orderBuyerPayableMoney": 19900,
                "orderFreightMoney": 0,
                "product": [
                    {
                        "skuId": 100012345678,
                        "skuName": "京东仿真商品A",
                        "jdPrice": 9900,
                        "num": 2,
                    }
                ],
            }
        }

        unified = JDAdapter.to_unified_order(platform_data)

        assert unified.status == OrderStatus.SHIPPED
        assert unified.pay_amount == "199.00"


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


class TestDouyinShopAdapter:
    def test_to_unified_order_from_official_fixture_converts_minor_units(self):
        platform_data = {
            "order": {
                "order_id": "6912558345648290211",
                "order_status": 10,
                "create_time": 1743264000,
                "update_time": 1743264000,
                "order_amount": {
                    "total_amount": 19900,
                    "pay_amount": 0,
                    "freight_amount": 0,
                },
                "receiver": {
                    "name": "张三",
                    "phone": "138****0000",
                    "province": "浙江省",
                    "city": "杭州市",
                    "district": "余杭区",
                    "address": "文一西路999号",
                },
                "product_items": [
                    {
                        "product_id": "3520562294461467753",
                        "product_name": "抖店仿真商品A",
                        "product_count": 2,
                        "product_price": 9900,
                    }
                ],
            }
        }

        unified = DouyinShopAdapter.to_unified_order(platform_data)

        assert unified.order_id == "6912558345648290211"
        assert unified.status == OrderStatus.WAIT_PAY
        assert unified.total_amount == "199.00"
        assert unified.pay_amount == "0.00"
        assert unified.products[0].price == "99.00"
