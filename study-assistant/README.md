# AI Smart Study Assistant

Upload PDFs, PPTX, and DOCX notes. Ask questions that are answered **only** from
what you've uploaded, plus generate quizzes and summaries — all running locally.

- **Backend:** Python/FastAPI. Parses documents, chunks them, and stores them in a
  local ChromaDB vector store using a local `sentence-transformers` embedding model
  (`all-MiniLM-L6-v2`) — no API key or network call needed for search itself.
- **Frontend:** React (Vite).
- **LLM:** Anthropic Claude API — used only for the final answer/quiz/summary
  generation, and every prompt instructs Claude to use *only* the retrieved
  document excerpts, never outside knowledge.

## 1. Backend setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# then edit .env and paste your Anthropic API key:
#   ANTHROPIC_API_KEY=sk-ant-...
```

Get an API key at https://console.anthropic.com/settings/keys

Run the server:

```bash
uvicorn app.main:app --reload --port 8000
```

The first run downloads the small embedding model (~90MB) — after that it works
fully offline for retrieval. API docs: http://localhost:8000/docs

## 2. Frontend setup

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

## How it works

1. **Upload** — a file is parsed (PDF via `pypdf`, PPTX via `python-pptx`, DOCX via
   `python-docx`), split into overlapping ~900-character chunks tagged with their
   page/slide/section, and embedded into the local Chroma vector store.
2. **Ask** — your question is embedded, the most relevant chunks are retrieved,
   and Claude is prompted to answer *strictly* from those excerpts, citing which
   excerpt each fact came from. If nothing relevant is found, it says so instead
   of guessing.
3. **Quiz / Summary** — pulls all chunks for the documents you've selected in the
   sidebar (capped to keep prompts reasonable) and asks Claude to generate
   questions or a summary from that material only.

## Project structure

```
study-assistant/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI app + CORS
│   │   ├── config.py          # settings, chunk size, model name
│   │   ├── store.py           # JSON-backed document registry
│   │   ├── services/
│   │   │   ├── document_parser.py   # PDF/PPTX/DOCX text extraction + chunking
│   │   │   ├── vector_store.py      # Chroma + local embeddings
│   │   │   └── claude_service.py    # all Anthropic API calls
│   │   └── routers/
│   │       ├── documents.py   # upload / list / delete
│   │       ├── qa.py          # POST /api/ask
│   │       ├── quiz.py        # POST /api/quiz
│   │       └── summary.py     # POST /api/summary
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── src/
    │   ├── App.jsx
    │   ├── api.js
    │   └── components/ (Sidebar, AskPanel, QuizPanel, SummaryPanel)
    └── package.json
```

## Notes

- Uploaded files, vector data, and document metadata all live under `backend/data/`
  locally (`data/uploads/`, `data/chroma_db/`, `data/documents.json`) — delete that
  folder to fully reset.
- Swap models by editing `CLAUDE_MODEL` in `.env` (defaults to `claude-sonnet-5`;
  try `claude-haiku-4-5-20251001` for cheaper/faster quiz and summary generation).
- CORS origins are controlled by `ALLOWED_ORIGINS` in `.env` (comma-separated).
  Defaults to `localhost:5173` for local dev.

## Deploying to GitHub + Render

### 1. Push to GitHub

```bash
cd study-assistant
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```

`.env` files are gitignored — never commit your Anthropic API key.

### 2. Deploy on Render

The included `render.yaml` defines both services as a Render **Blueprint**, so you
can deploy everything in one go:

1. Go to https://dashboard.render.com → **New** → **Blueprint**.
2. Connect your GitHub repo. Render detects `render.yaml` automatically and shows
   two services: `study-assistant-backend` (FastAPI) and `study-assistant-frontend`
   (static site).
3. Before applying, set the one required secret: on the backend service, add
   `ANTHROPIC_API_KEY` with your key (this is marked `sync: false` in the blueprint
   so it's never committed to the repo).
4. Click **Apply**. Render builds both services. First backend build takes a few
   minutes (installs torch/chromadb and downloads the embedding model).
5. Once live, confirm the URLs match what's in `render.yaml`:
   - Backend: `https://study-assistant-backend.onrender.com`
   - Frontend: `https://study-assistant-frontend.onrender.com`
   If Render assigns different subdomains (e.g. the name was taken), update
   `ALLOWED_ORIGINS` on the backend and `VITE_API_URL` on the frontend in the
   Render dashboard to match the real URLs, then redeploy both.

**No `render.yaml`? Manual setup works too:**
- **Backend** — New → Web Service → root dir `backend`, build command
  `pip install -r requirements.txt`, start command `bash start.sh`, add env vars
  `ANTHROPIC_API_KEY`, `PYTHON_VERSION=3.12.7`, `ALLOWED_ORIGINS=<frontend URL>`,
  `DATA_DIR=/var/data`, and attach a small persistent disk mounted at `/var/data`
  (Render dashboard → service → Disks) so uploads survive restarts.
- **Frontend** — New → Static Site → root dir `frontend`, build command
  `npm install && npm run build`, publish directory `dist`, add env var
  `VITE_API_URL=<backend URL>`.

### Storage note

Render's free plan disk is small and the free web service spins down after
inactivity, so on the free tier expect: a ~30-60s cold-start delay after idling,
and treat it as fine for a demo/portfolio project rather than production scale.
For heavier use, upgrade the plan and disk size.
