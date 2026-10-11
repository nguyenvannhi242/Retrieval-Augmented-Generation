"""Script to generate and validate the 60+ benchmark evaluation dataset."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT_DIR = Path(__file__).resolve().parent.parent
CORPUS_JSONL = ROOT_DIR / "data" / "processed" / "corpus.jsonl"
OUTPUT_BENCHMARK = ROOT_DIR / "data" / "evaluation" / "benchmark_queries.json"

BENCHMARK_DATA: List[Dict[str, Any]] = [
    # ── Category: Factual / Conceptual (English) ──
    {
        "query_id": "q001",
        "question": "What is the difference between concurrency and parallelism in FastAPI async?",
        "language": "en",
        "category": "factual",
        "relevant_sources": ["fastapi/docs/en/docs/async.md"],
    },
    {
        "query_id": "q002",
        "question": "How do standard Python type hints help FastAPI generate OpenAPI schemas and validation?",
        "language": "en",
        "category": "factual",
        "relevant_sources": ["fastapi/docs/en/docs/python-types.md"],
    },
    {
        "query_id": "q003",
        "question": "What does the response_model parameter in path operations do?",
        "language": "en",
        "category": "factual",
        "relevant_sources": ["fastapi/docs/en/docs/tutorial/response-model.md"],
    },
    {
        "query_id": "q004",
        "question": "What is OAuth2PasswordBearer in FastAPI security?",
        "language": "en",
        "category": "factual",
        "relevant_sources": ["fastapi/docs/en/docs/tutorial/security/first-steps.md"],
    },
    {
        "query_id": "q005",
        "question": "What is the role of BackgroundTasks in FastAPI responses?",
        "language": "en",
        "category": "factual",
        "relevant_sources": ["fastapi/docs/en/docs/tutorial/background-tasks.md"],
    },
    {
        "query_id": "q006",
        "question": "How does FastAPI handle dependency injection using Depends?",
        "language": "en",
        "category": "factual",
        "relevant_sources": ["fastapi/docs/en/docs/tutorial/dependencies/index.md"],
    },
    {
        "query_id": "q007",
        "question": "What is CORSMiddleware and why is it needed for frontend clients?",
        "language": "en",
        "category": "factual",
        "relevant_sources": ["fastapi/docs/en/docs/tutorial/cors.md"],
    },
    {
        "query_id": "q008",
        "question": "What is the difference between UploadFile and bytes when receiving uploaded files?",
        "language": "en",
        "category": "factual",
        "relevant_sources": ["fastapi/docs/en/docs/tutorial/request-files.md"],
    },
    {
        "query_id": "q009",
        "question": "What is APIRouter used for in large FastAPI applications?",
        "language": "en",
        "category": "factual",
        "relevant_sources": [
            "fastapi/docs/en/docs/tutorial/bigger-applications.md",
            "fastapi/docs/en/docs/reference/apirouter.md",
        ],
    },
    {
        "query_id": "q010",
        "question": "What is the default status code returned by FastAPI endpoints and how to customize it?",
        "language": "en",
        "category": "factual",
        "relevant_sources": ["fastapi/docs/en/docs/tutorial/response-status-code.md"],
    },

    # ── Category: Procedural / Code Examples (English) ──
    {
        "query_id": "q011",
        "question": "How do I declare query parameters with default values in FastAPI?",
        "language": "en",
        "category": "procedural",
        "relevant_sources": [
            "fastapi/docs/en/docs/tutorial/query-params.md",
            "fastapi/docs/en/docs/tutorial/query-params-str-validations.md",
        ],
    },
    {
        "query_id": "q012",
        "question": "How to validate string length and regular expressions in Query parameters?",
        "language": "en",
        "category": "procedural",
        "relevant_sources": ["fastapi/docs/en/docs/tutorial/query-params-str-validations.md"],
    },
    {
        "query_id": "q013",
        "question": "How can I run a FastAPI application in a Docker container?",
        "language": "en",
        "category": "procedural",
        "relevant_sources": ["fastapi/docs/en/docs/deployment/docker.md"],
    },
    {
        "query_id": "q014",
        "question": "How to raise an HTTPException with custom status code and detail message?",
        "language": "en",
        "category": "procedural",
        "relevant_sources": ["fastapi/docs/en/docs/tutorial/handling-errors.md"],
    },
    {
        "query_id": "q015",
        "question": "How to schedule background tasks using BackgroundTasks.add_task in a path operation?",
        "language": "en",
        "category": "procedural",
        "relevant_sources": ["fastapi/docs/en/docs/tutorial/background-tasks.md"],
    },
    {
        "query_id": "q016",
        "question": "How to mount static files in FastAPI using StaticFiles?",
        "language": "en",
        "category": "procedural",
        "relevant_sources": ["fastapi/docs/en/docs/tutorial/static-files.md"],
    },
    {
        "query_id": "q017",
        "question": "How to implement JWT authentication and generate bearer tokens in FastAPI?",
        "language": "en",
        "category": "procedural",
        "relevant_sources": ["fastapi/docs/en/docs/tutorial/security/oauth2-jwt.md"],
    },
    {
        "query_id": "q018",
        "question": "How to write tests for FastAPI endpoints using TestClient and pytest?",
        "language": "en",
        "category": "procedural",
        "relevant_sources": ["fastapi/docs/en/docs/tutorial/testing.md"],
    },
    {
        "query_id": "q019",
        "question": "How to use dependencies with yield to manage database sessions or cleanup?",
        "language": "en",
        "category": "procedural",
        "relevant_sources": ["fastapi/docs/en/docs/tutorial/dependencies/dependencies-with-yield.md"],
    },
    {
        "query_id": "q020",
        "question": "How to handle WebSockets connections for real-time messaging in FastAPI?",
        "language": "en",
        "category": "procedural",
        "relevant_sources": ["fastapi/docs/en/docs/advanced/websockets.md"],
    },
    {
        "query_id": "q021",
        "question": "How to declare request headers parameters using Header in FastAPI?",
        "language": "en",
        "category": "procedural",
        "relevant_sources": ["fastapi/docs/en/docs/tutorial/header-params.md"],
    },
    {
        "query_id": "q022",
        "question": "How to declare cookie parameters using Cookie in path operation functions?",
        "language": "en",
        "category": "procedural",
        "relevant_sources": ["fastapi/docs/en/docs/tutorial/cookie-params.md"],
    },
    {
        "query_id": "q023",
        "question": "How to read and parse form data using Form in FastAPI endpoints?",
        "language": "en",
        "category": "procedural",
        "relevant_sources": ["fastapi/docs/en/docs/tutorial/request-forms.md"],
    },
    {
        "query_id": "q024",
        "question": "How to configure application settings and environment variables with pydantic-settings?",
        "language": "en",
        "category": "procedural",
        "relevant_sources": ["fastapi/docs/en/docs/advanced/settings.md"],
    },
    {
        "query_id": "q025",
        "question": "How to mount sub-applications in FastAPI using app.mount?",
        "language": "en",
        "category": "procedural",
        "relevant_sources": ["fastapi/docs/en/docs/advanced/sub-applications.md"],
    },

    # ── Category: Multi-source Synthesis (English) ──
    {
        "query_id": "q026",
        "question": "How to declare body, path and query parameters all in the same endpoint function?",
        "language": "en",
        "category": "multi_source",
        "relevant_sources": [
            "fastapi/docs/en/docs/tutorial/body.md",
            "fastapi/docs/en/docs/tutorial/path-params.md",
            "fastapi/docs/en/docs/tutorial/query-params.md",
        ],
    },
    {
        "query_id": "q027",
        "question": "How to accept both file uploads and form fields simultaneously in FastAPI?",
        "language": "en",
        "category": "multi_source",
        "relevant_sources": [
            "fastapi/docs/en/docs/tutorial/request-forms-and-files.md",
            "fastapi/docs/en/docs/tutorial/request-files.md",
            "fastapi/docs/en/docs/tutorial/request-forms.md",
        ],
    },
    {
        "query_id": "q028",
        "question": "How to structure and modularize a large application with APIRouter and multiple routers?",
        "language": "en",
        "category": "multi_source",
        "relevant_sources": [
            "fastapi/docs/en/docs/tutorial/bigger-applications.md",
            "fastapi/docs/en/docs/reference/apirouter.md",
        ],
    },
    {
        "query_id": "q029",
        "question": "How to deploy FastAPI in production using Docker containers with worker processes?",
        "language": "en",
        "category": "multi_source",
        "relevant_sources": [
            "fastapi/docs/en/docs/deployment/docker.md",
            "fastapi/docs/en/docs/deployment/server-workers.md",
            "fastapi/docs/en/docs/deployment/concepts.md",
        ],
    },
    {
        "query_id": "q030",
        "question": "How to authenticate users with security dependencies and extract the current active user?",
        "language": "en",
        "category": "multi_source",
        "relevant_sources": [
            "fastapi/docs/en/docs/tutorial/security/get-current-user.md",
            "fastapi/docs/en/docs/tutorial/security/simple-oauth2.md",
            "fastapi/docs/en/docs/tutorial/dependencies/index.md",
        ],
    },

    # ── Category: Cross-lingual Vietnamese Queries ──
    {
        "query_id": "q031",
        "question": "Làm thế nào để khai báo query parameters trong FastAPI?",
        "language": "vi",
        "category": "cross_lingual",
        "relevant_sources": [
            "fastapi/docs/en/docs/tutorial/query-params.md",
            "fastapi/docs/en/docs/tutorial/query-params-str-validations.md",
        ],
    },
    {
        "query_id": "q032",
        "question": "Cách kiểm tra độ dài chuỗi và biểu thức chính quy regex cho query parameter?",
        "language": "vi",
        "category": "cross_lingual",
        "relevant_sources": ["fastapi/docs/en/docs/tutorial/query-params-str-validations.md"],
    },
    {
        "query_id": "q033",
        "question": "Làm thế nào để đóng gói và triển khai ứng dụng FastAPI trong Docker container?",
        "language": "vi",
        "category": "cross_lingual",
        "relevant_sources": ["fastapi/docs/en/docs/deployment/docker.md"],
    },
    {
        "query_id": "q034",
        "question": "Cách tạo background tasks để xử lý tác vụ ngầm sau khi trả về response?",
        "language": "vi",
        "category": "cross_lingual",
        "relevant_sources": ["fastapi/docs/en/docs/tutorial/background-tasks.md"],
    },
    {
        "query_id": "q035",
        "question": "Làm sao để cấu hình CORSMiddleware cho phép frontend React hoặc Vue gọi API?",
        "language": "vi",
        "category": "cross_lingual",
        "relevant_sources": ["fastapi/docs/en/docs/tutorial/cors.md"],
    },
    {
        "query_id": "q036",
        "question": "Cách ném ngoại lệ HTTPException kèm theo status code và nội dung lỗi?",
        "language": "vi",
        "category": "cross_lingual",
        "relevant_sources": ["fastapi/docs/en/docs/tutorial/handling-errors.md"],
    },
    {
        "query_id": "q037",
        "question": "Làm thế nào để sử dụng cơ chế Dependency Injection với Depends trong FastAPI?",
        "language": "vi",
        "category": "cross_lingual",
        "relevant_sources": ["fastapi/docs/en/docs/tutorial/dependencies/index.md"],
    },
    {
        "query_id": "q038",
        "question": "Cách upload file đơn hoặc danh sách nhiều file bằng UploadFile?",
        "language": "vi",
        "category": "cross_lingual",
        "relevant_sources": ["fastapi/docs/en/docs/tutorial/request-files.md"],
    },
    {
        "query_id": "q039",
        "question": "Làm thế nào để cấu hình static files bằng StaticFiles trong FastAPI?",
        "language": "vi",
        "category": "cross_lingual",
        "relevant_sources": ["fastapi/docs/en/docs/tutorial/static-files.md"],
    },
    {
        "query_id": "q040",
        "question": "Cách tạo và xác thực token JWT với OAuth2 trong FastAPI?",
        "language": "vi",
        "category": "cross_lingual",
        "relevant_sources": ["fastapi/docs/en/docs/tutorial/security/oauth2-jwt.md"],
    },
    {
        "query_id": "q041",
        "question": "Cách viết kiểm thử tự động cho endpoint bằng TestClient và pytest?",
        "language": "vi",
        "category": "cross_lingual",
        "relevant_sources": ["fastapi/docs/en/docs/tutorial/testing.md"],
    },
    {
        "query_id": "q042",
        "question": "Làm sao để giải phóng tài nguyên cơ sở dữ liệu bằng dependency có chứa yield?",
        "language": "vi",
        "category": "cross_lingual",
        "relevant_sources": ["fastapi/docs/en/docs/tutorial/dependencies/dependencies-with-yield.md"],
    },
    {
        "query_id": "q043",
        "question": "Cách thiết lập giao tiếp WebSocket real-time hai chiều trong FastAPI?",
        "language": "vi",
        "category": "cross_lingual",
        "relevant_sources": ["fastapi/docs/en/docs/advanced/websockets.md"],
    },
    {
        "query_id": "q044",
        "question": "Làm thế nào để cấu trúc dự án lớn bằng cách chia nhiều APIRouter con?",
        "language": "vi",
        "category": "cross_lingual",
        "relevant_sources": [
            "fastapi/docs/en/docs/tutorial/bigger-applications.md",
            "fastapi/docs/en/docs/reference/apirouter.md",
        ],
    },
    {
        "query_id": "q045",
        "question": "Khi nào nên dùng async def và khi nào dùng def thông thường trong FastAPI?",
        "language": "vi",
        "category": "cross_lingual",
        "relevant_sources": ["fastapi/docs/en/docs/async.md"],
    },
    {
        "query_id": "q046",
        "question": "Làm sao để lọc dữ liệu trả về bằng cách định nghĩa response_model?",
        "language": "vi",
        "category": "cross_lingual",
        "relevant_sources": ["fastapi/docs/en/docs/tutorial/response-model.md"],
    },
    {
        "query_id": "q047",
        "question": "Cách nhận dữ liệu form thông qua Form thay vì JSON trong FastAPI?",
        "language": "vi",
        "category": "cross_lingual",
        "relevant_sources": ["fastapi/docs/en/docs/tutorial/request-forms.md"],
    },
    {
        "query_id": "q048",
        "question": "Cách đọc giá trị Cookie gửi từ trình duyệt bằng Cookie parameter?",
        "language": "vi",
        "category": "cross_lingual",
        "relevant_sources": ["fastapi/docs/en/docs/tutorial/cookie-params.md"],
    },
    {
        "query_id": "q049",
        "question": "Làm thế nào để đọc custom HTTP Headers gửi lên từ client?",
        "language": "vi",
        "category": "cross_lingual",
        "relevant_sources": ["fastapi/docs/en/docs/tutorial/header-params.md"],
    },
    {
        "query_id": "q050",
        "question": "Cách quản lý cấu hình và biến môi trường bằng BaseSettings trong FastAPI?",
        "language": "vi",
        "category": "cross_lingual",
        "relevant_sources": ["fastapi/docs/en/docs/advanced/settings.md"],
    },

    # ── Category: Unanswerable / Out of Scope (Negatives) ──
    {
        "query_id": "q051",
        "question": "How do I configure Django ORM models with migrations and foreign keys?",
        "language": "en",
        "category": "unanswerable",
        "relevant_sources": [],
    },
    {
        "query_id": "q052",
        "question": "How to set up Apache Kafka consumer group with Spring Boot?",
        "language": "en",
        "category": "unanswerable",
        "relevant_sources": [],
    },
    {
        "query_id": "q053",
        "question": "How to configure Ruby on Rails Active Record callbacks and validations?",
        "language": "en",
        "category": "unanswerable",
        "relevant_sources": [],
    },
    {
        "query_id": "q054",
        "question": "How do I setup Angular route guards with RxJS observables?",
        "language": "en",
        "category": "unanswerable",
        "relevant_sources": [],
    },
    {
        "query_id": "q055",
        "question": "How do I configure CUDA drivers and PyTorch GPU memory pinning on Windows?",
        "language": "en",
        "category": "unanswerable",
        "relevant_sources": [],
    },
    {
        "query_id": "q056",
        "question": "Làm thế nào để cấu hình Redux Toolkit store và slice trong ứng dụng React frontend?",
        "language": "vi",
        "category": "unanswerable",
        "relevant_sources": [],
    },
    {
        "query_id": "q057",
        "question": "Cách tạo Kubernetes StatefulSet với Persistent Volume Claim trong Helm chart?",
        "language": "vi",
        "category": "unanswerable",
        "relevant_sources": [],
    },
    {
        "query_id": "q058",
        "question": "Làm sao để viết smart contract Solidity bằng Hardhat và deploy lên Ethereum?",
        "language": "vi",
        "category": "unanswerable",
        "relevant_sources": [],
    },
    {
        "query_id": "q059",
        "question": "Cách cấu hình Nginx reverse proxy với PHP-FPM trên hệ điều hành Ubuntu?",
        "language": "vi",
        "category": "unanswerable",
        "relevant_sources": [],
    },
    {
        "query_id": "q060",
        "question": "Làm thế nào để train model YOLOv8 nhận diện biển số xe bằng Ultralytics?",
        "language": "vi",
        "category": "unanswerable",
        "relevant_sources": [],
    },
]


def generate_benchmark() -> None:
    """Validates and saves the benchmark queries."""
    OUTPUT_BENCHMARK.parent.mkdir(parents=True, exist_ok=True)

    # Load all distinct valid sources in the indexed corpus
    valid_sources = set()
    if CORPUS_JSONL.exists():
        with open(CORPUS_JSONL, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    item = json.loads(line)
                    valid_sources.add(item["source"])

    print(f"Total corpus valid sources: {len(valid_sources)}")

    # Validate benchmark sources
    invalid_sources = []
    for q in BENCHMARK_DATA:
        for s in q["relevant_sources"]:
            if s not in valid_sources:
                invalid_sources.append((q["query_id"], s))

    if invalid_sources:
        raise ValueError(f"Found invalid relevant_sources in benchmark: {invalid_sources}")

    with open(OUTPUT_BENCHMARK, "w", encoding="utf-8") as f:
        json.dump(BENCHMARK_DATA, f, indent=2, ensure_ascii=False)

    print(f"✅ Successfully wrote {len(BENCHMARK_DATA)} benchmark queries to {OUTPUT_BENCHMARK}")

    # Breakdown statistics
    en_count = sum(1 for q in BENCHMARK_DATA if q["language"] == "en")
    vi_count = sum(1 for q in BENCHMARK_DATA if q["language"] == "vi")
    unans_count = sum(1 for q in BENCHMARK_DATA if q["category"] == "unanswerable")
    cats = {}
    for q in BENCHMARK_DATA:
        cats[q["category"]] = cats.get(q["category"], 0) + 1

    print("\nBenchmark Category Breakdown:")
    for cat, cnt in cats.items():
        print(f" • {cat}: {cnt}")
    print(f"Language: EN={en_count}, VI={vi_count}")
    print(f"Answerable queries: {len(BENCHMARK_DATA) - unans_count}, Unanswerable: {unans_count}")


if __name__ == "__main__":
    generate_benchmark()
