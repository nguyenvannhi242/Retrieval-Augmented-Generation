"""Tests for document parsing, chunking, and schema validation."""

from pathlib import Path
import pytest
from ingestion.chunker import (
    DocumentChunker,
    extract_title_and_clean_markdown,
    file_path_to_fastapi_url,
    slugify,
)
from ingestion.schemas import DocumentChunk


def test_slugify():
    assert slugify("First Steps: Hello World!") == "first-steps-hello-world"
    assert slugify("Query Parameters & String Validations") == "query-parameters-string-validations"


def test_extract_title():
    sample_md = """# First Steps
<!-- badge comment -->

Here is an example.
## Details
More details here.
"""
    title, cleaned = extract_title_and_clean_markdown(sample_md, "first-steps")
    assert title == "First Steps"
    assert "<!-- badge comment -->" not in cleaned
    assert "## Details" in cleaned


def test_file_path_to_fastapi_url():
    p1 = Path("tutorial/first-steps.md")
    url1 = file_path_to_fastapi_url(p1, section_anchor="create-it")
    assert url1 == "https://fastapi.tiangolo.com/tutorial/first-steps/#create-it"

    p2 = Path("index.md")
    url2 = file_path_to_fastapi_url(p2)
    assert url2 == "https://fastapi.tiangolo.com/"


def test_document_chunk_schema():
    chunk = DocumentChunk(
        chunk_id="fastapi_test_1",
        text="FastAPI is a modern, fast web framework for Python.",
        source="fastapi/docs/en/docs/index.md",
        title="FastAPI",
        section="Introduction",
        url="https://fastapi.tiangolo.com/",
        license="MIT License (Sebastián Ramírez)",
    )
    d = chunk.to_dict()
    assert d["chunk_id"] == "fastapi_test_1"
    assert d["license"] == "MIT License (Sebastián Ramírez)"
    assert "url" in d
    assert "source" in d


def test_chunker_processing(tmp_path: Path):
    doc_file = tmp_path / "sample.md"
    doc_file.write_text(
        """# Sample Guide
Welcome to the sample guide.

## Installation
Run pip install sample to get started. It is very fast and efficient.

## Usage
Import the package and enjoy building applications!
""",
        encoding="utf-8",
    )

    chunker = DocumentChunker(chunk_size=200, chunk_overlap=20, min_chunk_length=20)
    chunks = list(chunker.process_file(doc_file, base_dir=tmp_path))

    assert len(chunks) >= 2
    for c in chunks:
        assert c.title == "Sample Guide"
        assert c.chunk_id.startswith("fastapi_sample_")
        assert len(c.text) >= 20
