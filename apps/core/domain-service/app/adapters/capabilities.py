from typing import Dict, Any, List, Optional, Type
from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass, field

from models.unified import (
    UnifiedOrder,
    UnifiedShipment,
    UnifiedRefund,
    UnifiedConversation,
    Platform,
)


class PlatformCapability(str, Enum):
    ORDER = "order"
    SHIPMENT = "shipment"
    AFTER_SALE = "after_sale"
    CONVERSATION = "conversation"
    MESSAGE = "message"


@dataclass
class PlatformCapabilities:
    platform: Platform
    capabilities: List[PlatformCapability] = field(default_factory=list)
    
    def supports(self, capability: PlatformCapability) -> bool:
        return capability in self.capabilities
    
    def supports_order(self) -> bool:
        return self.supports(PlatformCapability.ORDER)
    
    def supports_shipment(self) -> bool:
        return self.supports(PlatformCapability.SHIPMENT)
    
    def supports_after_sale(self) -> bool:
        return self.supports(PlatformCapability.AFTER_SALE)
    
    def supports_conversation(self) -> bool:
        return self.supports(PlatformCapability.CONVERSATION)


PLATFORM_CAPABILITIES: Dict[Platform, PlatformCapabilities] = {
    Platform.TAOBAO: PlatformCapabilities(
        platform=Platform.TAOBAO,
        capabilities=[
            PlatformCapability.ORDER,
            PlatformCapability.SHIPMENT,
            PlatformCapability.AFTER_SALE,
        ],
    ),
    Platform.DOUYIN_SHOP: PlatformCapabilities(
        platform=Platform.DOUYIN_SHOP,
        capabilities=[
            PlatformCapability.ORDER,
            PlatformCapability.SHIPMENT,
            PlatformCapability.AFTER_SALE,
        ],
    ),
    Platform.JD: PlatformCapabilities(
        platform=Platform.JD,
        capabilities=[
            PlatformCapability.ORDER,
            PlatformCapability.SHIPMENT,
            PlatformCapability.AFTER_SALE,
        ],
    ),
    Platform.XHS: PlatformCapabilities(
        platform=Platform.XHS,
        capabilities=[
            PlatformCapability.ORDER,
            PlatformCapability.SHIPMENT,
            PlatformCapability.AFTER_SALE,
        ],
    ),
    Platform.KUAISHOU: PlatformCapabilities(
        platform=Platform.KUAISHOU,
        capabilities=[
            PlatformCapability.ORDER,
            PlatformCapability.SHIPMENT,
            PlatformCapability.AFTER_SALE,
        ],
    ),
    Platform.WECOM_KF: PlatformCapabilities(
        platform=Platform.WECOM_KF,
        capabilities=[
            PlatformCapability.CONVERSATION,
            PlatformCapability.MESSAGE,
        ],
    ),
}


def get_platform_capabilities(platform: Platform) -> PlatformCapabilities:
    return PLATFORM_CAPABILITIES.get(
        platform,
        PlatformCapabilities(platform=platform, capabilities=[])
    )
