"""Provider Factory for WeCom KF integration."""

import os

from providers.wecom_kf.mock.provider import WecomKfMockProvider
from providers.wecom_kf.real.provider import WecomKfRealProvider


class ProviderConfigError(Exception):
    pass


def get_wecom_kf_provider():
    mode = os.getenv("WECOM_PROVIDER_MODE", "mock").lower()

    if mode == "mock":
        return WecomKfMockProvider()

    if mode == "real":
        required = ["WECOM_CORP_ID", "WECOM_KF_SECRET"]
        missing = [v for v in required if not os.getenv(v)]
        if missing:
            raise ProviderConfigError(f"WECOM_PROVIDER_MODE=real but missing: {', '.join(missing)}")
        return WecomKfRealProvider()

    raise ProviderConfigError(f"Invalid WECOM_PROVIDER_MODE: {mode}. Must be 'mock' or 'real'.")
