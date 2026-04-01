import pytest

from app.adapters.registry import PlatformRegistry
from app.adapters.capabilities import PlatformCapabilities, PlatformCapability, get_platform_capabilities
from models.unified import Platform


class TestPlatformCapabilities:
    def test_taobao_capabilities(self):
        caps = get_platform_capabilities(Platform.TAOBAO)
        
        assert caps.supports_order() is True
        assert caps.supports_shipment() is True
        assert caps.supports_after_sale() is True
        assert caps.supports_conversation() is False
    
    def test_wecom_kf_capabilities(self):
        caps = get_platform_capabilities(Platform.WECOM_KF)
        
        assert caps.supports_order() is False
        assert caps.supports_shipment() is False
        assert caps.supports_after_sale() is False
        assert caps.supports_conversation() is True
    
    def test_all_platforms_have_capabilities(self):
        platforms = [
            Platform.TAOBAO,
            Platform.DOUYIN_SHOP,
            Platform.JD,
            Platform.XHS,
            Platform.KUAISHOU,
            Platform.WECOM_KF,
        ]
        
        for platform in platforms:
            caps = get_platform_capabilities(platform)
            assert caps.platform == platform
            assert len(caps.capabilities) > 0


class TestPlatformRegistry:
    def test_registry_initialization(self):
        registry = PlatformRegistry()
        
        assert registry is not None
    
    def test_get_capabilities(self):
        registry = PlatformRegistry()
        
        caps = registry.get_capabilities(Platform.TAOBAO)
        
        assert caps.platform == Platform.TAOBAO
        assert caps.supports_order() is True
    
    def test_list_platforms(self):
        registry = PlatformRegistry()
        
        platforms = registry.list_platforms()
        
        assert isinstance(platforms, list)
