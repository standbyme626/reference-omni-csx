"""Provider Factory for Taobao integration."""

import os
from providers.taobao.mock.provider import TaobaoMockProvider
from providers.taobao.real.provider import TaobaoRealProvider


class ProviderConfigError(Exception):
    pass


def get_taobao_provider():
    mode = os.getenv("TAOBAO_PROVIDER_MODE", "mock").lower()
    if mode == "mock":
        base_url = os.getenv("TAOBAO_MOCK_BASE_URL", "http://localhost:8200")
        return TaobaoMockProvider(base_url=base_url)
    if mode == "real":
        required = ["TAOBAO_APP_KEY", "TAOBAO_APP_SECRET"]
        missing = [v for v in required if not os.getenv(v)]
        if missing:
            raise ProviderConfigError(f"TAOBAO_PROVIDER_MODE=real but missing: {', '.join(missing)}")
        return TaobaoRealProvider()
    raise ProviderConfigError(f"Invalid TAOBAO_PROVIDER_MODE: {mode}. Must be 'mock' or 'real'.")
