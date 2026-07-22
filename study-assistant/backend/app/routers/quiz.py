from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services import vector_store, claude_service

router = APIRouter(prefix="/api", tags=["quiz"])

MAX_CHUNKS_FOR_GENERATION = 45


class QuizRequest(BaseModel):
    doc_ids: List[str]
    num_questions: int = 5
    question_type: str = "mixed"  # mcq | short_answer | mixed


@router.post("/quiz")
def generate_quiz(req: QuizRequest):
    if not req.doc_ids:
        raise HTTPException(400, "Select at least one document.")
    chunks = vector_store.get_all_chunks_for_docs(req.doc_ids)
    if not chunks:
        raise HTTPException(404, "No content found for the selected document(s).")
    chunks = chunks[:MAX_CHUNKS_FOR_GENERATION]

    questions = claude_service.generate_quiz(
        chunks, num_questions=req.num_questions, question_type=req.question_type
    )
    return {"questions": questions}
