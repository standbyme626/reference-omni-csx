from typing import Dict, Any, List
from datetime import datetime, timedelta
from collections import defaultdict


class AnalyticsService:
    def __init__(self):
        pass

    def get_orders_summary(self, platform: str = "all") -> Dict[str, Any]:
        return {
            "platform": platform,
            "total_orders": 0,
            "status_breakdown": {
                "pending": 0,
                "paid": 0,
                "shipped": 0,
                "delivered": 0,
                "cancelled": 0,
            },
            "total_amount": "0.00",
            "average_order_value": "0.00",
            "generated_at": datetime.now().isoformat(),
        }

    def get_conversations_summary(self, platform: str = "all") -> Dict[str, Any]:
        return {
            "platform": platform,
            "total_conversations": 0,
            "status_breakdown": {
                "pending": 0,
                "in_session": 0,
                "closed": 0,
            },
            "average_response_time": 0,
            "generated_at": datetime.now().isoformat(),
        }

    def get_platforms_coverage(self) -> Dict[str, Any]:
        return {
            "platforms": [
                {
                    "name": "taobao",
                    "display_name": "淘宝",
                    "status": "active",
                    "capabilities": ["order", "shipment", "after_sale"],
                },
                {
                    "name": "douyin_shop",
                    "display_name": "抖店",
                    "status": "active",
                    "capabilities": ["order", "shipment", "after_sale"],
                },
                {
                    "name": "jd",
                    "display_name": "京东",
                    "status": "active",
                    "capabilities": ["order", "shipment", "after_sale"],
                },
                {
                    "name": "xhs",
                    "display_name": "小红书",
                    "status": "active",
                    "capabilities": ["order", "shipment", "after_sale"],
                },
                {
                    "name": "kuaishou",
                    "display_name": "快手",
                    "status": "active",
                    "capabilities": ["order", "shipment", "after_sale"],
                },
                {
                    "name": "wecom_kf",
                    "display_name": "企微客服",
                    "status": "active",
                    "capabilities": ["conversation"],
                },
            ],
            "total_platforms": 6,
            "generated_at": datetime.now().isoformat(),
        }
