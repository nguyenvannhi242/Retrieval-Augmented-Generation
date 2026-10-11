# devdocs-rag: Chatbot Hỏi Đáp Tài Liệu Lập Trình (FastAPI, Python, Docker)

Hệ thống RAG (Retrieval-Augmented Generation) cho phép người dùng hỏi bằng tiếng Việt, truy xuất tài liệu kỹ thuật chính thức và sinh câu trả lời kèm trích dẫn nguồn (source citations & URLs).

---

## 🎯 Mục tiêu & Tính năng chính

- **Ngôn ngữ người dùng**: Hỏi đáp bằng tiếng Việt tự nhiên (hỗ trợ cả thuật ngữ kỹ thuật tiếng Anh).
- **Corpus nguồn**:
  - **FastAPI Documentation** (nguồn chính): Hơn 100+ trang tài liệu chuẩn hóa từ repository chính thức của FastAPI.
  - **Python Tutorial & Library Reference**: Bổ sung kiến thức nền tảng về Python async, type hints, typing.
  - **Docker Documentation**: Kiến thức triển khai container hóa cho ứng dụng FastAPI.
- **Chuẩn hóa Corpus**:
  - Định dạng JSONL chuẩn (`data/processed/corpus.jsonl`).
  - Mỗi chunk gồm: `chunk_id`, `text`, `source`, `title`, `url`, `license`.
- **Vector Database**: ChromaDB (`data/processed/chroma_db/`).
- **Embedding Model**: `BAAI/bge-small-en-v1.5` qua `sentence-transformers`.
- **LLM**: Local model qua Ollama (`gemma-4-E2B` hoặc `gemma2:2b`/`llama3.2:3b`).
- **Backend API**: FastAPI REST API (`/query`, `/health`, `/stats`).
- **Frontend UI**: Streamlit dashboard trực quan, hiển thị câu trả lời và thẻ trích dẫn tài liệu tham khảo kèm liên kết.
- **Đánh giá (Evaluation)**: Bộ câu hỏi kiểm thử, đo lường Recall@k, MRR và answer correctness.
- **Triển khai**: Docker Compose.

---

## 📁 Cấu trúc thư mục

```text
devdocs-rag/
├── data/
│   ├── raw/               # Tài liệu gốc (FastAPI markdown, Python docs)
│   ├── processed/         # JSONL chuẩn hóa và ChromaDB vector storage
│   └── evaluation/        # Bộ câu hỏi đánh giá benchmark
├── ingestion/             # Crawler, parser, LangChain chunking và xuất JSONL
├── retrieval/             # Semantic search, ChromaDB client, BGE-small embedding
├── generation/            # RAG prompt, kết nối Ollama local LLM, trích dẫn nguồn
├── evaluation/            # Đo lường Recall@k, MRR, độ chính xác
├── api/                   # FastAPI backend server
├── frontend/              # Streamlit web application
├── tests/                 # Unit tests & integration tests
├── docker-compose.yml     # Cấu hình triển khai hệ thống
├── Dockerfile             # Dockerfile cho backend & frontend
├── requirements.txt       # Danh sách thư viện Python
├── LOG.md                 # Nhật ký phát triển chi tiết qua từng giai đoạn
└── README.md
```

---

## 🚀 Hướng dẫn cài đặt & Chạy nhanh

### 1. Cài đặt môi trường
```bash
python -m venv .venv
# Trên Windows:
.\.venv\Scripts\Activate.ps1
# Trên Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Thu thập và chuẩn hóa dữ liệu
```bash
# Clone tài liệu FastAPI và parse thành corpus.jsonl
python ingestion/fetch_docs.py
python ingestion/chunk_and_index.py
```

### 3. Thử nghiệm tìm kiếm ngữ nghĩa
```bash
python retrieval/search.py --query "Làm thế nào để khai báo query parameters trong FastAPI?"
```
