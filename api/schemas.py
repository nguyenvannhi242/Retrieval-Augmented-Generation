"""Pydantic schemas for the FastAPI RAG backend."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Chat question request schema."""

    question: str = Field(
        ...,
        min_length=2,
        description="The technical query in English or Vietnamese",
        examples=["How do I configure Docker for FastAPI?"],
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of relevant document chunks to retrieve",
    )
    model: Optional[str] = Field(
        default=None,
        description="Optional Ollama model override (default: gemma2:2b)",
    )


class SourceItem(BaseModel):
    """Source reference citation used in the answer."""

    source_id: str = Field(..., description="Citation identifier, e.g., 'S1'")
    title: str = Field(..., description="Document page or section title")
    url: str = Field(..., description="Official canonical URL of the documentation")
    source_file: Optional[str] = Field(default=None, description="Relative markdown file path")
    score: Optional[float] = Field(default=None, description="Similarity score (cosine)")


class RetrievedChunkItem(BaseModel):
    """Individual chunk retrieved from vector database."""

    chunk_id: str
    title: str
    url: str
    source: str
    score: float
    text: str


class ChatResponse(BaseModel):
    """Structured response containing answer, sources, and latency measurements."""

    answer: str = Field(..., description="Generated answer with source citations")
    sources: List[SourceItem] = Field(
        default_factory=list,
        description="List of documentation sources cited in the answer",
    )
    retrieved_chunks: List[RetrievedChunkItem] = Field(
        default_factory=list,
        description="Full retrieved chunks for inspection",
    )
    retrieval_latency_ms: float = Field(
        ...,
        description="Time taken to embed and search ChromaDB in milliseconds",
    )
    generation_latency_ms: float = Field(
        ...,
        description="Time taken by LLM to generate the answer in milliseconds",
    )
    total_latency_ms: float = Field(
        ...,
        description="Total roundtrip pipeline latency in milliseconds",
    )


class ServiceHealth(BaseModel):
    """Health check status of a downstream component."""

    status: str
    details: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    """Health response indicating overall service and dependencies status."""

    status: str
    chroma_db: ServiceHealth
    ollama: ServiceHealth
    version: str = "1.0.0"
