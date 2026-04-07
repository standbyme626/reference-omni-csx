"""Protocol-based adapter registry.

Each platform may register separate adapters for order, shipment, after-sale,
and conversation capabilities.  The registry exposes capability-specific getters
so callers can ask for exactly the adapter they need.
"""

from __future__ import annotations

from typing import Optional

from app.models.unified import Platform

from .protocols import (
    AfterSaleAdapter,
    ConversationAdapter,
    OrderAdapter,
    ShipmentAdapter,
)


class AdapterRegistry:
    """Central registry for protocol-based adapters."""

    def __init__(self) -> None:
        self._order_adapters: dict[Platform, OrderAdapter] = {}
        self._shipment_adapters: dict[Platform, ShipmentAdapter] = {}
        self._after_sale_adapters: dict[Platform, AfterSaleAdapter] = {}
        self._conversation_adapters: dict[Platform, ConversationAdapter] = {}

    # -- registration -------------------------------------------------------

    def register(
        self,
        platform: Platform,
        *,
        order_adapter: OrderAdapter | None = None,
        shipment_adapter: ShipmentAdapter | None = None,
        after_sale_adapter: AfterSaleAdapter | None = None,
        conversation_adapter: ConversationAdapter | None = None,
    ) -> None:
        if order_adapter is not None:
            self._order_adapters[platform] = order_adapter
        if shipment_adapter is not None:
            self._shipment_adapters[platform] = shipment_adapter
        if after_sale_adapter is not None:
            self._after_sale_adapters[platform] = after_sale_adapter
        if conversation_adapter is not None:
            self._conversation_adapters[platform] = conversation_adapter

    def unregister(self, platform: Platform) -> None:
        self._order_adapters.pop(platform, None)
        self._shipment_adapters.pop(platform, None)
        self._after_sale_adapters.pop(platform, None)
        self._conversation_adapters.pop(platform, None)

    # -- capability getters -------------------------------------------------

    def get_order_adapter(self, platform: Platform) -> OrderAdapter | None:
        return self._order_adapters.get(platform)

    def get_shipment_adapter(self, platform: Platform) -> ShipmentAdapter | None:
        return self._shipment_adapters.get(platform)

    def get_after_sale_adapter(self, platform: Platform) -> AfterSaleAdapter | None:
        return self._after_sale_adapters.get(platform)

    def get_conversation_adapter(self, platform: Platform) -> ConversationAdapter | None:
        return self._conversation_adapters.get(platform)

    # -- query helpers ------------------------------------------------------

    def list_platforms(self) -> list[str]:
        platforms: set[Platform] = set()
        platforms.update(self._order_adapters.keys())
        platforms.update(self._shipment_adapters.keys())
        platforms.update(self._after_sale_adapters.keys())
        platforms.update(self._conversation_adapters.keys())
        return [p.value for p in platforms]

    def has_capability(self, platform: Platform, capability: str) -> bool:
        capability_map = {
            "order": platform in self._order_adapters,
            "shipment": platform in self._shipment_adapters,
            "after_sale": platform in self._after_sale_adapters,
            "conversation": platform in self._conversation_adapters,
        }
        return capability_map.get(capability, False)

    # -- backward compatibility with the old PlatformRegistry ---------------

    _singleton: AdapterRegistry | None = None

    @classmethod
    def get_instance(cls) -> AdapterRegistry:
        if cls._singleton is None:
            cls._singleton = bootstrap_default_registry()
        return cls._singleton

    def get_adapter(self, platform: Platform) -> Optional["_LegacyAdapter"]:
        """Return a best-effort legacy adapter for code paths that still
        expect a single adapter object with to_unified_order etc."""

        order = self.get_order_adapter(platform)
        shipment = self.get_shipment_adapter(platform)
        after_sale = self.get_after_sale_adapter(platform)
        conversation = self.get_conversation_adapter(platform)

        if order is None and shipment is None and after_sale is None and conversation is None:
            return None
        return _LegacyAdapter(platform, order, shipment, after_sale, conversation)

    def get_capabilities(self, platform: Platform) -> "_LegacyCapabilities":
        """Return a capabilities object compatible with old callers."""
        return _LegacyCapabilities(platform, self)

    def get_supported_capabilities(self, platform: Platform) -> list[str]:
        caps: list[str] = []
        if self.has_capability(platform, "order"):
            caps.append("order")
        if self.has_capability(platform, "shipment"):
            caps.append("shipment")
        if self.has_capability(platform, "after_sale"):
            caps.append("after_sale")
        if self.has_capability(platform, "conversation"):
            caps.append("conversation")
        return caps

    def is_registered(self, platform: Platform) -> bool:
        return any(self.has_capability(platform, c) for c in ("order", "shipment", "after_sale", "conversation"))

    def list_supported_platforms(self) -> list[str]:
        return self.list_platforms()


class _LegacyAdapter:
    """Thin shim that wraps the four protocol adapters so old code
    (which expects one adapter instance per platform) can still call
    ``to_unified_order``, ``to_unified_shipment``, ``to_unified_refund``,
    and ``to_unified_conversation`` on a single object.
    """

    def __init__(
        self,
        platform: Platform,
        order: OrderAdapter | None,
        shipment: ShipmentAdapter | None,
        after_sale: AfterSaleAdapter | None,
        conversation: ConversationAdapter | None,
    ) -> None:
        self._platform = platform
        self._order = order
        self._shipment = shipment
        self._after_sale = after_sale
        self._conversation = conversation

    @property
    def platform(self) -> Platform:
        return self._platform

    def to_unified_order(self, platform_data: dict) -> dict:
        if self._order is None:
            raise NotImplementedError("Order adapter not registered")
        result = self._order.to_unified_order(platform_data)
        return result.model_dump() if hasattr(result, "model_dump") else result

    def to_unified_shipment(self, platform_data: dict) -> dict:
        if self._shipment is None:
            raise NotImplementedError("Shipment adapter not registered")
        result = self._shipment.to_unified_shipment(platform_data)
        return result.model_dump() if hasattr(result, "model_dump") else result

    def to_unified_refund(self, platform_data: dict) -> dict:
        if self._after_sale is None:
            raise NotImplementedError("After-sale adapter not registered")
        result = self._after_sale.to_unified_after_sale(platform_data)
        return result.model_dump() if hasattr(result, "model_dump") else result

    def to_unified_conversation(self, platform_data: dict) -> dict:
        if self._conversation is None:
            raise NotImplementedError("Conversation adapter not registered")
        result = self._conversation.to_unified_conversation(platform_data)
        return result.model_dump() if hasattr(result, "model_dump") else result

    def get_contract(self) -> "_LegacyContract":
        return _LegacyContract()


class _LegacyContract:
    def __init__(self) -> None:
        pass


class _LegacyCapabilities:
    def __init__(self, platform: Platform, registry: AdapterRegistry) -> None:
        self._platform = platform
        self._registry = registry

    def supports_order(self) -> bool:
        return self._registry.has_capability(self._platform, "order")

    def supports_shipment(self) -> bool:
        return self._registry.has_capability(self._platform, "shipment")

    def supports_after_sale(self) -> bool:
        return self._registry.has_capability(self._platform, "after_sale")

    def supports_conversation(self) -> bool:
        return self._registry.has_capability(self._platform, "conversation")


# ---------------------------------------------------------------------------
# Bootstrap helpers
# ---------------------------------------------------------------------------

def bootstrap_default_registry() -> AdapterRegistry:
    registry = AdapterRegistry()

    from .douyin import DouyinAfterSaleAdapter, DouyinOrderAdapter, DouyinShipmentAdapter
    from .jd import JDAfterSaleAdapter, JDOrderAdapter, JDShipmentAdapter
    from .kuaishou import KuaishouAfterSaleAdapter, KuaishouOrderAdapter, KuaishouShipmentAdapter
    from .taobao import TaobaoOrderAdapter
    from .wecom_kf import WeComKfConversationAdapter
    from .xhs import XHSAfterSaleAdapter, XHSOrderAdapter, XHSShipmentAdapter

    registry.register(Platform.TAOBAO, order_adapter=TaobaoOrderAdapter())
    registry.register(
        Platform.DOUYIN_SHOP,
        order_adapter=DouyinOrderAdapter(),
        shipment_adapter=DouyinShipmentAdapter(),
        after_sale_adapter=DouyinAfterSaleAdapter(),
    )
    registry.register(
        Platform.JD,
        order_adapter=JDOrderAdapter(),
        shipment_adapter=JDShipmentAdapter(),
        after_sale_adapter=JDAfterSaleAdapter(),
    )
    registry.register(
        Platform.XHS,
        order_adapter=XHSOrderAdapter(),
        shipment_adapter=XHSShipmentAdapter(),
        after_sale_adapter=XHSAfterSaleAdapter(),
    )
    registry.register(
        Platform.KUAISHOU,
        order_adapter=KuaishouOrderAdapter(),
        shipment_adapter=KuaishouShipmentAdapter(),
        after_sale_adapter=KuaishouAfterSaleAdapter(),
    )
    registry.register(
        Platform.WECOM_KF,
        conversation_adapter=WeComKfConversationAdapter(),
    )

    return registry


# ---------------------------------------------------------------------------
# Aliases for backwards-compatibility with code that imports
# `PlatformRegistry` and `bootstrap_default_registry` from this module.
# ---------------------------------------------------------------------------

PlatformRegistry = AdapterRegistry

# Re-export the bootstrap function so existing imports still work.
__all__ = [
    "AdapterRegistry",
    "PlatformRegistry",
    "bootstrap_default_registry",
]
