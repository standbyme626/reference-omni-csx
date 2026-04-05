"""Unified error handling for domain-service API."""
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse


class DomainServiceError(Exception):
    """Base exception for domain service errors."""

    def __init__(self, detail: str = "", status_code: int = 500):
        self.detail = detail
        self.status_code = status_code
        super().__init__(self.detail)


class NotFoundError(DomainServiceError):
    """Resource not found."""

    def __init__(self, detail: str = ""):
        super().__init__(detail=detail, status_code=404)


class BadRequestError(DomainServiceError):
    """Bad request."""

    def __init__(self, detail: str = ""):
        super().__init__(detail=detail, status_code=400)


def domain_service_error_handler(request: Request, exc: DomainServiceError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail or "Internal server error"},
    )


def not_found_error_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={"detail": exc.detail or "Resource not found"},
    )


def bad_request_error_handler(request: Request, exc: BadRequestError) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={"detail": exc.detail or "Bad request"},
    )


def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Fallback handler for unhandled exceptions."""
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )
