"""Provider Factory for JD integration."""

import os

from providers.jd.mock.provider import JdMockProvider
from providers.jd.real.provider import JdRealProvider


class ProviderConfigError(Exception):
    pass


def get_jd_provider():
    mode = os.getenv("JD_PROVIDER_MODE", "mock").lower()

    if mode == "mock":
        base_url = os.getenv("JD_MOCK_BASE_URL", "http://localhost:8200")
        return JdMockProvider(base_url=base_url)

    if mode == "real":
        required = ["JD_APP_KEY", "JD_APP_SECRET"]
        missing = [v for v in required if not os.getenv(v)]
        if missing:
            raise ProviderConfigError(f"JD_PROVIDER_MODE=real but missing: {', '.join(missing)}")
        return JdRealProvider()

    raise ProviderConfigError(f"Invalid JD_PROVIDER_MODE: {mode}. Must be 'mock' or 'real'.")
