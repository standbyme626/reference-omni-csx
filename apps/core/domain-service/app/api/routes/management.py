from fastapi import APIRouter

from app.core.response import success_response
from app.services.compat_data import (
    list_dashboard_snapshots,
    list_training_cases,
    list_training_tasks,
    list_voc_topics,
)


router = APIRouter()


@router.get("/voc-topics")
async def get_voc_topics():
    items = list_voc_topics()
    return success_response({"items": items, "total": len(items)})


@router.get("/training-cases")
async def get_training_cases():
    items = list_training_cases()
    return success_response({"items": items, "total": len(items)})


@router.get("/training-tasks")
async def get_training_tasks():
    items = list_training_tasks()
    return success_response({"items": items, "total": len(items)})


@router.get("/dashboard-snapshots")
async def get_dashboard_snapshots():
    items = list_dashboard_snapshots()
    return success_response({"items": items, "total": len(items)})
