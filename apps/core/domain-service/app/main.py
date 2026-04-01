from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.api.router import api_router

app = FastAPI(
    title="Domain Service",
    description="Unified business layer for multi-platform customer service middleware.",
    version="0.1.0",
)

app.include_router(api_router)


@app.get("/healthz")
async def healthz():
    return JSONResponse(
        status_code=200,
        content={"status": "ok", "service": "domain-service"}
    )


@app.get("/")
async def root():
    return {"message": "Domain Service", "version": "0.1.0"}
