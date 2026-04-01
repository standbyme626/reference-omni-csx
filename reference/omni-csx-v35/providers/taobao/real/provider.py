"""Taobao real provider - V1 skeleton for future extension."""

import os


class TaobaoRealProvider:
    def __init__(self, app_key: str = None, app_secret: str = None):
        self.app_key = app_key or os.getenv("TAOBAO_APP_KEY", "")
        self.app_secret = app_secret or os.getenv("TAOBAO_APP_SECRET", "")
        self.base_url = "https://eco.taobao.com/router/rest"

    def get_platform(self) -> str:
        return "taobao"

    def get_order(self, order_id: str) -> dict:
        return {"error": "V1 real provider not implemented", "order_id": order_id}

    def get_shipment(self, order_id: str) -> dict:
        return {"error": "V1 real provider not implemented", "order_id": order_id}

    def get_after_sale(self, after_sale_id: str) -> dict:
        return {"error": "V1 real provider not implemented", "after_sale_id": after_sale_id}
