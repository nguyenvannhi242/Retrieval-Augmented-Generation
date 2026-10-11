# Development Log - devdocs-rag

Nhật ký ghi lại quá trình thiết kế, triển khai, kiểm thử và tối ưu hóa hệ thống DevDocs RAG Chatbot.

---

## 📌 Phase 1: Khởi tạo dự án & Chuẩn hóa cấu trúc

- **Thời gian**: 2026-10-12
- **Mục tiêu**:
  - Khởi tạo Git repository và cấu trúc thư mục chuẩn theo yêu cầu dự án.
  - Thiết lập môi trường Python ảo và danh sách dependencies trong `requirements.txt`.
  - Cấu hình `.gitignore` và license MIT.
- **Kết quả**:
  - Đã khởi tạo git và các thư mục: `data/`, `ingestion/`, `retrieval/`, `generation/`, `evaluation/`, `api/`, `frontend/`, `tests/`.
  - Khởi tạo virtual environment `.venv` và cài đặt các thư viện lõi (FastAPI, Streamlit, ChromaDB, Sentence-Transformers, LangChain, Ollama).

---

## 📌 Phase 2: Ingestion & Chuẩn hóa Corpus (FastAPI Documentation)

- **Trạng thái**: Hoàn thành (DONE)
- **Thời gian**: 2026-10-12
- **Thực hiện**:
  - Clone tài liệu chính thức từ repository gốc `fastapi/fastapi` (docs/en/docs).
  - Lọc bỏ các tệp tin meta/nhiễu không liên quan đến kỹ thuật (release notes, changelogs, translations progress, banners) để bảo đảm mật độ thông tin kỹ thuật cao nhất.
  - Tổng số tệp tài liệu kỹ thuật chuẩn hóa: **149 tài liệu Markdown**.
  - Pipeline chuẩn hóa: Trích xuất tiêu đề cấp cao, loại bỏ bình luận/badge/thẻ HTML, bóc tách anchor chính xác của MkDocs `{ #anchor-slug }`.
  - Phân đoạn thông minh bằng LangChain:
    - `MarkdownHeaderTextSplitter` theo cấp bậc `#`, `##`, `###`.
    - `RecursiveCharacterTextSplitter` với `chunk_size=750`, `chunk_overlap=100`.
  - Tạo corpus chuẩn hóa tại `data/processed/corpus.jsonl` gồm **1,591 chunks**, chiều dài trung bình **480.4 ký tự** (~120 tokens).
  - Đảm bảo đầy đủ 100% metadata bắt buộc cho từng chunk:
    - `chunk_id`: ID duy nhất theo đường dẫn và chỉ số (ví dụ: `fastapi_tutorial_query-params_1`).
    - `text`: Nội dung trích đoạn Markdown chuẩn hóa.
    - `source`: Đường dẫn file gốc tương đối (ví dụ: `fastapi/docs/en/docs/tutorial/query-params.md`).
    - `title`: Tiêu đề tài liệu và tên section.
    - `url`: Liên kết trực tiếp tới trang tài liệu chính thức kèm anchor (ví dụ: `https://fastapi.tiangolo.com/tutorial/query-params/#query-parameters`).
    - `license`: `MIT License (Sebastián Ramírez)`.

---

## 📌 Phase 3: Vector Database Indexing & Semantic Search (ChromaDB + BGE-small)

- **Trạng thái**: Hoàn thành (DONE)
- **Thời gian**: 2026-10-12
- **Thực hiện**:
  - Sử dụng mô hình nhúng `BAAI/bge-small-en-v1.5` qua `sentence-transformers` (kích thước embedding 384 chiều, khoảng cách cosine).
  - Lập chỉ mục toàn bộ 1,591 chunks vào cơ sở dữ liệu vector ChromaDB (`data/processed/chroma_db/`), collection `fastapi_docs`.
  - Xây dựng module và CLI `retrieval/search.py` hỗ trợ truy vấn song ngữ (Việt - Anh), tự động gắn query prefix tối ưu cho BGE (`Represent this sentence for searching relevant passages: `).
  - Trả về top-5 đoạn trích phù hợp nhất kèm điểm tương đồng, đường dẫn nguồn và canonical URL chính thức.
- **Kết quả thực nghiệm**:
  - **Query 1**: *"Làm thế nào để khai báo query parameters trong FastAPI?"* -> Trả về chính xác các mục trong `tutorial/query-params-str-validations.md`, `tutorial/query-param-models.md`, `reference/parameters.md` (Top score: ~0.69).
  - **Query 2**: *"Làm thế nào để chạy ứng dụng FastAPI trong Docker container?"* -> Trả về chính xác các mục trong `deployment/docker.md` và `deployment/concepts.md` (Top score: ~0.69).
  - **Query 3**: *"Làm sao để cấu hình background tasks trong FastAPI?"* -> Trả về chính xác `tutorial/background-tasks.md` và `reference/background.md` (Top score: ~0.68).
  - Tốc độ truy vấn: Dưới 150ms sau khi tải mô hình.
