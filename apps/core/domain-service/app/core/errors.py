from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel


class ErrorCode(str, Enum):
    PLATFORM_NOT_SUPPORTED = "platform_not_supported"
    ORDER_NOT_FOUND = "order_not_found"
    SHIPMENT_NOT_FOUND = "shipment_not_found"
    AFTER_SALE_NOT_FOUND = "after_sale_not_found"
    CONVERSATION_NOT_FOUND = "conversation_not_found"
    CONTEXT_NOT_FOUND = "context_not_found"
    PROVIDER_ERROR = "provider_error"
    VALIDATION_ERROR = "validation_error"
    INTERNAL_ERROR = "internal_error"


class ErrorResponse(BaseModel):
    code: str
    message: str
    request_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


ERROR_RESPONSES: Dict[ErrorCode, Dict[str, Any]] = {
    ErrorCode.PLATFORM_NOT_SUPPORTED: {
        "http_status": 400,
        "message": "Platform not supported",
        "retryable": False,
    },
    ErrorCode.ORDER_NOT_FOUND: {
        "http_status": 404,
        "message": "Order not found",
        "retryable": False,
    },
    ErrorCode.SHIPMENT_NOT_FOUND: {
        "http_status": 404,
        "message": "Shipment not found",
        "retryable": False,
    },
    ErrorCode.AFTER_SALE_NOT_FOUND: {
        "http_status": 404,
        "message": "After-sale not found",
        "retryable": False,
    },
    ErrorCode.CONVERSATION_NOT_FOUND: {
        "http_status": 404,
        "message": "Conversation not found",
        "retryable": False,
    },
    ErrorCode.CONTEXT_NOT_FOUND: {
        "http_status": 404,
        "message": "Business context not found",
        "retryable": False,
    },
    ErrorCode.PROVIDER_ERROR: {
        "http_status": 502,
        "message": "Provider error",
        "retryable": True,
    },
    ErrorCode.VALIDATION_ERROR: {
        "http_status": 400,
        "message": "Validation error",
        "retryable": False,
    },
    ErrorCode.INTERNAL_ERROR: {
        "http_status": 500,
        "message": "Internal server error",
        "retryable": False,
    },
}


def get_error_response(error_code: ErrorCode) -> Dict[str, Any]:
    base = ERROR_RESPONSES.get(error_code, ERROR_RESPONSES[ErrorCode.INTERNAL_ERROR])
    return {
        "error": error_code.value,
        "message": base["message"],
        "http_status": base["http_status"],
        "retryable": base.get("retryable", False),
    }
