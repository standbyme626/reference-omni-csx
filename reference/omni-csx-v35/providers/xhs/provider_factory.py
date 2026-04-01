"""Provider Factory for XHS integration."""

import os
from providers.xhs.mock.provider import XhsMockProvider
from providers.xhs.real.provider import XhsRealProvider


class ProviderConfigError(Exception):
    pass


def get_xhs_provider():
    mode = os.getenv("XHS_PROVIDER_MODE", "mock").lower()
    if mode == "mock":
        base_url = os.getenv("XHS_MOCK_BASE_URL", "http://localhost:8200")
        return XhsMockProvider(base_url=base_url)
    if mode == "real":
        required = ["XHS_APP_KEY", "XHS_APP_SECRET"]
        missing = [v for v in required if not os.getenv(v)]
        if missing:
            raise ProviderConfigError(f"XHS_PROVIDER_MODE=real but missing: {', '.join(missing)}")
        return XhsRealProvider()
    raise ProviderConfigError(f"Invalid XHS_PROVIDER_MODE: {mode}. Must be 'mock' or 'real'.")
