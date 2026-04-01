from typing import Generic, TypeVar, Optional, Dict, Any
from pydantic import BaseModel

T = TypeVar("T")


class EnvelopeResponse(BaseModel, Generic[T]):
    code: str = "0"
    message: str = "success"
    data: Optional[T] = None
    request_id: Optional[str] = None


class PaginatedResponse(BaseModel, Generic[T]):
    items: list
    total: int
    page: int
    page_size: int
    has_more: bool


def success_response(data: Any, request_id: Optional[str] = None) -> Dict[str, Any]:
    return {
        "code": "0",
        "message": "success",
        "data": data,
        "request_id": request_id,
    }


def error_response(
    code: str,
    message: str,
    request_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return {
        "code": code,
        "message": message,
        "request_id": request_id,
        "details": details,
    }
