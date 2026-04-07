from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from app.api.router import api_router
from app.api.errors import (
    DomainServiceError,
    NotFoundError,
    BadRequestError,
    domain_service_error_handler,
    not_found_error_handler,
    bad_request_error_handler,
    general_exception_handler,
)
from app.core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

app = FastAPI(
    title="Domain Service",
    description="Unified business layer for multi-platform customer service middleware.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

# Register exception handlers
app.add_exception_handler(NotFoundError, not_found_error_handler)
app.add_exception_handler(BadRequestError, bad_request_error_handler)
app.add_exception_handler(DomainServiceError, domain_service_error_handler)
app.add_exception_handler(Exception, general_exception_handler)


@app.get("/")
async def root():
    return {"message": "Domain Service", "version": "0.1.0"}
