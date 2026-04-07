"""Test adapter registry capabilities."""
from app.adapters.registry import AdapterRegistry, bootstrap_default_registry
from app.models.unified import Platform


class TestPlatformRegistry:
    def test_registry_initialization(self):
        registry = AdapterRegistry()
        assert registry is not None

    def test_bootstrap_registers_all_platforms(self):
        registry = bootstrap_default_registry()
        platforms = registry.list_platforms()
        assert len(platforms) == 6

    def test_get_capabilities_via_has_capability(self):
        registry = bootstrap_default_registry()
        assert registry.has_capability(Platform.TAOBAO, "order") is True
        assert registry.has_capability(Platform.TAOBAO, "conversation") is False
        assert registry.has_capability(Platform.WECOM_KF, "conversation") is True
        assert registry.has_capability(Platform.WECOM_KF, "order") is False


class TestPlatformCapabilities:
    def test_taobao_capabilities(self):
        registry = bootstrap_default_registry()
        assert registry.has_capability(Platform.TAOBAO, "order") is True
        assert registry.has_capability(Platform.TAOBAO, "shipment") is False
        assert registry.has_capability(Platform.TAOBAO, "after_sale") is False
        assert registry.has_capability(Platform.TAOBAO, "conversation") is False

    def test_douyin_capabilities(self):
        registry = bootstrap_default_registry()
        for cap in ("order", "shipment", "after_sale"):
            assert registry.has_capability(Platform.DOUYIN_SHOP, cap) is True
        assert registry.has_capability(Platform.DOUYIN_SHOP, "conversation") is False

    def test_wecom_kf_capabilities(self):
        registry = bootstrap_default_registry()
        assert registry.has_capability(Platform.WECOM_KF, "conversation") is True
        for cap in ("order", "shipment", "after_sale"):
            assert registry.has_capability(Platform.WECOM_KF, cap) is False

    def test_all_platforms_have_capabilities(self):
        registry = bootstrap_default_registry()
        platforms = [
            Platform.TAOBAO, Platform.DOUYIN_SHOP, Platform.JD,
            Platform.XHS, Platform.KUAISHOU, Platform.WECOM_KF,
        ]
        for platform in platforms:
            assert registry.is_registered(platform) is True
