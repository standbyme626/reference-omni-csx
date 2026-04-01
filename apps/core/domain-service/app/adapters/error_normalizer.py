from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass


class NormalizedErrorLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class NormalizedError:
    original_code: str
    original_message: str
    normalized_code: str
    normalized_message: str
    level: NormalizedErrorLevel
    retryable: bool
    http_status: int
    platform: str
    context: Dict[str, Any]


class PlatformErrorNormalizer:
    _mappings: Dict[str, Dict[str, NormalizedError]] = {}
    
    @classmethod
    def normalize(
        cls,
        platform: str,
        error_code: str,
        error_message: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> NormalizedError:
        platform_mappings = cls._mappings.get(platform, {})
        
        if error_code in platform_mappings:
            return platform_mappings[error_code]
        
        return NormalizedError(
            original_code=error_code,
            original_message=error_message,
            normalized_code="unknown_error",
            normalized_message=error_message,
            level=NormalizedErrorLevel.ERROR,
            retryable=False,
            http_status=500,
            platform=platform,
            context=context or {},
        )
    
    @classmethod
    def register(cls, platform: str, error_mapping: Dict[str, NormalizedError]):
        if platform not in cls._mappings:
            cls._mappings[platform] = {}
        cls._mappings[platform].update(error_mapping)


TAOBAO_ERROR_MAPPINGS = {
    "50": NormalizedError(
        original_code="50",
        original_message="App call limited",
        normalized_code="rate_limited",
        normalized_message="API rate limit exceeded",
        level=NormalizedErrorLevel.WARNING,
        retryable=True,
        http_status=429,
        platform="taobao",
        context={},
    ),
    "7": NormalizedError(
        original_code="7",
        original_message="Insufficient permissions",
        normalized_code="permission_denied",
        normalized_message="Insufficient API permissions",
        level=NormalizedErrorLevel.ERROR,
        retryable=False,
        http_status=403,
        platform="taobao",
        context={},
    ),
    "27": NormalizedError(
        original_code="27",
        original_message="Invalid session",
        normalized_code="token_expired",
        normalized_message="Access token expired or invalid",
        level=NormalizedErrorLevel.ERROR,
        retryable=True,
        http_status=401,
        platform="taobao",
        context={},
    ),
}

DOUYIN_ERROR_MAPPINGS = {
    "10001": NormalizedError(
        original_code="10001",
        original_message="系统错误",
        normalized_code="internal_error",
        normalized_message="Platform internal error",
        level=NormalizedErrorLevel.ERROR,
        retryable=True,
        http_status=500,
        platform="douyin_shop",
        context={},
    ),
    "10002": NormalizedError(
        original_code="10002",
        original_message="服务不可用",
        normalized_code="service_unavailable",
        normalized_message="Service temporarily unavailable",
        level=NormalizedErrorLevel.WARNING,
        retryable=True,
        http_status=503,
        platform="douyin_shop",
        context={},
    ),
}

PlatformErrorNormalizer.register("taobao", TAOBAO_ERROR_MAPPINGS)
PlatformErrorNormalizer.register("douyin_shop", DOUYIN_ERROR_MAPPINGS)
