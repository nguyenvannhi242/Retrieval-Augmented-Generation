# DevDocs RAG — Technical Documentation Q&A Chatbot

A production-ready **Retrieval-Augmented Generation (RAG)** system for answering technical questions about FastAPI documentation. Supports bilingual queries (Vietnamese & English), provides citation-grounded answers with source references `[S1]`, and measures real-time latency.

> **Tech Stack**: Python · FastAPI · Streamlit · ChromaDB · Sentence-Transformers · Ollama · LangChain · Docker

---

## Architecture

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                          devdocs-rag Pipeline                              │
│                                                                             │
│  ┌──────────────┐    ┌────────────────┐    ┌──────────────────────────────┐ │
│  │  Ingestion    │    │   Retrieval     │    │       Generation             │ │
│  │              │    │                │    │                              │ │
│  │ Markdown     │    │ BGE-small      │    │ Ollama (gemma2:2b)           │ │
│  │ Parsing  ────┼──▶ │ Embeddings ────┼──▶ │ + Citation Validation ───────┼─┤
│  │ + LangChain  │    │ + ChromaDB     │    │ + Refusal Guardrail         │ │
│  │ Chunking     │    │ Vector Search  │    │                              │ │
│  └──────────────┘    └────────────────┘    └──────────────────────────────┘ │
│         │                                            │                      │
│         ▼                                            ▼                      │
│  corpus.jsonl                              FastAPI REST Backend             │
│  (1,591 chunks)                           POST /chat · GET /health          │
│                                                      │                      │
│                                            Streamlit Frontend               │
│                                           Chat UI · Latency Badges          │
│                                          Source Citations · Chunks Viewer    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Key Features

| Feature | Description |
|:---|:---|
| **Semantic Retrieval** | `BAAI/bge-small-en-v1.5` embeddings + ChromaDB vector search over 1,591 documentation chunks |
| **Local LLM Generation** | `gemma2:2b` via Ollama — fully offline, privacy-preserving, ~845ms end-to-end latency |
| **Citation Validation** | Auto-extracts `[S1]`, `[S2]` tags from answers, maps them to source metadata, detects hallucinated citations |
| **Bilingual Support** | Vietnamese & English queries against English documentation corpus |
| **Refusal Guardrail** | Refuses out-of-scope questions (90.0% held-out refusal rate) without fabricating content |
| **REST API** | FastAPI backend with Pydantic schemas, health monitoring, and latency metrics |
| **Docker Deployment** | Multi-container Docker Compose setup (backend + frontend) |

---

## Project Structure

```text
devdocs-rag/
├── api/                        # FastAPI backend (endpoints, Pydantic schemas)
│   ├── main.py                 # Application with lifespan, /chat, /health
│   └── schemas.py              # ChatRequest, ChatResponse, HealthResponse
├── ingestion/                  # Document parsing & chunking pipeline
│   ├── fetch_docs.py           # Git sparse-checkout of FastAPI docs
│   ├── chunker.py              # LangChain Markdown + Recursive splitting
│   ├── build_corpus.py         # Pipeline orchestration → corpus.jsonl
│   └── schemas.py              # DocumentChunk data model
├── retrieval/                  # Vector database indexing & search
│   ├── indexer.py              # Batch embedding + ChromaDB upsert
│   └── search.py               # Semantic search with BGE query prefix
├── generation/                 # LLM generation & citation validation
│   ├── generator.py            # RAGPipeline, citation extraction, retry logic
│   └── prompts.py              # System prompt with 6 technical rules
├── evaluation/                 # Benchmark & ablation experiment scripts
│   ├── build_benchmark_dataset.py
│   ├── evaluate_retrieval.py   # Recall@5, MRR@5, Hit Rate@5
│   ├── evaluate_e2e.py         # RAG vs No-RAG with statistical testing
│   ├── evaluate_k_and_models.py
│   ├── evaluate_refusal_and_overrefusal.py
│   ├── compare_embeddings.py   # BGE vs Multilingual E5
│   ├── compare_chunks.py       # Chunk size ablation (400/750/1200)
│   └── calculate_auroc.py      # Answerable vs unanswerable separation
├── frontend/                   # Streamlit chat interface
│   └── app.py
├── tests/                      # 19 automated tests (pytest)
│   ├── test_ingestion.py
│   ├── test_generation.py
│   ├── test_api.py
│   └── test_evaluation.py
├── data/
│   ├── raw/                    # Source markdown documents
│   ├── processed/              # corpus.jsonl + ChromaDB storage
│   └── evaluation/             # Benchmark queries, result JSON & CSV
├── Dockerfile.api
├── Dockerfile.frontend
├── docker-compose.yml
└── requirements.txt
```

---

## Getting Started

> [!NOTE]
> Model weights and ChromaDB data are not stored in the repository. Follow the steps below to initialize them.

### Prerequisites

- Python 3.11+
- [Ollama](https://ollama.com) installed and running
- Git

### 1. Environment Setup

```bash
python -m venv .venv

# Windows
.\.venv\Scripts\Activate.ps1
# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Download LLM Model

```bash
ollama run gemma2:2b
```

Verify Ollama is running at `http://localhost:11434`.

### 3. Build Document Index

```bash
# Fetch official FastAPI English documentation
python -m ingestion.fetch_docs

# Chunk documents using LangChain (750 chars, 100 overlap)
python -m ingestion.build_corpus

# Generate embeddings and index into ChromaDB
python -m retrieval.indexer
```

### 4. Run Application

**Backend** (FastAPI):
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

**Frontend** (Streamlit):
```bash
streamlit run frontend/app.py --server.port 8501
```

| Service | URL |
|:---|:---|
| Chat UI | http://localhost:8501 |
| API Docs (Swagger) | http://localhost:8000/docs |
| Health Check | http://localhost:8000/health |

---

## Docker Deployment

```bash
docker compose up --build -d
```

> [!TIP]
> The backend container connects to Ollama on the host machine via `host.docker.internal:11434`.

```bash
docker compose down   # Stop services
```

---

## Evaluation & Testing

### Run Benchmark Suite

```bash
# Retrieval baseline (Recall@5, MRR@5, Hit Rate@5)
python -m evaluation.evaluate_retrieval

# End-to-end RAG vs No-RAG comparison
python -m evaluation.evaluate_e2e

# Unit & integration tests (19 tests)
pytest tests/ -v
```

### Benchmark Results

**Evaluation methodology**: 60 benchmark queries (50 answerable + 10 unanswerable), bilingual (35 EN + 25 VI). Statistical validation via paired t-test, Wilcoxon signed-rank test, and Bootstrap 95% CI (10,000 resamples).

#### Core Metrics

| Metric | RAG Pipeline | No-RAG Baseline | Notes |
|:---|:---:|:---:|:---|
| **Retrieval Recall@5** | **85.67%** | — | Answerable queries (n=50) |
| **Hit Rate@5** | **92.00%** | — | ≥1 relevant source in top-5 |
| **Answerable Token F1** | **24.07%** | 18.25% | **+5.81pp** uplift (p < 0.001) |
| **Citation Precision** | **69.93%** | — | At k=5 configuration |
| **Citation Accuracy** | **74.00%** | — | ≥1 correct citation, 0 hallucinated |
| **Hallucinated Citations** | **0 tags** | — | All tags within [S1]-[S5] range |
| **Refusal Rate (held-out)** | **90.0%** | 0.0% | 20 unseen out-of-scope questions |
| **End-to-End Latency** | **845.6 ms** | ~850 ms | RTX 5070, k=5 |

> [!IMPORTANT]
> The +5.81pp uplift on answerable queries (n=50) is the headline metric. The larger +11.51pp at n=60 is inflated by RAG correctly refusing out-of-scope questions (refusal F1 ≈ 40% vs No-RAG 0%).

#### Ablation Studies

**Top-k (k ∈ {3, 5, 8})**:

| k | Recall@k | Answer F1 | Citation Precision | Latency |
|:---:|:---:|:---:|:---:|:---:|
| 3 | 81.67% | 23.31% | 66.67% | 719.7 ms |
| **5** | **85.67%** | **25.71%** | **69.93%** | **845.6 ms** |
| 8 | 91.00% | 25.81% | 54.04% | 981.2 ms |

*k=5 selected*: k=8 increases Recall (+5.33pp) but Citation Precision drops sharply (-15.89pp) as longer context dilutes LLM attention.

**Chunk Size (400 / 750 / 1200 chars)**:

| Size | Chunks | Code Block Break Rate | Recall@5 |
|:---:|:---:|:---:|:---:|
| 400 | 2,655 | 9.45% | 84.67% |
| **750** | **1,591** | **7.86%** | **85.67%** |
| 1200 | 1,259 | 5.08% | 89.67% |

*750 selected*: Balanced trade-off between context size for the 2B model and information density.

**LLM Comparison (GPU RTX 5070)**:

| Model | Throughput | Latency | Answer F1 | Citation Prec |
|:---|:---:|:---:|:---:|:---:|
| **Gemma 2 2B** | 185.0 t/s | **847 ms** | **24.66%** | **66.00%** |
| Qwen 2.5 3B | 183.7 t/s | 1,803 ms | 17.94% | 33.67% |

*Gemma 2B selected*: 2× better citation compliance and sub-1s latency.

---

## Technical Design Decisions

| Decision | Rationale |
|:---|:---|
| **BGE-small-en-v1.5** over multilingual E5 | Simpler pipeline (no prefix management); 85.67% Recall already sufficient. E5 noted for future work (AUROC 0.95 vs 0.87). |
| **chunk_size=750** | Preserves complete code blocks within sections; optimal for 2B model context window. |
| **top_k=5** | Sweet spot: Recall 85.67% with Citation Precision 69.93%. k=8 degrades citation quality. |
| **temperature=0.0** | Deterministic outputs for reproducible evaluation and consistent user experience. |
| **Local LLM (Ollama)** | Full data privacy; no API costs; sub-1s latency on consumer GPU. |

---

## Limitations & Future Work

> [!WARNING]
> **Refusal vs Over-refusal trade-off**: The strict prompt guardrail achieves 90.0% refusal on out-of-scope queries but causes 12.0% over-refusal on complex in-scope questions.
> *Mitigation*: Few-shot prompting with edge-case examples or a dedicated intent classifier before the RAG pipeline.

> [!NOTE]
> **Token F1 limitations for Vietnamese**: Token F1 penalizes synonym differences and verbose code-inclusive answers heavily.
> *Mitigation*: LLM-as-a-Judge evaluation (GPT-4o / Claude) with a 4-criterion rubric (Correctness, Groundedness, Completeness, Hallucination) validated against human evaluation via Cohen's κ.

---

## License

This project is licensed under the [MIT License](LICENSE).
