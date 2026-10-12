"""Generation pipeline integrating ChromaDB retrieval with local LLM via Ollama."""

from __future__ import annotations

import argparse
import logging
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import ollama

from generation.prompts import SYSTEM_PROMPT, build_user_prompt
from retrieval.search import DocumentRetriever, SearchResult

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gemma2:2b"


@dataclass
class SourceCitation:
    """Represents a validated citation mapped from [S{i}] in the answer."""

    source_id: str  # e.g. "S1"
    index: int  # 1-indexed
    title: str
    url: str
    source_file: str
    chunk_id: str
    score: float
    excerpt: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "index": self.index,
            "title": self.title,
            "url": self.url,
            "source_file": self.source_file,
            "chunk_id": self.chunk_id,
            "score": round(self.score, 4),
            "excerpt": self.excerpt,
        }


@dataclass
class RAGAnswer:
    """Full structured answer containing LLM response, validated citations, and metadata."""

    question: str
    answer: str
    model: str
    all_retrieved_sources: List[Dict[str, Any]]
    cited_sources: List[SourceCitation]
    hallucinated_citations: List[str]
    retrieval_count: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question": self.question,
            "answer": self.answer,
            "model": self.model,
            "retrieval_count": self.retrieval_count,
            "cited_sources": [s.to_dict() for s in self.cited_sources],
            "all_retrieved_sources": self.all_retrieved_sources,
            "hallucinated_citations": self.hallucinated_citations,
        }


def format_context_from_chunks(retrieved_chunks: List[Dict[str, Any]]) -> str:
    """Formats retrieved chunks with numbered source markers [S1], [S2], ..."""
    context_parts: List[str] = []
    for i, chunk in enumerate(retrieved_chunks, start=1):
        context_parts.append(
            f"[S{i}]\n"
            f"Title: {chunk.get('title', '')}\n"
            f"Source: {chunk.get('url', '')}\n"
            f"Content:\n{chunk.get('text', '')}"
        )
    return "\n\n".join(context_parts)


def validate_citations(
    answer: str,
    retrieved_chunks: List[Dict[str, Any]],
) -> tuple[List[SourceCitation], List[str]]:
    """Extracts [S{i}] references from the answer and validates them against retrieved chunks."""
    found_tags: Set[str] = set(re.findall(r"\[S(\d+)\]", answer))
    cited_sources: List[SourceCitation] = []
    hallucinated: List[str] = []

    for tag in sorted(found_tags, key=int):
        idx = int(tag)
        if 1 <= idx <= len(retrieved_chunks):
            chunk = retrieved_chunks[idx - 1]
            cited_sources.append(
                SourceCitation(
                    source_id=f"S{idx}",
                    index=idx,
                    title=chunk.get("title", ""),
                    url=chunk.get("url", ""),
                    source_file=chunk.get("source", ""),
                    chunk_id=chunk.get("chunk_id", ""),
                    score=float(chunk.get("score", 0.0)),
                    excerpt=chunk.get("text", "")[:200] + "...",
                )
            )
        else:
            hallucinated.append(f"[S{idx}]")

    return cited_sources, hallucinated


def generate_answer(
    question: str,
    retrieved_chunks: List[Dict[str, Any]],
    model: str = DEFAULT_MODEL,
    system_prompt: str = SYSTEM_PROMPT,
) -> str:
    """Generates an answer using local LLM via Ollama based on documentation context."""
    if not retrieved_chunks:
        return "I could not find relevant documentation to answer this question."

    context = format_context_from_chunks(retrieved_chunks)
    user_content = build_user_prompt(question, context)

    response = ollama.chat(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        options={"temperature": 0.2, "num_predict": 384},
    )

    return response["message"]["content"].strip()


class RAGPipeline:
    """End-to-end RAG pipeline connecting ChromaDB retrieval and Ollama generation."""

    def __init__(
        self,
        retriever: Optional[DocumentRetriever] = None,
        model: str = DEFAULT_MODEL,
    ) -> None:
        self.retriever = retriever or DocumentRetriever()
        self.model = model

    def answer(
        self,
        question: str,
        top_k: int = 5,
        model: Optional[str] = None,
    ) -> RAGAnswer:
        """Executes full RAG flow: retrieval -> context building -> LLM generation -> citation validation."""
        active_model = model or self.model

        # 1. Retrieve top-k chunks
        search_hits: List[SearchResult] = self.retriever.search(question, top_k=top_k)
        chunks_data = [hit.to_dict() for hit in search_hits]

        # 2. Generate answer
        answer_text = generate_answer(
            question=question,
            retrieved_chunks=chunks_data,
            model=active_model,
        )

        # 3. Validate citations
        cited_sources, hallucinated = validate_citations(answer_text, chunks_data)

        return RAGAnswer(
            question=question,
            answer=answer_text,
            model=active_model,
            all_retrieved_sources=chunks_data,
            cited_sources=cited_sources,
            hallucinated_citations=hallucinated,
            retrieval_count=len(chunks_data),
        )


def print_rag_result(result: RAGAnswer) -> None:
    """Displays structured RAG answer and source citations."""
    print("\n" + "=" * 80)
    print(f" ❓ QUESTION: {result.question}")
    print(f" 🤖 MODEL:    {result.model}")
    print("=" * 80)
    print("\n💡 ANSWER:\n")
    print(result.answer)
    print("\n" + "─" * 80)

    if result.cited_sources:
        print(f" 📚 VALIDATED CITATIONS ({len(result.cited_sources)} cited):")
        for cit in result.cited_sources:
            print(f"   [{cit.source_id}] {cit.title}")
            print(f"        🔗 URL:    {cit.url}")
            print(f"        📄 Source: {cit.source_file}")
            print(f"        🎯 Score:  {cit.score:.4f}")
    else:
        print(" ℹ️ No specific [S{i}] source citations were detected in the response.")

    if result.hallucinated_citations:
        print(f"\n ⚠️ WARNING: Detected invalid citations: {result.hallucinated_citations}")

    print("=" * 80 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Query FastAPI RAG Chatbot using Ollama LLM")
    parser.add_argument(
        "--query",
        "-q",
        type=str,
        default="Làm thế nào để khai báo query parameters trong FastAPI?",
        help="Question in Vietnamese or English",
    )
    parser.add_argument(
        "--model",
        "-m",
        type=str,
        default=DEFAULT_MODEL,
        help="Ollama model name (default: gemma2:2b)",
    )
    parser.add_argument(
        "--top-k",
        "-k",
        type=int,
        default=5,
        help="Number of retrieved chunks (default: 5)",
    )
    args = parser.parse_args()

    pipeline = RAGPipeline(model=args.model)
    rag_result = pipeline.answer(args.query, top_k=args.top_k, model=args.model)
    print_rag_result(rag_result)
