from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from models.unified import (
    UnifiedOrder,
    UnifiedShipment,
    UnifiedRefund,
    UnifiedConversation,
    Platform,
)


@dataclass
class PlatformContract:
    platform: Platform
    supports_order: bool = True
    supports_shipment: bool = True
    supports_after_sale: bool = True
    supports_conversation: bool = False


class BaseAdapter(ABC):
    platform: Platform
    
    @abstractmethod
    def to_unified_order(self, platform_data: Dict[str, Any]) -> UnifiedOrder:
        pass
    
    @abstractmethod
    def to_unified_shipment(self, platform_data: Dict[str, Any]) -> UnifiedShipment:
        pass
    
    @abstractmethod
    def to_unified_refund(self, platform_data: Dict[str, Any]) -> UnifiedRefund:
        pass
    
    @abstractmethod
    def to_unified_conversation(self, platform_data: Dict[str, Any]) -> UnifiedConversation:
        pass
    
    @abstractmethod
    def from_unified_order(self, unified: UnifiedOrder) -> Dict[str, Any]:
        pass
    
    def get_contract(self) -> PlatformContract:
        return PlatformContract(platform=self.platform)
