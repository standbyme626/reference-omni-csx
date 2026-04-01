from fastapi import APIRouter

from app.api.routes import runs
from app.api.routes import raw_query
from app.api.routes import mock_compat

api_router = APIRouter()

api_router.include_router(runs.router, prefix="/official-sim/runs", tags=["runs"])
api_router.include_router(raw_query.router, prefix="/official-sim/raw", tags=["raw-query"])
api_router.include_router(raw_query.router, prefix="/official-sim/query", tags=["query-compat"])
api_router.include_router(mock_compat.jd_router)
api_router.include_router(mock_compat.douyin_router)
api_router.include_router(mock_compat.wecom_router)
api_router.include_router(mock_compat.taobao_router)
api_router.include_router(mock_compat.xhs_router)
api_router.include_router(mock_compat.kuaishou_router)
