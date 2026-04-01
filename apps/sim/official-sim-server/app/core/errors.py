from typing import Dict, Any, Optional
from enum import Enum


class ErrorCode(str, Enum):
    TOKEN_EXPIRED = "token_expired"
    INVALID_SIGNATURE = "invalid_signature"
    TIMESTAMP_OUT_OF_WINDOW = "timestamp_out_of_window"
    PERMISSION_DENIED = "permission_denied"
    RESOURCE_NOT_FOUND = "resource_not_found"
    RATE_LIMITED = "rate_limited"
    DUPLICATE_PUSH = "duplicate_push"
    OUT_OF_ORDER_PUSH = "out_of_order_push"
    CALLBACK_ACK_INVALID = "callback_ack_invalid"
    CONVERSATION_CLOSED = "conversation_closed"
    MSG_CODE_EXPIRED = "msg_code_expired"
    INTERNAL_ERROR = "internal_error"


ERROR_RESPONSES: Dict[ErrorCode, Dict[str, Any]] = {
    ErrorCode.TOKEN_EXPIRED: {
        "error": "token_expired",
        "message": "Access token has expired, please re-authenticate",
        "http_status": 401,
        "retryable": True,
    },
    ErrorCode.INVALID_SIGNATURE: {
        "error": "invalid_signature",
        "message": "Request signature verification failed",
        "http_status": 403,
        "retryable": False,
    },
    ErrorCode.TIMESTAMP_OUT_OF_WINDOW: {
        "error": "timestamp_out_of_window",
        "message": "Request timestamp is outside acceptable window",
        "http_status": 400,
        "retryable": True,
    },
    ErrorCode.PERMISSION_DENIED: {
        "error": "permission_denied",
        "message": "Insufficient permissions for this operation",
        "http_status": 403,
        "retryable": False,
    },
    ErrorCode.RESOURCE_NOT_FOUND: {
        "error": "resource_not_found",
        "message": "The requested resource does not exist",
        "http_status": 404,
        "retryable": False,
    },
    ErrorCode.RATE_LIMITED: {
        "error": "rate_limited",
        "message": "API rate limit exceeded, please slow down",
        "http_status": 429,
        "retryable": True,
    },
    ErrorCode.DUPLICATE_PUSH: {
        "error": "duplicate_push",
        "message": "This push event has already been processed",
        "http_status": 409,
        "retryable": False,
    },
    ErrorCode.OUT_OF_ORDER_PUSH: {
        "error": "out_of_order_push",
        "message": "Push event received out of expected order",
        "http_status": 400,
        "retryable": True,
    },
    ErrorCode.CALLBACK_ACK_INVALID: {
        "error": "callback_ack_invalid",
        "message": "Callback acknowledgment is invalid or expired",
        "http_status": 400,
        "retryable": False,
    },
    ErrorCode.CONVERSATION_CLOSED: {
        "error": "conversation_closed",
        "message": "The conversation has been closed",
        "http_status": 410,
        "retryable": False,
    },
    ErrorCode.MSG_CODE_EXPIRED: {
        "error": "msg_code_expired",
        "message": "Verification code has expired",
        "http_status": 400,
        "retryable": True,
    },
    ErrorCode.INTERNAL_ERROR: {
        "error": "internal_error",
        "message": "Internal server error, please try again later",
        "http_status": 500,
        "retryable": True,
    },
}


def get_error_response(error_code: ErrorCode) -> Dict[str, Any]:
    return ERROR_RESPONSES.get(error_code, ERROR_RESPONSES[ErrorCode.INTERNAL_ERROR])


def is_retryable(error_code: ErrorCode) -> bool:
    return ERROR_RESPONSES[error_code].get("retryable", False)
