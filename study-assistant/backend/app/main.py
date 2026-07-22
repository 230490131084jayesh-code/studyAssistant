from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import ALLOWED_ORIGINS
from app.routers import documents, qa, quiz, summary

app = FastAPI(title="AI Smart Study Assistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router)
app.include_router(qa.router)
app.include_router(quiz.router)
app.include_router(summary.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
