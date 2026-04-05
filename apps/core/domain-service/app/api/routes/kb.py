from fastapi import APIRouter
from pydantic import BaseModel

from app.core.response import success_response
from app.services.compat_data import create_kb_document, list_kb_documents, reindex_knowledge_base


router = APIRouter()


class DocumentCreateRequest(BaseModel):
    title: str
    content: str
    doc_type: str = "faq"


@router.get("/documents")
async def get_documents():
    items = list_kb_documents()
    return success_response({"items": items, "total": len(items)})


@router.post("/documents")
async def create_document(request: DocumentCreateRequest):
    document = create_kb_document(request.title, request.content, request.doc_type)
    return success_response(document)


@router.post("/reindex")
async def reindex_documents():
    return success_response(reindex_knowledge_base())
