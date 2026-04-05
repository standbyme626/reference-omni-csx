from __future__ import annotations

from typing import Protocol

from app.models import Order, Shipment, AfterSale, Conversation, Message


class OrderAdapter(Protocol):
    """Converts platform-specific raw order data to unified Order model."""

    def to_unified_order(self, platform_data: dict) -> Order: ...


class ShipmentAdapter(Protocol):
    """Converts platform-specific raw shipment data to unified Shipment model."""

    def to_unified_shipment(self, platform_data: dict) -> Shipment: ...


class AfterSaleAdapter(Protocol):
    """Converts platform-specific raw after-sale data to unified AfterSale model."""

    def to_unified_after_sale(self, platform_data: dict) -> AfterSale: ...


class ConversationAdapter(Protocol):
    """Converts platform-specific raw conversation data to unified Conversation/Message models."""

    def to_unified_conversation(self, platform_data: dict) -> Conversation: ...

    def to_unified_messages(self, platform_data: dict, limit: int = 100) -> list[Message]: ...
