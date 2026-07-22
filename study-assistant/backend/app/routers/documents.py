from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException

from app.config import UPLOAD_DIR, ALLOWED_EXTENSIONS
from app.services import document_parser, vector_store
from app import store

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Unsupported file type '{ext}'. Allowed: {sorted(ALLOWED_EXTENSIONS)}")

    doc_id = vector_store.new_doc_id()
    dest_path = UPLOAD_DIR / f"{doc_id}{ext}"
    content = await file.read()
    dest_path.write_bytes(content)

    try:
        location_texts = document_parser.extract_text(dest_path)
        chunks = document_parser.chunk_text(location_texts)
        if not chunks:
            raise HTTPException(422, "No extractable text found in this file.")
        count = vector_store.add_document_chunks(doc_id, file.filename, chunks)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to process file: {e}")

    entry = store.add_document(doc_id, file.filename, count)
    return entry


@router.get("")
def list_documents():
    return store.list_documents()


@router.delete("/{doc_id}")
def delete_document(doc_id: str):
    entry = store.get_document(doc_id)
    if not entry:
        raise HTTPException(404, "Document not found")
    vector_store.delete_document(doc_id)
    store.remove_document(doc_id)

    for f in UPLOAD_DIR.glob(f"{doc_id}.*"):
        f.unlink(missing_ok=True)

    return {"deleted": doc_id}
