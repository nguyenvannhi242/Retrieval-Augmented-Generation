"""Fetch official FastAPI and complementary documentation.

Supports cloning FastAPI docs via git sparse-checkout to keep repository size minimal
and fetching complementary Python/Docker reference materials.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = ROOT_DIR / "data" / "raw"
FASTAPI_REPO_URL = "https://github.com/fastapi/fastapi.git"
FASTAPI_RAW_TARGET = RAW_DATA_DIR / "fastapi_docs"


def fetch_fastapi_docs(target_dir: Path = FASTAPI_RAW_TARGET) -> Path:
    """Clones or extracts the official English docs from the FastAPI repository."""
    target_dir.parent.mkdir(parents=True, exist_ok=True)
    temp_clone_dir = RAW_DATA_DIR / "_fastapi_clone_temp"

    if (target_dir / "tutorial").exists() and any(target_dir.glob("**/*.md")):
        md_count = len(list(target_dir.glob("**/*.md")))
        logger.info(f"FastAPI docs already exist at {target_dir} ({md_count} markdown files).")
        return target_dir

    logger.info("Cloning FastAPI English docs via git sparse-checkout...")
    try:
        if temp_clone_dir.exists():
            shutil.rmtree(temp_clone_dir, ignore_errors=True)

        # Clone repository with sparse-checkout and depth 1
        subprocess.run(
            [
                "git",
                "clone",
                "--depth",
                "1",
                "--filter=blob:none",
                "--sparse",
                FASTAPI_REPO_URL,
                str(temp_clone_dir),
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        # Sparse-checkout docs/en/docs
        subprocess.run(
            ["git", "sparse-checkout", "set", "docs/en/docs"],
            cwd=str(temp_clone_dir),
            check=True,
            capture_output=True,
            text=True,
        )

        source_en_docs = temp_clone_dir / "docs" / "en" / "docs"
        if not source_en_docs.exists():
            raise FileNotFoundError(f"Expected docs directory not found at {source_en_docs}")

        if target_dir.exists():
            shutil.rmtree(target_dir, ignore_errors=True)

        shutil.copytree(source_en_docs, target_dir)
        logger.info(f"Successfully copied FastAPI English docs to {target_dir}")

        # Clean up temporary clone
        shutil.rmtree(temp_clone_dir, ignore_errors=True)

    except Exception as exc:
        logger.warning(f"Git sparse-checkout failed ({exc}). Falling back to shallow clone...")
        if temp_clone_dir.exists():
            shutil.rmtree(temp_clone_dir, ignore_errors=True)

        subprocess.run(
            ["git", "clone", "--depth", "1", FASTAPI_REPO_URL, str(temp_clone_dir)],
            check=True,
            capture_output=True,
            text=True,
        )
        source_en_docs = temp_clone_dir / "docs" / "en" / "docs"
        if target_dir.exists():
            shutil.rmtree(target_dir, ignore_errors=True)
        shutil.copytree(source_en_docs, target_dir)
        shutil.rmtree(temp_clone_dir, ignore_errors=True)

    md_files = list(target_dir.glob("**/*.md"))
    logger.info(f"FastAPI English documentation ready: {len(md_files)} markdown files found.")
    return target_dir


if __name__ == "__main__":
    docs_path = fetch_fastapi_docs()
    print(f"Docs fetched to: {docs_path}")
