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

# Gemini support: comma-separated list of API keys (from separate Google Cloud
# projects, since free-tier quota is enforced per-project, not per-key). The
# app tries each key in order and rotates to the next one if a key's quota is
# exhausted (HTTP 429), so a single project's daily limit doesn't stop the app.
GEMINI_API_KEYS = [
    k.strip() for k in os.getenv("GEMINI_API_KEYS", "").split(",") if k.strip()
]
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# Which provider to use for the final answer/quiz/summary generation step.
# "gemini" or "anthropic". Defaults to gemini if keys are present, else anthropic.
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini" if GEMINI_API_KEYS else "anthropic")

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