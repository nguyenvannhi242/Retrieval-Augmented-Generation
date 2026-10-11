"""Document parsing and chunking pipeline using LangChain."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterator, List, Tuple

from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)

from ingestion.schemas import DocumentChunk


def slugify(text: str) -> str:
    """Creates a URL anchor slug from header text."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return text.strip("-")


def parse_header_text_and_anchor(header_line: str) -> Tuple[str, str]:
    """Extracts clean header title and explicit MkDocs anchor if present."""
    # Look for MkDocs attribute like '{ #some-anchor }'
    anchor = ""
    attr_match = re.search(r"\{[ \t]*#([a-zA-Z0-9_-]+)[ \t]*\}", header_line)
    if attr_match:
        anchor = attr_match.group(1)
        header_line = re.sub(r"\{[ \t]*#[a-zA-Z0-9_-]+[ \t]*\}", "", header_line)

    # Strip HTML tags like <abbr> or <span>
    clean_line = re.sub(r"<[^>]+>", "", header_line).strip()
    return clean_line, anchor


def extract_title_and_clean_markdown(content: str, filename: str) -> Tuple[str, str]:
    """Extracts top level title and cleans markdown content."""
    lines = content.splitlines()
    title = ""
    cleaned_lines: List[str] = []

    # Check for frontmatter
    in_frontmatter = False
    if lines and lines[0].strip() == "---":
        in_frontmatter = True
        lines = lines[1:]

    for line in lines:
        if in_frontmatter:
            if line.strip() == "---":
                in_frontmatter = False
            elif line.startswith("title:"):
                raw_t = line.split("title:", 1)[1].strip().strip('"\'')
                clean_t, _ = parse_header_text_and_anchor(raw_t)
                title = clean_t
            continue

        # Check for first H1 header if title not found yet
        if not title and line.startswith("# "):
            raw_h1 = line[2:].strip()
            clean_h1, _ = parse_header_text_and_anchor(raw_h1)
            title = clean_h1

        # Filter out markdown badges or html comments
        if line.strip().startswith("<!--") and line.strip().endswith("-->"):
            continue

        cleaned_lines.append(line)

    if not title:
        title = filename.replace("-", " ").replace("_", " ").title()

    return title, "\n".join(cleaned_lines)


def file_path_to_fastapi_url(rel_path: Path, section_anchor: str = "") -> str:
    """Maps local relative path under docs/en/docs/ to official documentation URL."""
    # rel_path is relative to docs/en/docs/, e.g. 'tutorial/first-steps.md' or 'index.md'
    parts = list(rel_path.parts)
    # Remove extension
    filename = rel_path.stem
    if filename == "index":
        if len(parts) == 1:
            url_path = ""
        else:
            url_path = "/".join(parts[:-1]) + "/"
    else:
        parts[-1] = filename
        url_path = "/".join(parts) + "/"

    base_url = "https://fastapi.tiangolo.com"
    full_url = f"{base_url}/{url_path}".rstrip("/") + "/"
    if section_anchor:
        full_url = f"{full_url}#{section_anchor}"
    return full_url


class DocumentChunker:
    """Chunks Markdown documents into normalized DocumentChunk objects."""

    def __init__(
        self,
        chunk_size: int = 750,
        chunk_overlap: int = 100,
        min_chunk_length: int = 50,
    ) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_length = min_chunk_length

        self.headers_to_split = [
            ("#", "h1"),
            ("##", "h2"),
            ("###", "h3"),
        ]
        self.header_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=self.headers_to_split,
            strip_headers=False,
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n```", "\n\n", "\n", ". ", " ", ""],
            keep_separator=True,
        )

    def process_file(
        self,
        file_path: Path,
        base_dir: Path,
        license_text: str = "MIT License (Sebastián Ramírez)",
        source_prefix: str = "fastapi/docs/en/docs",
    ) -> Iterator[DocumentChunk]:
        """Processes a single markdown file into a series of DocumentChunk instances."""
        rel_path = file_path.relative_to(base_dir)
        raw_content = file_path.read_text(encoding="utf-8", errors="replace")

        doc_title, cleaned_content = extract_title_and_clean_markdown(
            raw_content, file_path.stem
        )

        header_splits = self.header_splitter.split_text(cleaned_content)
        chunk_counter = 0

        for split in header_splits:
            raw_section = (
                split.metadata.get("h3")
                or split.metadata.get("h2")
                or split.metadata.get("h1")
                or ""
            )
            section_title, explicit_anchor = parse_header_text_and_anchor(raw_section)
            anchor = explicit_anchor or (slugify(section_title) if section_title else "")
            canonical_url = file_path_to_fastapi_url(rel_path, section_anchor=anchor)

            # Sub-split long sections
            sub_chunks = self.text_splitter.split_text(split.page_content)

            for sub_text in sub_chunks:
                clean_chunk_text = sub_text.strip()
                if len(clean_chunk_text) < self.min_chunk_length:
                    continue

                chunk_counter += 1
                full_rel_stem = str(rel_path.with_suffix("")).replace("\\", "_").replace("/", "_")
                doc_slug = slugify(full_rel_stem)
                unique_chunk_id = f"fastapi_{doc_slug}_{chunk_counter}"

                yield DocumentChunk(
                    chunk_id=unique_chunk_id,
                    text=clean_chunk_text,
                    source=f"{source_prefix}/{rel_path.as_posix()}",
                    title=doc_title,
                    section=section_title,
                    url=canonical_url,
                    license=license_text,
                    metadata={
                        "char_count": len(clean_chunk_text),
                        "source_file": rel_path.as_posix(),
                    },
                )
