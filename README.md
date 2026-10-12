# devdocs-rag: Chatbot Hỏi Đáp Tài Liệu Lập Trình (FastAPI, Python, Docker)

Hệ thống RAG (Retrieval-Augmented Generation) cho phép người dùng hỏi bằng tiếng Việt hoặc tiếng Anh, tự động truy xuất ngữ cảnh chính xác từ tài liệu chính thức và sinh câu trả lời kèm **trích dẫn nguồn `[S1]`, liên kết canonical và đo lường thời gian thực**.

---

## 🎯 Tính năng nổi bật

1. **Truy xuất ngữ nghĩa chính xác**:
   - Sử dụng mô hình nhúng `BAAI/bge-small-en-v1.5` cùng cơ sở dữ liệu vector ChromaDB (1,591 chunks).
   - Đo lường Retrieval Recall@5 đạt **85.67%**, Hit Rate@5 đạt **92.00%**.
2. **Sinh câu trả lời tin cậy (Local LLM qua Ollama)**:
   - Mô hình cục bộ `gemma2:2b` chạy offline, đảm bảo quyền riêng tư và tốc độ phản hồi cao (~1.0s).
   - Tuân thủ quy tắc nghiêm ngặt: không bịa đặt API, chỉ trả lời dựa trên context, từ chối câu hỏi ngoài phạm vi.
   - Trích dẫn nguồn `[S1]`, `[S2]` và tự động xác thực chống ảo giác trích dẫn (`hallucinated citations`).
3. **Backend FastAPI chuẩn REST**:
   - `POST /chat`: Nhận câu hỏi, trả lời, danh sách nguồn trích dẫn và số liệu latency chi tiết.
   - `GET /health`: Giám sát sức khỏe kết nối của ChromaDB và Ollama.
4. **Giao diện người dùng Streamlit**:
   - Khung chat trực quan, hiển thị câu trả lời với định dạng markdown và cú pháp code rõ ràng.
   - Hiển thị badge thời gian phản hồi: *⚡ Retrieval Latency*, *🤖 Generation Latency*, *⏱️ Total Latency*.
   - Khối mở rộng (*Expander*) cho phép kiểm tra chi tiết các chunk đã truy xuất từ ChromaDB.
5. **Đóng gói toàn diện với Docker Compose**:
   - Tách biệt rõ ràng container Backend FastAPI (`port 8000`) và Frontend Streamlit (`port 8501`).

---

## 📁 Cấu trúc Thư mục

```text
devdocs-rag/
├── api/                       # Backend FastAPI (main.py, schemas.py)
├── data/
│   ├── raw/                   # Tài liệu markdown thô
│   ├── processed/             # corpus.jsonl và thư mục lưu trữ ChromaDB
│   └── evaluation/            # benchmark_queries.json, kết quả CSV & JSON
├── frontend/                  # Giao diện Streamlit (app.py)
├── generation/                # RAG prompts, Ollama generator, citation validator
├── ingestion/                 # Bộ parser, LangChain chunking và xuất corpus JSONL
├── retrieval/                 # ChromaDB indexer và công cụ tìm kiếm ngữ nghĩa
├── tests/                     # Toàn bộ bộ kiểm thử tự động (pytest)
├── Dockerfile.api             # Dockerfile cho backend FastAPI
├── Dockerfile.frontend        # Dockerfile cho frontend Streamlit
├── docker-compose.yml         # Cấu hình đa dịch vụ Docker Compose
├── requirements.txt           # Danh sách thư viện phụ thuộc
├── LOG.md                     # Nhật ký kỹ thuật chi tiết qua 7 giai đoạn
└── README.md
```

---

## 🛠️ Hướng dẫn Cài đặt & Khởi chạy Cục bộ

> [!NOTE]
> Nhằm giữ cho kho lưu trữ Git gọn nhẹ, **trọng số mô hình (LLM model weights)** và **cơ sở dữ liệu vector ChromaDB** không được lưu trong Git repository. Hãy làm theo các bước dưới đây để tải và khởi tạo chúng.

### 1. Chuẩn bị môi trường Python & Cài đặt Thư viện
```bash
# Khởi tạo virtual environment
python -m venv .venv

# Kích hoạt trên Windows:
.\.venv\Scripts\Activate.ps1
# Kích hoạt trên Linux / macOS:
source .venv/bin/activate

# Cài đặt các thư viện cần thiết
pip install -r requirements.txt
```

### 2. Cài đặt Ollama và Tải Mô hình LLM
1. Tải và cài đặt Ollama từ [https://ollama.com](https://ollama.com).
2. Mở terminal và tải mô hình:
   ```bash
   ollama run gemma2:2b
   ```
3. Đảm bảo dịch vụ Ollama đang hoạt động tại `http://localhost:11434`.

### 3. Thu thập Dữ liệu & Khởi tạo Vector Database
```bash
# Bước 1: Tải tài liệu tiếng Anh chính thức từ repo FastAPI
python -m ingestion.fetch_docs

# Bước 2: Phân đoạn (Chunking) bằng LangChain và xuất corpus.jsonl
python -m ingestion.chunk_docs

# Bước 3: Tạo vector embeddings và lập chỉ mục ChromaDB
python -m retrieval.indexer
```

### 4. Khởi chạy Ứng dụng Cục bộ

#### Khởi chạy Backend FastAPI:
```bash
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```
- API Documentation (Swagger UI): `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

#### Khởi chạy Frontend Streamlit:
```bash
python -m streamlit run frontend/app.py --server.port 8501
```
- Mở trình duyệt tại: `http://localhost:8501`

---

## 🐳 Khởi chạy bằng Docker Compose

Hệ thống cung cấp sẵn `docker-compose.yml` để đóng gói backend và frontend thành các container độc lập:

```bash
docker compose up --build -d
```

- **Frontend Streamlit**: `http://localhost:8501`
- **Backend FastAPI**: `http://localhost:8000`
- **Swagger Documentation**: `http://localhost:8000/docs`

> [!TIP]
> Khi chạy trong container, Backend được cấu hình tự động trỏ tới Ollama trên máy host thông qua `host.docker.internal:11434`.

Để dừng các dịch vụ:
```bash
docker compose down
```

---

## 📊 Đánh giá Benchmark & Kiểm thử

### 1. Chạy Đánh giá Retrieval Baseline:
```bash
python -m evaluation.evaluate_retrieval
```

### 2. Chạy Đánh giá End-to-End RAG (với Ablation Study so sánh No-RAG):
```bash
python -m evaluation.evaluate_e2e
```
Kết quả được tự động ghi nhận vào [rag_e2e_results.json](file:///c:/Users/2/Desktop/WORKSPACE/RAG/data/evaluation/rag_e2e_results.json) và [rag_e2e_results.csv](file:///c:/Users/2/Desktop/WORKSPACE/RAG/data/evaluation/rag_e2e_results.csv).

### 3. Chạy Toàn bộ Bộ Kiểm thử Tự động (Unit Tests):
```bash
pytest tests/ -v
```
*(Hiện có 15 bài kiểm tra tự động bao phủ ingestion, retrieval, generation và API endpoints).*
