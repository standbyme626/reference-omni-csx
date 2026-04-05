from __future__ import annotations

from typing import Protocol


class OrderAdapter(Protocol):
    """Converts platform-specific raw order data to unified Order dict."""

    def to_unified_order(self, platform_data: dict) -> dict: ...


class ShipmentAdapter(Protocol):
    """Converts platform-specific raw shipment data to unified Shipment dict."""

    def to_unified_shipment(self, platform_data: dict) -> dict: ...


class AfterSaleAdapter(Protocol):
    """Converts platform-specific raw after-sale data to unified AfterSale dict."""

    def to_unified_after_sale(self, platform_data: dict) -> dict: ...


class ConversationAdapter(Protocol):
    """Converts platform-specific raw conversation data to unified Conversation dict."""

    def to_unified_conversation(self, platform_data: dict) -> dict: ...

    def to_unified_messages(self, platform_data: dict, limit: int = 100) -> list[dict]: ...
