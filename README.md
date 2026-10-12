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
*(Hiện có 19 bài kiểm tra tự động bao phủ ingestion, retrieval, generation và API endpoints).*

---

## 📈 Kết quả Đánh giá Thực nghiệm & Thí nghiệm Đối chứng

> [!IMPORTANT]
> **Headline Đánh giá Chất lượng Trả lời (Answer Quality Uplift)**:
> Trên tập câu hỏi kỹ thuật trong phạm vi (**Answerable $n=50$**):
> - **RAG Token F1**: **24.07%** vs **No-RAG Baseline**: **18.25%** $\rightarrow$ **Uplift: +5.81 điểm %**.
> - **Kiểm định Thống kê**: Paired t-test $t = 4.0874, p = 0.00016 < 0.001$; Wilcoxon signed-rank test $W = 235.0, p = 0.00019 < 0.001$.
> - **Bootstrap 95% Confidence Interval**: **[+3.03%, +8.52%]** (10,000 resamples).
> - *Lưu ý về con số +11.51 điểm % ở tập $n=60$*: Phần lớn mức chênh lệch tại $n=60$ đến từ việc RAG từ chối đúng trên 10 câu ngoài phạm vi (RAG F1 $\approx 40\%$ do khớp reference refusal vs No-RAG F1 $\approx 0\%$), không phản ánh việc trả lời kỹ thuật tốt hơn. Do đó, **+5.81 điểm % trên tập answerable** là con số đại diện chính xác nhất cho chất lượng trả lời.

---

### 1. Bảng Tổng hợp Tiến bộ Trước / Sau (Before vs After)

| Hạng mục Phân tích | Trạng thái Ban đầu (Before) | Cải tiến & Kiểm định Mới (After) | Ý nghĩa Kỹ thuật |
| :--- | :--- | :--- | :--- |
| **Số lượng Chunks** | Mâu thuẫn: Phase 2 ghi 1,591 nhưng Phase 8 ghi 3,002. | Chuẩn hóa **1,591 chunks** (khớp 100% Phase 2 và pipeline thực tế). | Loại bỏ tệp nhiễu `release-notes.md` và áp dụng đúng bộ lọc `min_chunk_length < 50`. |
| **Headline Chất lượng** | Báo cáo lẫn lộn "+11.51%" trên $n=60$ (bị chi phối bởi câu unanswerable). | Tách riêng: **+5.81 điểm %** trên Answerable ($n=50$); Refusal báo cáo độc lập. | Minh bạch đóng góp thực tế của việc cung cấp tài liệu kỹ thuật vs từ chối ngoài phạm vi. |
| **Kiểm định Thống kê** | Chỉ dùng Paired t-test. | Bổ sung **Wilcoxon signed-rank test** ($p = 0.00019$) và Bootstrap 95% CI. | Phù hợp với đặc tính phân phối Token F1 bị chặn trong $[0, 1]$ và không đối xứng. |
| **Định nghĩa Citation Acc** | 54% chưa làm rõ tiêu chí tính toán. | Định nghĩa rõ: $\ge 1$ trích dẫn đúng nguồn mục tiêu VÀ 0 thẻ ảo giác. | 27/50 câu đạt tiêu chuẩn; 11 câu 0 thẻ; 0 thẻ bịa đặt ngoài top-k (`[S6]`, `[S9]`). |
| **Top-k Ablation** | Chỉ đo Recall/Hit Rate lý thuyết. | Đo **End-to-End ($k \in \{3, 5, 8\}$)** gồm Recall, F1, Citation Precision & Latency. | Thực nghiệm chứng minh $k=8$ làm giảm mạnh Citation Precision (69.9% $\rightarrow$ 54.0%); $k=5$ là sweet spot. |
| **Chunk Size Ablation** | Chỉ đo đứt code, thiếu Recall. | Đo đầy đủ Recall@5 (84.7% vs 85.7% vs 89.7%) và tỷ lệ đứt code (9.5% vs 7.9% vs 5.1%). | Phân tích trade-off trung thực: 1200 có Recall cao hơn nhưng ngữ cảnh dày hơn. |
| **Embedding Comparison** | So sánh cosine similarity thô (0.64 vs 0.84). | Bổ sung **Bootstrap CI cho MRR** và phân tích **AUROC** (0.8740 vs 0.9547). | Xác nhận Multilingual E5 phân tách câu hỏi trong/ngoài phạm vi tốt hơn rõ rệt. |
| **Đánh giá Từ chối (Refusal)** | Đo trên 10 câu nhìn khi sửa prompt (dễ overfit). | Kiểm định trên **Held-out Test Set 20 câu mới** (90.0%) và đo **Over-refusal** (12.0%). | Đánh giá khách quan ranh giới an toàn thông tin và tính hữu ích. |
| **So sánh LLM Sinh** | Qwen 3B bị đo chậm gấp 28 lần trên CPU do cold load & swap RAM. | Đo profiling chuẩn trên **GPU RTX 5070**: cả hai mô hình đạt **~185 tokens/s**. | Gemma 2B được chọn vì tuân thủ trích dẫn cao hơn gấp đôi (66.0% vs 33.7%) và latency thấp hơn. |
| **Văn phong Khoa học** | Dùng từ khẳng định tuyệt đối ("triệt để", "dứt điểm"). | Chuyển sang văn phong học thuật chừng mực ("giảm đáng kể", "gợi ý rằng"). | Tăng tính thuyết phục và độ tin cậy trong thẩm định kỹ thuật. |

---

### 2. Bảng Tổng hợp Chỉ số Toàn diện (Metrics Summary)

| Nhóm Metric | Chỉ số Đo lường | RAG Pipeline | No-RAG Baseline | Quy cách Mẫu số & Ghi chú |
| :--- | :--- | :---: | :---: | :--- |
| **Retrieval** | Recall@5 | **85.67%** (BGE) / **88.33%** (E5) | — | Đo trên tập Answerable ($n=50$) |
| | Hit Rate@5 | **92.00%** (BGE) / **94.00%** (E5) | — | Đo trên tập Answerable ($n=50$) |
| | Vietnamese MRR@5 | **0.6458** (BGE) $\rightarrow$ **0.8000** (E5) | — | Cải thiện thứ hạng nguồn tiếng Việt ($n=20$) |
| | AUROC (Ans vs Unans) | **0.8740** (BGE) $\rightarrow$ **0.9547** (E5) | — | Khả năng phân tách câu trong vs ngoài phạm vi |
| **Refusal** | Held-out Refusal Rate | **90.0%** (18/20 câu) | 0.0% | Đo trên 20 câu unanswerable hoàn toàn mới |
| | Over-refusal Rate | **12.0%** (6/50 câu) | 0.0% | Đo trên 50 câu answerable (trade-off an toàn) |
| **Citations** | Precision | **69.93%** ($k=5$) / 46.90% (e2e baseline) | — | Tỷ lệ thẻ trích dẫn đúng nguồn mục tiêu |
| | Accuracy | **74.00%** ($k=5$) / 54.00% (e2e baseline) | — | Tỷ lệ câu có $\ge 1$ trích dẫn đúng & 0 thẻ ảo giác |
| | Hallucinated Tags ngoài Top-k | **0 thẻ** (100% nằm trong `[S1]-[S5]`) | — | Không có thẻ bịa như `[S6]`, `[S9]` |
| **Answer Quality**| **Answerable F1 (n=50)** | **24.07%** | **18.25%** | **Uplift: +5.81%** ($p = 0.00016 < 0.001$) |
| | English Answerable F1 ($n=30$)| **29.54%** | **20.83%** | **Uplift: +8.71%** |
| | Vietnamese Answerable F1 ($n=20$)| **15.86%** | **14.38%** | **Uplift: +1.48%** |
| **Latency & Speed**| Thông lượng Sinh (RTX 5070)| **185.0 tokens/s** (Gemma 2B) | — | Đo qua `eval_count` / `eval_duration` của Ollama |
| | Độ trễ Đầu cuối TB | **845.6 ms** ($k=5$ trên RTX 5070) | ~850 ms | Retrieval: ~18ms, Generation: ~827ms |

---

### 3. Chi tiết Thực nghiệm Mở rộng (Ablation Studies)

#### A. Thực nghiệm Top-k End-to-End ($k \in \{3, 5, 8\}$ trên RTX 5070):

| Top-k | Recall@k | Answer Correctness F1 | Citation Precision | Citation Accuracy | Ngữ cảnh TB | Latency Đầu Cuối |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **k = 3** | 81.67% | 23.31% | 66.67% | **76.00%** | ~1,462 chars (~365 tok) | **719.7 ms** |
| **k = 5 (Chọn)** | **85.67%** | **25.71%** | **69.93%** | **74.00%** | ~2,501 chars (~625 tok) | **845.6 ms** |
| **k = 8** | **91.00%** | 25.81% | **54.04%** | **66.00%** | ~3,937 chars (~984 tok) | **981.2 ms** |

*Nhận định*: Tăng lên $k=8$ giúp Recall tăng (+5.33%) nhưng F1 đi ngang (25.71% vs 25.81%), trong khi Citation Precision giảm mạnh từ 69.93% xuống 54.04% (-15.89 điểm %) do ngữ cảnh quá dài làm loãng sự chú ý của LLM 2B. Cấu hình $k=5$ là điểm cân bằng thực nghiệm tối ưu.

#### B. Thực nghiệm Phân đoạn Văn bản (Chunk Size: 400 vs 750 vs 1200):

| Cấu hình Chunk Size | Số Chunks | Độ dài TB (Chars) | Tỷ lệ Code Block bị đứt | Retrieval Recall@5 | Đánh giá Kỹ thuật |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **400 chars (overlap 60)** | 2,655 | 286.6 chars (~72 tok) | 9.45% | 84.67% | Phân mảnh, tỷ lệ đứt code cao nhất. |
| **750 chars (Selected)** | **1,591** | **480.4 chars (~120 tok)** | **7.86%** | **85.67%** | Cân bằng giữa bảo toàn section code và kích thước chunk. |
| **1200 chars (overlap 150)**| 1,259 | 605.0 chars (~151 tok) | **5.08%** | **89.67%** | Recall cao hơn, đứt code ít nhất, nhưng context dài. |

#### C. So sánh Mô hình Sinh trên GPU NVIDIA RTX 5070 (Gemma 2 2B vs Qwen 2.5 3B):

| Mô hình LLM | Tốc độ Sinh | Latency TB | Answer F1 ($n=50$) | English F1 | Vietnamese F1 | Citation Prec | Held-out Refusal |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Gemma 2 2B (Mặc định)** | **185.0 t/s** | **847.0 ms** | **24.66%** | **28.44%** | 18.98% | **66.00%** | **90.0%** |
| **Qwen 2.5 3B** | **183.7 t/s** | 1,802.6 ms | 17.94% | 15.90% | **21.01%** | 33.67% | **90.0%** |

*Nhận định*: Cả hai mô hình có thông lượng sinh tương đương (~184-185 tokens/s) trên RTX 5070. `gemma2:2b` vượt trội về khả năng tuân thủ trích dẫn và thời gian phản hồi, trong khi `qwen2.5:3b` thể hiện sự lưu loát hơn ở tiếng Việt (+2.03% F1).

---

### 4. Phân tích Giới hạn Kỹ thuật & Hướng Cải tiến (Limitations & Roadmap)

> [!WARNING]
> **Giới hạn 1: Đánh đổi giữa Refusal Rate và Over-refusal Rate**
> - *Hiện tượng*: Prompt guardrail siết chặt giúp Refusal Rate trên câu ngoài phạm vi đạt 90.0%, nhưng gây ra tỷ lệ từ chối nhầm 12.0% trên các câu hỏi khái niệm phức tạp trong phạm vi.
> - *Hướng giải quyết*: Bổ sung Few-shot Prompting với các ví dụ biên (edge cases) hoặc tách riêng bộ phân loại ý định (Intent Classifier) trước pipeline RAG.

> [!NOTE]
> **Giới hạn 2: Đánh giá bằng Token F1 trên truy vấn tiếng Việt**
> - *Hiện tượng*: Token F1 phạt nặng sự khác biệt từ ngữ đồng nghĩa và độ dài câu trả lời có code mẫu.
> - *Hướng giải quyết*: Triển khai **LLM-as-a-Judge** (GPT-4o / Claude 3.5 Sonnet) với rubric 4 tiêu chí (Correctness, Groundedness, Completeness, Hallucination) kết hợp đối soát Cohen's Kappa với Human Evaluation.

