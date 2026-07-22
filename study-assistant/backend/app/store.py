import json
import threading
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

from app.config import DATA_DIR

_REGISTRY_FILE = DATA_DIR / "documents.json"
_lock = threading.Lock()


def _load() -> Dict:
    if _REGISTRY_FILE.exists():
        return json.loads(_REGISTRY_FILE.read_text())
    return {}


def _save(data: Dict) -> None:
    _REGISTRY_FILE.write_text(json.dumps(data, indent=2))


def add_document(doc_id: str, filename: str, chunk_count: int) -> Dict:
    with _lock:
        data = _load()
        entry = {
            "doc_id": doc_id,
            "filename": filename,
            "chunk_count": chunk_count,
            "uploaded_at": datetime.utcnow().isoformat() + "Z",
        }
        data[doc_id] = entry
        _save(data)
        return entry


def list_documents() -> List[Dict]:
    data = _load()
    return sorted(data.values(), key=lambda d: d["uploaded_at"], reverse=True)


def get_document(doc_id: str) -> Optional[Dict]:
    return _load().get(doc_id)


def remove_document(doc_id: str) -> None:
    with _lock:
        data = _load()
        data.pop(doc_id, None)
        _save(data)
