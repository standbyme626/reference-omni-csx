"""Provider Factory for Douyin Shop integration."""

import os

from providers.douyin_shop.mock.provider import DouyinShopMockProvider
from providers.douyin_shop.real.provider import DouyinShopRealProvider


class ProviderConfigError(Exception):
    pass


def get_douyin_shop_provider():
    mode = os.getenv("DOUYIN_PROVIDER_MODE", "mock").lower()

    if mode == "mock":
        base_url = os.getenv("DOUYIN_MOCK_BASE_URL", "http://localhost:8200")
        return DouyinShopMockProvider(base_url=base_url)

    if mode == "real":
        required = ["DOUYIN_APP_KEY", "DOUYIN_APP_SECRET"]
        missing = [v for v in required if not os.getenv(v)]
        if missing:
            raise ProviderConfigError(f"DOUYIN_PROVIDER_MODE=real but missing: {', '.join(missing)}")
        return DouyinShopRealProvider()

    raise ProviderConfigError(f"Invalid DOUYIN_PROVIDER_MODE: {mode}. Must be 'mock' or 'real'.")
