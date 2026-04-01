from typing import Dict, Any
from models.unified import (
    UnifiedOrder,
    UnifiedShipment,
    UnifiedRefund,
    UnifiedConversation,
    Platform,
)
from app.adapters.contracts import BaseAdapter
from adapters.platform_adapter import (
    TaobaoAdapter as TaobaoAdapterStatic,
    DouyinShopAdapter as DouyinShopAdapterStatic,
    WecomKfAdapter as WecomKfAdapterStatic,
    JDAdapter as JDAdapterStatic,
    XhsAdapter as XhsAdapterStatic,
    KuaishouAdapter as KuaishouAdapterStatic,
)


class TaobaoAdapter(BaseAdapter):
    platform = Platform.TAOBAO
    
    def to_unified_order(self, platform_data: Dict[str, Any]) -> UnifiedOrder:
        return TaobaoAdapterStatic.to_unified_order(platform_data)
    
    def to_unified_shipment(self, platform_data: Dict[str, Any]) -> UnifiedShipment:
        raise NotImplementedError("Taobao shipment adapter not implemented")
    
    def to_unified_refund(self, platform_data: Dict[str, Any]) -> UnifiedRefund:
        raise NotImplementedError("Taobao refund adapter not implemented")
    
    def to_unified_conversation(self, platform_data: Dict[str, Any]) -> UnifiedConversation:
        raise NotImplementedError("Taobao does not support conversation")
    
    def from_unified_order(self, unified: UnifiedOrder) -> Dict[str, Any]:
        return TaobaoAdapterStatic.from_unified_order(unified)


class DouyinShopAdapter(BaseAdapter):
    platform = Platform.DOUYIN_SHOP
    
    def to_unified_order(self, platform_data: Dict[str, Any]) -> UnifiedOrder:
        return DouyinShopAdapterStatic.to_unified_order(platform_data)
    
    def to_unified_shipment(self, platform_data: Dict[str, Any]) -> UnifiedShipment:
        raise NotImplementedError("DouyinShop shipment adapter not implemented")
    
    def to_unified_refund(self, platform_data: Dict[str, Any]) -> UnifiedRefund:
        raise NotImplementedError("DouyinShop refund adapter not implemented")
    
    def to_unified_conversation(self, platform_data: Dict[str, Any]) -> UnifiedConversation:
        raise NotImplementedError("DouyinShop does not support conversation")
    
    def from_unified_order(self, unified: UnifiedOrder) -> Dict[str, Any]:
        return DouyinShopAdapterStatic.from_unified_order(unified)


class JdAdapter(BaseAdapter):
    platform = Platform.JD
    
    def to_unified_order(self, platform_data: Dict[str, Any]) -> UnifiedOrder:
        return JDAdapterStatic.to_unified_order(platform_data)
    
    def to_unified_shipment(self, platform_data: Dict[str, Any]) -> UnifiedShipment:
        raise NotImplementedError("JD shipment adapter not implemented")
    
    def to_unified_refund(self, platform_data: Dict[str, Any]) -> UnifiedRefund:
        raise NotImplementedError("JD refund adapter not implemented")
    
    def to_unified_conversation(self, platform_data: Dict[str, Any]) -> UnifiedConversation:
        raise NotImplementedError("JD does not support conversation")
    
    def from_unified_order(self, unified: UnifiedOrder) -> Dict[str, Any]:
        return JDAdapterStatic.from_unified_order(unified)


class XhsAdapter(BaseAdapter):
    platform = Platform.XHS
    
    def to_unified_order(self, platform_data: Dict[str, Any]) -> UnifiedOrder:
        return XhsAdapterStatic.to_unified_order(platform_data)
    
    def to_unified_shipment(self, platform_data: Dict[str, Any]) -> UnifiedShipment:
        raise NotImplementedError("XHS shipment adapter not implemented")
    
    def to_unified_refund(self, platform_data: Dict[str, Any]) -> UnifiedRefund:
        raise NotImplementedError("XHS refund adapter not implemented")
    
    def to_unified_conversation(self, platform_data: Dict[str, Any]) -> UnifiedConversation:
        raise NotImplementedError("XHS does not support conversation")
    
    def from_unified_order(self, unified: UnifiedOrder) -> Dict[str, Any]:
        return XhsAdapterStatic.from_unified_order(unified)


class KuaishouAdapter(BaseAdapter):
    platform = Platform.KUAISHOU
    
    def to_unified_order(self, platform_data: Dict[str, Any]) -> UnifiedOrder:
        return KuaishouAdapterStatic.to_unified_order(platform_data)
    
    def to_unified_shipment(self, platform_data: Dict[str, Any]) -> UnifiedShipment:
        raise NotImplementedError("Kuaishou shipment adapter not implemented")
    
    def to_unified_refund(self, platform_data: Dict[str, Any]) -> UnifiedRefund:
        raise NotImplementedError("Kuaishou refund adapter not implemented")
    
    def to_unified_conversation(self, platform_data: Dict[str, Any]) -> UnifiedConversation:
        raise NotImplementedError("Kuaishou does not support conversation")
    
    def from_unified_order(self, unified: UnifiedOrder) -> Dict[str, Any]:
        return KuaishouAdapterStatic.from_unified_order(unified)


class WecomKfAdapter(BaseAdapter):
    platform = Platform.WECOM_KF
    
    def to_unified_order(self, platform_data: Dict[str, Any]) -> UnifiedOrder:
        raise NotImplementedError("WecomKf does not support order")
    
    def to_unified_shipment(self, platform_data: Dict[str, Any]) -> UnifiedShipment:
        raise NotImplementedError("WecomKf does not support shipment")
    
    def to_unified_refund(self, platform_data: Dict[str, Any]) -> UnifiedRefund:
        raise NotImplementedError("WecomKf does not support refund")
    
    def to_unified_conversation(self, platform_data: Dict[str, Any]) -> UnifiedConversation:
        return WecomKfAdapterStatic.to_unified_conversation(platform_data)
    
    def from_unified_order(self, unified: UnifiedOrder) -> Dict[str, Any]:
        raise NotImplementedError("WecomKf does not support order")
