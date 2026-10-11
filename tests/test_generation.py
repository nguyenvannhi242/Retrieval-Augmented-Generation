"""Unit tests for generation prompts, context formatting, and citation validation."""

from generation.generator import (
    format_context_from_chunks,
    generate_answer,
    validate_citations,
)
from generation.prompts import SYSTEM_PROMPT, build_user_prompt


def test_system_prompt_rules():
    assert "You are a technical assistant for FastAPI documentation" in SYSTEM_PROMPT
    assert "Answer using only the supplied context" in SYSTEM_PROMPT
    assert "Cite sources using the source IDs provided in the context" in SYSTEM_PROMPT
    assert "Answer in the same language as the user's question" in SYSTEM_PROMPT


def test_build_user_prompt():
    prompt = build_user_prompt("What is FastAPI?", "[S1] FastAPI is fast.")
    assert "Question: What is FastAPI?" in prompt
    assert "Documentation context:\n[S1] FastAPI is fast." in prompt
    assert "[S1]" in prompt


def test_format_context_from_chunks():
    chunks = [
        {
            "title": "Query Params",
            "url": "https://fastapi.tiangolo.com/tutorial/query-params/",
            "text": "Declare query params as function args.",
        },
        {
            "title": "Path Params",
            "url": "https://fastapi.tiangolo.com/tutorial/path-params/",
            "text": "Declare path params with curly braces.",
        },
    ]
    ctx = format_context_from_chunks(chunks)
    assert "[S1]" in ctx
    assert "Title: Query Params" in ctx
    assert "Source: https://fastapi.tiangolo.com/tutorial/query-params/" in ctx
    assert "[S2]" in ctx
    assert "Title: Path Params" in ctx


def test_validate_citations():
    chunks = [
        {"title": "Doc 1", "url": "https://url1", "source": "src1.md", "chunk_id": "c1", "score": 0.85, "text": "Content 1"},
        {"title": "Doc 2", "url": "https://url2", "source": "src2.md", "chunk_id": "c2", "score": 0.80, "text": "Content 2"},
    ]
    answer = "Based on [S1], you can declare params. Additionally, as shown in [S2] and [S9], more details exist."
    cited, hallucinated = validate_citations(answer, chunks)

    assert len(cited) == 2
    assert cited[0].source_id == "S1"
    assert cited[0].title == "Doc 1"
    assert cited[1].source_id == "S2"
    assert cited[1].title == "Doc 2"
    assert hallucinated == ["[S9]"]


def test_empty_retrieved_chunks():
    result = generate_answer("How to do X?", [])
    assert "could not find relevant documentation" in result.lower()
