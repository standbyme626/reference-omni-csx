from functools import lru_cache

from app.adapters.registry import PlatformRegistry, bootstrap_default_registry
from app.services.platform_gateway_service import PlatformGatewayService


@lru_cache()
def get_platform_registry() -> PlatformRegistry:
    return bootstrap_default_registry()


def get_platform_gateway_service() -> PlatformGatewayService:
    registry = get_platform_registry()
    return PlatformGatewayService(registry)
