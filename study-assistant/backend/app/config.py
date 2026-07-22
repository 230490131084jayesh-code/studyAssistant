import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# Where uploads / vector DB / document registry live. Defaults to a local
# "data" folder next to the app; on Render this is overridden via DATA_DIR
# to point at the mounted persistent disk, so files survive restarts/redeploys.
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5")

# Comma-separated list of allowed frontend origins, e.g.
# "http://localhost:5173,https://your-frontend.onrender.com"
_default_origins = "http://localhost:5173,http://127.0.0.1:5173"
ALLOWED_ORIGINS = [
    o.strip() for o in os.getenv("ALLOWED_ORIGINS", _default_origins).split(",") if o.strip()
]

UPLOAD_DIR = DATA_DIR / "uploads"
CHROMA_DIR = DATA_DIR / "chroma_db"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

# Chunking
CHUNK_SIZE = 900       # characters per chunk
CHUNK_OVERLAP = 150    # overlap between chunks
TOP_K_RESULTS = 6       # chunks retrieved per question

ALLOWED_EXTENSIONS = {".pdf", ".pptx", ".docx", ".txt", ".md"}
