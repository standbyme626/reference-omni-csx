"""Provider Factory for Kuaishou integration."""

import os
from providers.kuaishou.mock.provider import KuaishouMockProvider
from providers.kuaishou.real.provider import KuaishouRealProvider


class ProviderConfigError(Exception):
    pass


def get_kuaishou_provider():
    mode = os.getenv("KUAISHOU_PROVIDER_MODE", "mock").lower()
    if mode == "mock":
        base_url = os.getenv("KUAISHOU_MOCK_BASE_URL", "http://localhost:8200")
        return KuaishouMockProvider(base_url=base_url)
    if mode == "real":
        required = ["KUAISHOU_APP_KEY", "KUAISHOU_APP_SECRET"]
        missing = [v for v in required if not os.getenv(v)]
        if missing:
            raise ProviderConfigError(f"KUAISHOU_PROVIDER_MODE=real but missing: {', '.join(missing)}")
        return KuaishouRealProvider()
    raise ProviderConfigError(f"Invalid KUAISHOU_PROVIDER_MODE: {mode}. Must be 'mock' or 'real'.")
