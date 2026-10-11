"""Data models for document chunks and normalized corpus."""

from __future__ import annotations

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class DocumentChunk(BaseModel):
    """Normalized schema for every text chunk in the corpus."""

    chunk_id: str = Field(description="Unique identifier for the chunk")
    text: str = Field(description="Extracted and normalized chunk content")
    source: str = Field(description="Relative path to original source file")
    title: str = Field(description="Document title")
    section: Optional[str] = Field(default="", description="Section header or sub-topic")
    url: str = Field(description="Canonical documentation URL")
    license: str = Field(
        default="MIT License (Sebastián Ramírez)",
        description="Source license information",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata (e.g. char_count, tags, source_type)",
    )

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()
