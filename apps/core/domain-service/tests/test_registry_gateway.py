import pytest
from app.adapters.registry import PlatformRegistry, bootstrap_default_registry
from app.core.config import Environment, settings
from app.services.official_sim_provider import OfficialSimProxyProvider
from app.services.platform_gateway_service import PlatformGatewayService
from app.models.unified import Platform


class TestRegistryBootstrap:
    def test_bootstrap_default_registry(self):
        registry = bootstrap_default_registry()
        
        assert isinstance(registry, PlatformRegistry)
        assert len(registry.list_platforms()) == 6
    
    def test_all_six_platforms_registered(self):
        registry = bootstrap_default_registry()
        
        expected_platforms = [
            Platform.TAOBAO,
            Platform.DOUYIN_SHOP,
            Platform.JD,
            Platform.XHS,
            Platform.KUAISHOU,
            Platform.WECOM_KF,
        ]
        
        for platform in expected_platforms:
            assert registry.is_registered(platform), f"Platform {platform} not registered"
    
    def test_get_adapter_for_each_platform(self):
        registry = bootstrap_default_registry()
        
        for platform in registry.list_platforms():
            adapter = registry.get_adapter(platform)
            assert adapter is not None, f"No adapter for platform {platform}"
            assert adapter.platform == platform
    
    def test_get_capabilities_for_each_platform(self):
        registry = bootstrap_default_registry()
        
        for platform in registry.list_platforms():
            caps = registry.get_capabilities(platform)
            assert caps is not None, f"No capabilities for platform {platform}"
    
    def test_wecom_kf_conversation_first(self):
        registry = bootstrap_default_registry()
        
        caps = registry.get_capabilities(Platform.WECOM_KF)
        assert caps.supports_conversation() is True
        assert caps.supports_order() is False
    
    def test_taobao_order_first(self):
        registry = bootstrap_default_registry()
        
        caps = registry.get_capabilities(Platform.TAOBAO)
        assert caps.supports_order() is True
        assert caps.supports_conversation() is False


class TestGatewayWithRegistry:
    @pytest.fixture
    def gateway(self):
        original_mode = settings.default_provider_mode
        settings.default_provider_mode = "mock"
        registry = bootstrap_default_registry()
        gateway = PlatformGatewayService(registry)
        settings.default_provider_mode = original_mode
        return gateway
    
    def test_gateway_has_adapter_for_all_platforms(self, gateway):
        for platform in gateway.list_platforms():
            assert gateway.has_adapter(platform), f"Gateway missing adapter for {platform}"
    
    def test_gateway_has_provider_for_all_platforms(self, gateway):
        for platform in gateway.list_platforms():
            assert gateway.has_provider(platform), f"Gateway missing provider for {platform}"
    
    def test_gateway_is_platform_supported(self, gateway):
        for platform in gateway.list_platforms():
            assert gateway.is_platform_supported(platform), f"Platform {platform} not fully supported"
    
    def test_gateway_get_adapter(self, gateway):
        for platform in gateway.list_platforms():
            adapter = gateway.get_adapter(platform)
            assert adapter is not None
            assert adapter.platform == platform
    
    def test_gateway_order_query_returns_payload(self, gateway):
        result = gateway.get_order(Platform.TAOBAO, "ORDER_999")
        assert result is not None
    
    def test_gateway_wecom_kf_conversation_capability(self, gateway):
        caps = gateway.registry.get_capabilities(Platform.WECOM_KF)
        assert caps.supports_conversation() is True
        
        with pytest.raises(ValueError, match="does not support order operations"):
            gateway.get_order(Platform.WECOM_KF, "ORDER_001")
    
    def test_gateway_taobao_order_capability(self, gateway):
        caps = gateway.registry.get_capabilities(Platform.TAOBAO)
        assert caps.supports_order() is True

        with pytest.raises(ValueError, match="does not support conversation operations"):
            gateway.get_conversation(Platform.TAOBAO, "CONV_001")

    def test_official_sim_mock_fallback_only_enabled_in_development(self):
        original_mode = settings.default_provider_mode
        original_fallback = settings.official_sim_enable_mock_fallback
        original_environment = settings.environment
        try:
            settings.default_provider_mode = "official_sim"
            settings.official_sim_enable_mock_fallback = True
            settings.environment = Environment.DEVELOPMENT

            gateway = PlatformGatewayService(bootstrap_default_registry())
            provider = gateway.get_provider(Platform.TAOBAO)

            assert isinstance(provider, OfficialSimProxyProvider)
            assert provider.fallback_provider is not None
        finally:
            settings.default_provider_mode = original_mode
            settings.official_sim_enable_mock_fallback = original_fallback
            settings.environment = original_environment

    def test_official_sim_mock_fallback_disabled_outside_development(self):
        original_mode = settings.default_provider_mode
        original_fallback = settings.official_sim_enable_mock_fallback
        original_environment = settings.environment
        try:
            settings.default_provider_mode = "official_sim"
            settings.official_sim_enable_mock_fallback = True
            settings.environment = Environment.STAGING

            gateway = PlatformGatewayService(bootstrap_default_registry())
            provider = gateway.get_provider(Platform.TAOBAO)

            assert isinstance(provider, OfficialSimProxyProvider)
            assert provider.fallback_provider is None
        finally:
            settings.default_provider_mode = original_mode
            settings.official_sim_enable_mock_fallback = original_fallback
            settings.environment = original_environment
