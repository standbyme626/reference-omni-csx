from typing import Dict, Any, Optional
from datetime import datetime

from app.adapters.registry import PlatformRegistry
from app.adapters.capabilities import PlatformCapability
from app.adapters.contracts import BaseAdapter
from models.unified import Platform, UnifiedOrder, UnifiedShipment, UnifiedRefund, UnifiedConversation
from providers.base.provider import ProviderMode
from providers.taobao.provider import TaobaoProvider
from providers.douyin_shop.provider import DouyinShopProvider
from providers.jd.provider import JdProvider
from providers.xhs.provider import XhsProvider
from providers.kuaishou.provider import KuaishouProvider
from providers.wecom_kf.provider import WecomKfProvider


class PlatformGatewayService:
    def __init__(self, registry: PlatformRegistry):
        self.registry = registry
        self._providers: Dict[Platform, Any] = {}
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
                provider = provider_class(mode=ProviderMode.MOCK)
                self._providers[platform] = provider
            except Exception:
                pass
    
    def get_provider(self, platform: Platform) -> Optional[Any]:
        return self._providers.get(platform)
    
    def get_adapter(self, platform: Platform) -> Optional[BaseAdapter]:
        return self.registry.get_adapter(platform)
    
    def has_provider(self, platform: Platform) -> bool:
        return platform in self._providers
    
    def has_adapter(self, platform: Platform) -> bool:
        return self.registry.is_registered(platform)
    
    def get_order(self, platform: Platform, order_id: str) -> Dict[str, Any]:
        provider = self.get_provider(platform)
        if not provider:
            raise ValueError(f"Platform not supported: {platform}")
        
        caps = self.registry.get_capabilities(platform)
        if not caps.supports_order():
            raise ValueError(f"Platform {platform} does not support order operations")
        
        return provider.get_order(order_id)
    
    def get_unified_order(self, platform: Platform, order_id: str) -> UnifiedOrder:
        platform_data = self.get_order(platform, order_id)
        
        adapter = self.get_adapter(platform)
        if not adapter:
            raise ValueError(f"No adapter registered for platform: {platform}")
        
        return adapter.to_unified_order(platform_data)
    
    def get_shipment(self, platform: Platform, order_id: str) -> Dict[str, Any]:
        provider = self.get_provider(platform)
        if not provider:
            raise ValueError(f"Platform not supported: {platform}")
        
        caps = self.registry.get_capabilities(platform)
        if not caps.supports_shipment():
            raise ValueError(f"Platform {platform} does not support shipment operations")
        
        return provider.get_shipment(order_id)
    
    def get_unified_shipment(self, platform: Platform, order_id: str) -> UnifiedShipment:
        platform_data = self.get_shipment(platform, order_id)
        
        adapter = self.get_adapter(platform)
        if not adapter:
            raise ValueError(f"No adapter registered for platform: {platform}")
        
        return adapter.to_unified_shipment(platform_data)
    
    def get_refund(self, platform: Platform, refund_id: str) -> Dict[str, Any]:
        provider = self.get_provider(platform)
        if not provider:
            raise ValueError(f"Platform not supported: {platform}")
        
        caps = self.registry.get_capabilities(platform)
        if not caps.supports_after_sale():
            raise ValueError(f"Platform {platform} does not support after-sale operations")
        
        return provider.get_refund(refund_id)
    
    def get_unified_refund(self, platform: Platform, refund_id: str) -> UnifiedRefund:
        platform_data = self.get_refund(platform, refund_id)
        
        adapter = self.get_adapter(platform)
        if not adapter:
            raise ValueError(f"No adapter registered for platform: {platform}")
        
        return adapter.to_unified_refund(platform_data)
    
    def get_conversation(self, platform: Platform, conversation_id: str) -> Dict[str, Any]:
        provider = self.get_provider(platform)
        if not provider:
            raise ValueError(f"Platform not supported: {platform}")
        
        caps = self.registry.get_capabilities(platform)
        if not caps.supports_conversation():
            raise ValueError(f"Platform {platform} does not support conversation operations")
        
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
