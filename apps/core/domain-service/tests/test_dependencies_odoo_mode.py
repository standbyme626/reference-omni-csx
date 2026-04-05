from app.core.config import settings
from app.dependencies import get_odoo_provider

from providers.odoo.provider import OdooProviderMode


def test_get_odoo_provider_defaults_to_real_when_mode_is_empty():
    original_odoo_mode = settings.odoo_provider_mode
    original_default_provider_mode = settings.default_provider_mode
    get_odoo_provider.cache_clear()
    try:
        settings.odoo_provider_mode = ""
        settings.default_provider_mode = "mock"

        provider = get_odoo_provider()

        assert provider.mode == OdooProviderMode.REAL
    finally:
        settings.odoo_provider_mode = original_odoo_mode
        settings.default_provider_mode = original_default_provider_mode
        get_odoo_provider.cache_clear()


def test_get_odoo_provider_respects_explicit_mock_mode():
    original_odoo_mode = settings.odoo_provider_mode
    get_odoo_provider.cache_clear()
    try:
        settings.odoo_provider_mode = "mock"

        provider = get_odoo_provider()

        assert provider.mode == OdooProviderMode.MOCK
    finally:
        settings.odoo_provider_mode = original_odoo_mode
        get_odoo_provider.cache_clear()
