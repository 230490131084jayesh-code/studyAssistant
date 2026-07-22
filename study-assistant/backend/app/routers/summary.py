from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services import vector_store, claude_service
from app.routers.quiz import MAX_CHUNKS_FOR_GENERATION

router = APIRouter(prefix="/api", tags=["summary"])


class SummaryRequest(BaseModel):
    doc_ids: List[str]
    style: str = "concise"  # concise | detailed


@router.post("/summary")
def generate_summary(req: SummaryRequest):
    if not req.doc_ids:
        raise HTTPException(400, "Select at least one document.")
    chunks = vector_store.get_all_chunks_for_docs(req.doc_ids)
    if not chunks:
        raise HTTPException(404, "No content found for the selected document(s).")
    chunks = chunks[:MAX_CHUNKS_FOR_GENERATION]

    summary = claude_service.generate_summary(chunks, style=req.style)
    return {"summary": summary}
