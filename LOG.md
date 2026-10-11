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

---

## 📌 Phase 4: Xây dựng Bộ Benchmark & Đo lường Baseline Retrieval

- **Trạng thái**: Hoàn thành (DONE)
- **Thời gian**: 2026-10-12
- **Thực hiện**:
  - Xây dựng bộ ground truth benchmark `data/evaluation/benchmark_queries.json` gồm **60 câu hỏi** đa dạng:
    - 10 câu tra cứu khái niệm & API (factual/conceptual, English).
    - 15 câu quy trình & ví dụ code (procedural, English).
    - 5 câu kết hợp nhiều tài liệu (multi_source, English).
    - 20 câu cross-lingual (tiếng Việt truy vấn corpus tiếng Anh).
    - 10 câu unanswerable / out-of-scope (câu hỏi ngoài phạm vi như Django ORM, React Redux, Spring Boot, Solidity).
  - Xây dựng pipeline đo lường `evaluation/evaluate_retrieval.py` tính toán các metric ở cấp **Source file**:
    - **Recall@5**: Tỷ lệ các nguồn tài liệu liên quan xuất hiện trong top 5.
    - **MRR@5**: Điểm trung bình nghịch đảo thứ hạng của nguồn đúng đầu tiên ($1/r$ với $r \le 5$).
    - **Hit Rate@5**: Xác suất có ít nhất 1 nguồn tài liệu chính xác trong top 5.
    - **Latency**: Đo lường thời gian truy xuất (mean, median, p95).
    - Tách riêng phân tích giữa tiếng Anh và tiếng Việt, cùng phân tích điểm tương đồng trên câu hỏi out-of-domain.
  - Xuất báo cáo baseline chi tiết tại `data/evaluation/retrieval_baseline.json`.
- **Kết quả Baseline đo lường (`BAAI/bge-small-en-v1.5`)**:
  - **Overall (50 câu hỏi answerable)**:
    - Recall@5: **85.67%**
    - MRR@5: **0.7890**
    - Hit Rate@5: **92.00%**
    - Median Latency: **16.1 ms** (Mean: **16.4 ms**)
  - **Tách theo ngôn ngữ**:
    - **English (n=30)**: Recall@5 = **89.44%**, MRR@5 = **0.8844**, Hit Rate@5 = **96.67%**, Median Latency = **15.6 ms**
    - **Vietnamese Cross-lingual (n=20)**: Recall@5 = **80.00%**, MRR@5 = **0.6458**, Hit Rate@5 = **85.00%**, Median Latency = **16.9 ms**
  - **Phân tích quan trọng**:
    - Khi truy vấn bằng tiếng Việt trên mô hình nhúng đơn ngữ tiếng Anh (`bge-small-en-v1.5`), MRR@5 sụt giảm rõ rệt từ 0.884 xuống 0.646 (-23.9 điểm) và Hit Rate giảm từ 96.7% xuống 85.0%.
    - Các câu hỏi ngoài phạm vi (unanswerable) vẫn có điểm tương đồng cosine trung bình lên tới 0.6419 (cao nhất 0.7047), chứng minh rằng điểm similarity cao không đồng nghĩa với câu trả lời đúng, và cần có cơ chế lọc ngưỡng hoặc phân loại truy vấn.

---

## 📌 Phase 5: Tích hợp Local LLM qua Ollama (Gemma 2 2B) & Xác thực Trích dẫn Nguồn

- **Trạng thái**: Hoàn thành (DONE)
- **Thời gian**: 2026-10-12
- **Thực hiện**:
  - Tải và cấu hình mô hình local qua Ollama: `gemma2:2b` (~1.6 GB).
  - Xây dựng module `generation/prompts.py` định nghĩa `SYSTEM_PROMPT` với 6 nguyên tắc kỹ thuật nghiêm ngặt (chỉ dùng ngữ cảnh cung cấp, không bịa đặt API, trích dẫn nguồn `[S1]`, trả lời đúng ngôn ngữ câu hỏi).
  - Xây dựng module `generation/generator.py`:
    - Định dạng ngữ cảnh từ top 5 chunks theo cấu trúc `[S{i}]` kèm Tiêu đề, URL và nội dung.
    - Kết nối `ollama.chat` thực hiện sinh câu trả lời.
    - Bộ bóc tách và xác thực trích dẫn (`validate_citations`): Quét toàn bộ thẻ `[S{i}]` trong câu trả lời, ánh xạ sang thông tin metadata thực tế của chunk tương ứng (tiêu đề, URL canonical, file nguồn, score), phát hiện và cảnh báo các trích dẫn bịa đặt (`hallucinated_citations`).
    - Lớp `RAGPipeline` liên kết trực tiếp với `DocumentRetriever` từ `retrieval/search.py` để thực hiện toàn bộ luồng RAG đầu cuối.
  - Viết bộ unit test `tests/test_generation.py` (5 tests) kiểm tra prompt rules, context builder, citation validator, và xử lý khi không có chunks.
- **Kết quả thực nghiệm**:
  - Thử nghiệm câu hỏi tiếng Việt: *"Làm thế nào để khai báo query parameters trong FastAPI?"* -> Trả lời bằng tiếng Việt chính xác, trích dẫn chuẩn xác `[S2]`, `[S3]`, `[S5]` tương ứng với `tutorial/query-param-models.md`, `reference/parameters.md`, `tutorial/body.md`.
  - Thử nghiệm câu hỏi: *"Làm thế nào để chạy ứng dụng FastAPI trong Docker container?"* -> Trả lời ngắn gọn, chuẩn xác kèm trích dẫn `[S4]` tới `deployment/docker.md#build-the-docker-image`.
