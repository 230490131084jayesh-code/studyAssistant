from typing import List, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from app.services import vector_store, claude_service

router = APIRouter(prefix="/api", tags=["qa"])


class AskRequest(BaseModel):
    question: str
    doc_ids: Optional[List[str]] = None


@router.post("/ask")
def ask(req: AskRequest):
    chunks = vector_store.query(req.question, doc_ids=req.doc_ids)
    result = claude_service.answer_question(req.question, chunks)
    return result
