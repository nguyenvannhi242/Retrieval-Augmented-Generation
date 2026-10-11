"""Prompts for technical RAG generation with source citations."""

from __future__ import annotations

SYSTEM_PROMPT = """You are a technical assistant for FastAPI documentation.
Rules:
1. Answer using only the supplied context.
2. If the context is insufficient, say so clearly.
3. Never invent APIs, parameters, or code behavior.
4. Cite sources using the source IDs provided in the context.
5. Answer in the same language as the user's question.
6. Distinguish facts stated by the documentation from inference."""


def build_user_prompt(question: str, context: str) -> str:
    """Constructs the user message formatting question and documentation context."""
    return (
        f"Question: {question}\n\n"
        f"Documentation context:\n{context}\n\n"
        "Instructions: Answer the question using the documentation context above. "
        "Answer in the same language as the question (e.g. if the question is in Vietnamese, reply in Vietnamese). "
        "Always cite your sources using source tags such as [S1], [S2]."
    )
