"""All calls to the LLM (Gemini or Anthropic) live here. Every prompt is built
so the model answers strictly from the supplied document excerpts, never from
outside knowledge.

Supports Google Gemini with automatic key rotation across multiple API keys
(useful since Gemini's free-tier quota is enforced per Google Cloud project,
not per key — rotating keys from separate projects gives more effective
daily headroom), and falls back to Anthropic if configured instead.
"""
import json
import re
from typing import List, Dict

import httpx

from app.config import (
    GEMINI_API_KEYS,
    GEMINI_MODEL,
    ANTHROPIC_API_KEY,
    CLAUDE_MODEL,
    LLM_PROVIDER,
)

_GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

_anthropic_client = None
if LLM_PROVIDER == "anthropic":
    import anthropic
    _anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def _format_context(chunks: List[Dict]) -> str:
    parts = []
    for i, c in enumerate(chunks, start=1):
        parts.append(f"[Excerpt {i} | {c['filename']} - {c['location']}]\n{c['text']}")
    return "\n\n".join(parts)


def _call_gemini(system: str, user_content: str, max_tokens: int) -> str:
    """Calls Gemini's generateContent endpoint, trying each configured API key
    in order. If a key is rate-limited (HTTP 429) or otherwise rejected, moves
    on to the next key. Raises the last error if every key fails."""
    if not GEMINI_API_KEYS:
        raise RuntimeError(
            "No Gemini API keys configured. Set GEMINI_API_KEYS (comma-separated) "
            "in your environment."
        )

    url = _GEMINI_URL.format(model=GEMINI_MODEL)
    payload = {
        "system_instruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": user_content}]}],
        "generationConfig": {"maxOutputTokens": max_tokens},
    }

    last_error = None
    for key in GEMINI_API_KEYS:
        try:
            resp = httpx.post(
                url,
                params={"key": key},
                json=payload,
                timeout=60,
            )
            if resp.status_code == 429:
                # This key/project's quota is exhausted — try the next one.
                last_error = RuntimeError(f"Gemini key ending in ...{key[-4:]} rate-limited (429)")
                continue
            resp.raise_for_status()
            data = resp.json()
            candidates = data.get("candidates", [])
            if not candidates:
                last_error = RuntimeError("Gemini returned no candidates")
                continue
            parts = candidates[0].get("content", {}).get("parts", [])
            text = "".join(p.get("text", "") for p in parts)
            return text
        except httpx.HTTPStatusError as e:
            last_error = e
            continue

    raise RuntimeError(f"All Gemini API keys failed. Last error: {last_error}")


def _call_anthropic(system: str, user_content: str, max_tokens: int) -> str:
    message = _anthropic_client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user_content}],
    )
    return "".join(b.text for b in message.content if b.type == "text")


def _generate(system: str, user_content: str, max_tokens: int) -> str:
    if LLM_PROVIDER == "gemini":
        return _call_gemini(system, user_content, max_tokens)
    return _call_anthropic(system, user_content, max_tokens)


def answer_question(question: str, chunks: List[Dict]) -> Dict:
    if not chunks:
        return {
            "answer": "I couldn't find anything relevant to that question in your uploaded documents.",
            "sources": [],
        }

    context = _format_context(chunks)
    system = (
        "You are a study assistant. Answer the student's question using ONLY the "
        "information in the provided document excerpts. Do not use outside knowledge. "
        "If the excerpts don't contain the answer, say plainly that the documents don't "
        "cover it — do not guess. When you use a fact, mention which excerpt number it "
        "came from, like (Excerpt 2). Keep answers clear and study-friendly."
    )
    answer_text = _generate(
        system,
        f"Document excerpts:\n\n{context}\n\nQuestion: {question}",
        1000,
    )

    sources = [{"filename": c["filename"], "location": c["location"]} for c in chunks]
    return {"answer": answer_text, "sources": sources}


def generate_summary(chunks: List[Dict], style: str = "concise") -> str:
    context = _format_context(chunks)
    length_hint = {
        "concise": "Keep it to 150-250 words, in a short paragraph plus 3-5 key bullet points.",
        "detailed": "Write a thorough summary (400-600 words) organized under clear subheadings.",
    }.get(style, "Keep it to 150-250 words, in a short paragraph plus 3-5 key bullet points.")

    system = (
        "You are a study assistant. Summarize the following document excerpts using ONLY "
        "the information they contain. Do not add outside facts. " + length_hint
    )
    return _generate(system, context, 1200)


def generate_quiz(chunks: List[Dict], num_questions: int = 5, question_type: str = "mixed") -> List[Dict]:
    context = _format_context(chunks)
    type_hint = {
        "mcq": "multiple-choice questions only, each with 4 options",
        "short_answer": "short-answer questions only",
        "mixed": "a mix of multiple-choice (4 options) and short-answer questions",
    }.get(question_type, "a mix of multiple-choice (4 options) and short-answer questions")

    system = (
        "You are a study assistant generating a quiz strictly from the provided document "
        "excerpts. Do not use outside knowledge. Respond with ONLY valid JSON (no markdown "
        "fences, no preamble) matching this schema:\n"
        '{"questions": [{"type": "mcq" | "short_answer", "question": str, '
        '"options": [str, str, str, str] (omit for short_answer), '
        '"answer": str, "explanation": str}]}'
    )
    user_msg = (
        f"Document excerpts:\n\n{context}\n\n"
        f"Create {num_questions} quiz questions ({type_hint}) based only on these excerpts."
    )
    raw = _generate(system, user_msg, 2000)
    raw = re.sub(r"^```(json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()

    try:
        data = json.loads(raw)
        return data.get("questions", [])
    except json.JSONDecodeError:
        return [{"type": "error", "question": "Could not parse quiz output.", "answer": raw, "explanation": ""}]