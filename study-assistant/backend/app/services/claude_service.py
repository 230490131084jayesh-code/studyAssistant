"""All calls to the Anthropic API live here. Every prompt is built so Claude
answers strictly from the supplied document excerpts, never from outside knowledge."""
import json
import re
from typing import List, Dict

import anthropic

from app.config import ANTHROPIC_API_KEY, CLAUDE_MODEL

_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def _format_context(chunks: List[Dict]) -> str:
    parts = []
    for i, c in enumerate(chunks, start=1):
        parts.append(f"[Excerpt {i} | {c['filename']} - {c['location']}]\n{c['text']}")
    return "\n\n".join(parts)


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
    message = _client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1000,
        system=system,
        messages=[{
            "role": "user",
            "content": f"Document excerpts:\n\n{context}\n\nQuestion: {question}",
        }],
    )
    answer_text = "".join(b.text for b in message.content if b.type == "text")

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
    message = _client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1200,
        system=system,
        messages=[{"role": "user", "content": context}],
    )
    return "".join(b.text for b in message.content if b.type == "text")


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
    message = _client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=2000,
        system=system,
        messages=[{"role": "user", "content": user_msg}],
    )
    raw = "".join(b.text for b in message.content if b.type == "text")
    raw = re.sub(r"^```(json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()

    try:
        data = json.loads(raw)
        return data.get("questions", [])
    except json.JSONDecodeError:
        return [{"type": "error", "question": "Could not parse quiz output.", "answer": raw, "explanation": ""}]
