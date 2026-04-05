from typing import Any, Dict, Optional

from app.adapters.contracts import BaseAdapter
from app.adapters.registry import PlatformRegistry
from app.core.config import Environment, settings
from app.services.official_sim_provider import OfficialSimProxyProvider
from models.unified import (
    Platform,
    UnifiedConversation,
    UnifiedOrder,
    UnifiedRefund,
    UnifiedShipment,
)

from providers.base.provider import ProviderMode
from providers.douyin_shop.provider import DouyinShopProvider
from providers.jd.provider import JdProvider
from providers.kuaishou.provider import KuaishouProvider
from providers.taobao.provider import TaobaoProvider
from providers.wecom_kf.provider import WecomKfProvider
from providers.xhs.provider import XhsProvider


class PlatformGatewayService:
    def __init__(self, registry: PlatformRegistry):
        self.registry = registry
        self._providers: Dict[Platform, Any] = {}
        self._provider_mode = (settings.default_provider_mode or "mock").lower()
        self._init_providers()
    
    def _init_providers(self):
        provider_classes = {
            Platform.TAOBAO: TaobaoProvider,
            Platform.DOUYIN_SHOP: DouyinShopProvider,
            Platform.JD: JdProvider,
            Platform.XHS: XhsProvider,
            Platform.KUAISHOU: KuaishouProvider,
            Platform.WECOM_KF: WecomKfProvider,
        }
        
        for platform, provider_class in provider_classes.items():
            try:
                if self._provider_mode == "official_sim":
                    fallback_provider = None
                    if self._allow_official_sim_mock_fallback():
                        fallback_provider = provider_class(mode=ProviderMode.MOCK)
                    provider = OfficialSimProxyProvider(
                        platform=platform.value,
                        base_url=settings.official_sim_base_url,
                        fallback_provider=fallback_provider,
                    )
                else:
                    mode = ProviderMode.REAL if self._provider_mode == "real" else ProviderMode.MOCK
                    provider = provider_class(mode=mode)
                self._providers[platform] = provider
            except Exception:
                pass

    def _allow_official_sim_mock_fallback(self) -> bool:
        if not settings.official_sim_enable_mock_fallback:
            return False
        return settings.environment == Environment.DEVELOPMENT
    
    def get_provider(self, platform: Platform) -> Optional[Any]:
        return self._providers.get(platform)
    
    def get_adapter(self, platform: Platform) -> Optional[BaseAdapter]:
        return self.registry.get_adapter(platform)
    
    def has_provider(self, platform: Platform) -> bool:
        return platform in self._providers
    
    def has_adapter(self, platform: Platform) -> bool:
        return self.registry.is_registered(platform)
    
    def get_order(
        self,
        platform: Platform,
        order_id: str,
        official_run_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        provider = self.get_provider(platform)
        if not provider:
            raise ValueError(f"Platform not supported: {platform}")
        
        caps = self.registry.get_capabilities(platform)
        if not caps.supports_order():
            raise ValueError(f"Platform {platform} does not support order operations")
        
        if isinstance(provider, OfficialSimProxyProvider):
            return provider.get_order(order_id, official_run_id=official_run_id)
        return provider.get_order(order_id)
    
    def get_unified_order(
        self,
        platform: Platform,
        order_id: str,
        official_run_id: Optional[str] = None,
    ) -> UnifiedOrder:
        platform_data = self.get_order(platform, order_id, official_run_id=official_run_id)
        
        adapter = self.get_adapter(platform)
        if not adapter:
            raise ValueError(f"No adapter registered for platform: {platform}")
        
        return adapter.to_unified_order(platform_data)
    
    def get_shipment(
        self,
        platform: Platform,
        order_id: str,
        official_run_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        provider = self.get_provider(platform)
        if not provider:
            raise ValueError(f"Platform not supported: {platform}")
        
        caps = self.registry.get_capabilities(platform)
        if not caps.supports_shipment():
            raise ValueError(f"Platform {platform} does not support shipment operations")
        
        if isinstance(provider, OfficialSimProxyProvider):
            return provider.get_shipment(order_id, official_run_id=official_run_id)
        return provider.get_shipment(order_id)
    
    def get_unified_shipment(self, platform: Platform, order_id: str) -> UnifiedShipment:
        platform_data = self.get_shipment(platform, order_id)
        
        adapter = self.get_adapter(platform)
        if not adapter:
            raise ValueError(f"No adapter registered for platform: {platform}")
        
        return adapter.to_unified_shipment(platform_data)
    
    def get_refund(
        self,
        platform: Platform,
        refund_id: str,
        official_run_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        provider = self.get_provider(platform)
        if not provider:
            raise ValueError(f"Platform not supported: {platform}")
        
        caps = self.registry.get_capabilities(platform)
        if not caps.supports_after_sale():
            raise ValueError(f"Platform {platform} does not support after-sale operations")
        
        if isinstance(provider, OfficialSimProxyProvider):
            return provider.get_refund(refund_id, official_run_id=official_run_id)
        return provider.get_refund(refund_id)

    def get_refund_by_order(
        self,
        platform: Platform,
        order_id: str,
        official_run_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        provider = self.get_provider(platform)
        if not provider:
            raise ValueError(f"Platform not supported: {platform}")

        caps = self.registry.get_capabilities(platform)
        if not caps.supports_after_sale():
            raise ValueError(f"Platform {platform} does not support after-sale operations")

        if isinstance(provider, OfficialSimProxyProvider):
            return provider.get_refund_by_order(order_id, official_run_id=official_run_id)
        if hasattr(provider, "get_refund_by_order"):
            return provider.get_refund_by_order(order_id)
        return provider.get_refund(order_id)
    
    def get_unified_refund(self, platform: Platform, refund_id: str) -> UnifiedRefund:
        platform_data = self.get_refund(platform, refund_id)
        
        adapter = self.get_adapter(platform)
        if not adapter:
            raise ValueError(f"No adapter registered for platform: {platform}")
        
        return adapter.to_unified_refund(platform_data)
    
    def get_conversation(
        self,
        platform: Platform,
        conversation_id: str,
        official_run_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        provider = self.get_provider(platform)
        if not provider:
            raise ValueError(f"Platform not supported: {platform}")
        
        caps = self.registry.get_capabilities(platform)
        if not caps.supports_conversation():
            raise ValueError(f"Platform {platform} does not support conversation operations")
        
        if isinstance(provider, OfficialSimProxyProvider):
            return provider.get_conversation(conversation_id, official_run_id=official_run_id)
        return provider.get_conversation(conversation_id)
    
    def get_unified_conversation(self, platform: Platform, conversation_id: str) -> UnifiedConversation:
        platform_data = self.get_conversation(platform, conversation_id)
        
        adapter = self.get_adapter(platform)
        if not adapter:
            raise ValueError(f"No adapter registered for platform: {platform}")
        
        return adapter.to_unified_conversation(platform_data)
    
    def list_platforms(self) -> list:
        return list(self._providers.keys())
    
    def get_supported_operations(self, platform: Platform) -> list:
        caps = self.registry.get_capabilities(platform)
        return [c.value for c in caps.capabilities]
    
    def is_platform_supported(self, platform: Platform) -> bool:
        return self.has_provider(platform) and self.has_adapter(platform)
