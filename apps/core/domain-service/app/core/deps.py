from typing import Optional
from functools import lru_cache

from app.core.config import settings
from app.adapters.registry import PlatformRegistry
from app.services.platform_gateway_service import PlatformGatewayService


@lru_cache()
def get_platform_registry() -> PlatformRegistry:
    return PlatformRegistry()


def get_platform_gateway_service() -> PlatformGatewayService:
    registry = get_platform_registry()
    return PlatformGatewayService(registry)
