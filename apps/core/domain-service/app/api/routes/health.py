from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("/healthz")
async def healthz():
    return JSONResponse(
        status_code=200,
        content={"status": "ok", "service": "domain-service"}
    )
