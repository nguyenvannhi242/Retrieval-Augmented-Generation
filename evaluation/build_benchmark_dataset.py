"""Script to generate, enrich, and validate the 60 benchmark evaluation dataset."""

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
        "reference_answer": "Concurrency involves switching between multiple waiting tasks (e.g. I/O operations like network or DB calls with async/await). Parallelism means executing computations simultaneously across multiple CPU cores or threads.",
        "answerable": True,
    },
    {
        "query_id": "q002",
        "question": "How do standard Python type hints help FastAPI generate OpenAPI schemas and validation?",
        "language": "en",
        "category": "factual",
        "relevant_sources": ["fastapi/docs/en/docs/python-types.md"],
        "reference_answer": "FastAPI uses standard Python type hints with Pydantic to parse and validate incoming data, convert types automatically, provide editor autocomplete and error checks, and automatically generate interactive OpenAPI documentation.",
        "answerable": True,
    },
    {
        "query_id": "q003",
        "question": "What does the response_model parameter in path operations do?",
        "language": "en",
        "category": "factual",
        "relevant_sources": ["fastapi/docs/en/docs/tutorial/response-model.md"],
        "reference_answer": "The response_model parameter defines the output data schema, validates outgoing data, filters out private or sensitive fields (e.g. passwords), and formats the output schema in OpenAPI docs.",
        "answerable": True,
    },
    {
        "query_id": "q004",
        "question": "What is OAuth2PasswordBearer in FastAPI security?",
        "language": "en",
        "category": "factual",
        "relevant_sources": ["fastapi/docs/en/docs/tutorial/security/first-steps.md"],
        "reference_answer": "OAuth2PasswordBearer is a security utility class declaring the OAuth2 password flow with Bearer tokens. It specifies the tokenUrl endpoint where clients obtain tokens and extracts Bearer tokens from the HTTP Authorization header.",
        "answerable": True,
    },
    {
        "query_id": "q005",
        "question": "What is the role of BackgroundTasks in FastAPI responses?",
        "language": "en",
        "category": "factual",
        "relevant_sources": ["fastapi/docs/en/docs/tutorial/background-tasks.md"],
        "reference_answer": "BackgroundTasks allows scheduling functions to execute in the background after the HTTP response has been sent to the client, preventing slow operations (like email sending or logging) from blocking the response.",
        "answerable": True,
    },
    {
        "query_id": "q006",
        "question": "How does FastAPI handle dependency injection using Depends?",
        "language": "en",
        "category": "factual",
        "relevant_sources": ["fastapi/docs/en/docs/tutorial/dependencies/index.md"],
        "reference_answer": "FastAPI handles dependency injection using Depends(func), executing the callable or class dependency, passing its return value into endpoint parameters, and resolving nested sub-dependencies automatically.",
        "answerable": True,
    },
    {
        "query_id": "q007",
        "question": "What is CORSMiddleware and why is it needed for frontend clients?",
        "language": "en",
        "category": "factual",
        "relevant_sources": ["fastapi/docs/en/docs/tutorial/cors.md"],
        "reference_answer": "CORSMiddleware configures Cross-Origin Resource Sharing headers (such as allow_origins, allow_methods, and allow_headers) so web browsers permit frontend applications on a different origin/domain to communicate with the API.",
        "answerable": True,
    },
    {
        "query_id": "q008",
        "question": "What is the difference between UploadFile and bytes when receiving uploaded files?",
        "language": "en",
        "category": "factual",
        "relevant_sources": ["fastapi/docs/en/docs/tutorial/request-files.md"],
        "reference_answer": "Using bytes loads the entire file into memory at once, suitable only for small files. UploadFile stores files as a SpooledTemporaryFile that rolls over to disk, saving memory and providing file-like methods (read, write, seek).",
        "answerable": True,
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
        "reference_answer": "APIRouter groups related path operations into separate modules or files (such as items or users), allowing large codebases to be cleanly organized and mounted into the main app via app.include_router().",
        "answerable": True,
    },
    {
        "query_id": "q010",
        "question": "What is the default status code returned by FastAPI endpoints and how to customize it?",
        "language": "en",
        "category": "factual",
        "relevant_sources": ["fastapi/docs/en/docs/tutorial/response-status-code.md"],
        "reference_answer": "The default HTTP status code is 200 OK. It can be customized in the path operation decorator using the status_code parameter (e.g. status_code=201 or status_code=status.HTTP_201_CREATED).",
        "answerable": True,
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
        "reference_answer": "Declare function arguments that are not part of the route path and assign default values, for example `def read_items(skip: int = 0, limit: int = 10):`. These default values make them optional query parameters.",
        "answerable": True,
    },
    {
        "query_id": "q012",
        "question": "How to validate string length and regular expressions in Query parameters?",
        "language": "en",
        "category": "procedural",
        "relevant_sources": ["fastapi/docs/en/docs/tutorial/query-params-str-validations.md"],
        "reference_answer": "Import Query from fastapi and use it with Annotated: `q: Annotated[str | None, Query(min_length=3, max_length=50, pattern=r'^[a-zA-Z0-9]+$')] = None`.",
        "answerable": True,
    },
    {
        "query_id": "q013",
        "question": "How can I run a FastAPI application in a Docker container?",
        "language": "en",
        "category": "procedural",
        "relevant_sources": ["fastapi/docs/en/docs/deployment/docker.md"],
        "reference_answer": "Create a Dockerfile from an official Python image, install dependencies from requirements.txt, copy your code, and run `fastapi run app/main.py --port 80`. Then build with `docker build -t myimage .` and run with `docker run -d -p 80:80 myimage`.",
        "answerable": True,
    },
    {
        "query_id": "q014",
        "question": "How to raise an HTTPException with custom status code and detail message?",
        "language": "en",
        "category": "procedural",
        "relevant_sources": ["fastapi/docs/en/docs/tutorial/handling-errors.md"],
        "reference_answer": "Import HTTPException from fastapi and raise it: `raise HTTPException(status_code=404, detail='Item not found')`.",
        "answerable": True,
    },
    {
        "query_id": "q015",
        "question": "How to schedule background tasks using BackgroundTasks.add_task in a path operation?",
        "language": "en",
        "category": "procedural",
        "relevant_sources": ["fastapi/docs/en/docs/tutorial/background-tasks.md"],
        "reference_answer": "Declare a `background_tasks: BackgroundTasks` parameter in your endpoint and call `background_tasks.add_task(task_function, *args)` inside the function body.",
        "answerable": True,
    },
    {
        "query_id": "q016",
        "question": "How to mount static files in FastAPI using StaticFiles?",
        "language": "en",
        "category": "procedural",
        "relevant_sources": ["fastapi/docs/en/docs/tutorial/static-files.md"],
        "reference_answer": "Import StaticFiles from fastapi.staticfiles and call `app.mount('/static', StaticFiles(directory='static'), name='static')`.",
        "answerable": True,
    },
    {
        "query_id": "q017",
        "question": "How to implement JWT authentication and generate bearer tokens in FastAPI?",
        "language": "en",
        "category": "procedural",
        "relevant_sources": ["fastapi/docs/en/docs/tutorial/security/oauth2-jwt.md"],
        "reference_answer": "Authenticate user credentials with OAuth2PasswordRequestForm, create a JWT token with PyJWT containing expiry and user claims, and return `{'access_token': token, 'token_type': 'bearer'}`.",
        "answerable": True,
    },
    {
        "query_id": "q018",
        "question": "How to write tests for FastAPI endpoints using TestClient and pytest?",
        "language": "en",
        "category": "procedural",
        "relevant_sources": ["fastapi/docs/en/docs/tutorial/testing.md"],
        "reference_answer": "Import TestClient from fastapi.testclient, instantiate `client = TestClient(app)`, and send test requests like `response = client.get('/')` asserting `assert response.status_code == 200`.",
        "answerable": True,
    },
    {
        "query_id": "q019",
        "question": "How to use dependencies with yield to manage database sessions or cleanup?",
        "language": "en",
        "category": "procedural",
        "relevant_sources": ["fastapi/docs/en/docs/tutorial/dependencies/dependencies-with-yield.md"],
        "reference_answer": "Define a dependency function that yields the database session inside a try block and closes it in a finally block: `def get_db(): db = SessionLocal(); try: yield db; finally: db.close()`.",
        "answerable": True,
    },
    {
        "query_id": "q020",
        "question": "How to handle WebSockets connections for real-time messaging in FastAPI?",
        "language": "en",
        "category": "procedural",
        "relevant_sources": ["fastapi/docs/en/docs/advanced/websockets.md"],
        "reference_answer": "Define a websocket endpoint `@app.websocket('/ws') async def ws_endpoint(websocket: WebSocket):`, call `await websocket.accept()`, and receive/send messages in a loop using `await websocket.receive_text()` and `await websocket.send_text()`.",
        "answerable": True,
    },
    {
        "query_id": "q021",
        "question": "How to declare request headers parameters using Header in FastAPI?",
        "language": "en",
        "category": "procedural",
        "relevant_sources": ["fastapi/docs/en/docs/tutorial/header-params.md"],
        "reference_answer": "Import Header from fastapi and declare the parameter: `user_agent: Annotated[str | None, Header()] = None`. Hyphens in header names are converted to underscores.",
        "answerable": True,
    },
    {
        "query_id": "q022",
        "question": "How to declare cookie parameters using Cookie in path operation functions?",
        "language": "en",
        "category": "procedural",
        "relevant_sources": ["fastapi/docs/en/docs/tutorial/cookie-params.md"],
        "reference_answer": "Import Cookie from fastapi and declare the parameter: `ads_id: Annotated[str | None, Cookie()] = None`.",
        "answerable": True,
    },
    {
        "query_id": "q023",
        "question": "How to read and parse form data using Form in FastAPI endpoints?",
        "language": "en",
        "category": "procedural",
        "relevant_sources": ["fastapi/docs/en/docs/tutorial/request-forms.md"],
        "reference_answer": "Import Form from fastapi and declare parameters: `username: Annotated[str, Form()], password: Annotated[str, Form()]`. This receives x-www-form-urlencoded data.",
        "answerable": True,
    },
    {
        "query_id": "q024",
        "question": "How to configure application settings and environment variables with pydantic-settings?",
        "language": "en",
        "category": "procedural",
        "relevant_sources": ["fastapi/docs/en/docs/advanced/settings.md"],
        "reference_answer": "Subclass BaseSettings from pydantic_settings, define typed fields, specify SettingsConfigDict(env_file='.env'), and access settings via a cached dependency.",
        "answerable": True,
    },
    {
        "query_id": "q025",
        "question": "How to mount sub-applications in FastAPI using app.mount?",
        "language": "en",
        "category": "procedural",
        "relevant_sources": ["fastapi/docs/en/docs/advanced/sub-applications.md"],
        "reference_answer": "Create a sub-application instance `subapp = FastAPI()` and mount it onto the main app: `app.mount('/subapi', subapp)`.",
        "answerable": True,
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
        "reference_answer": "FastAPI distinguishes them automatically: parameters declared in the path route are path parameters; parameters typed as Pydantic models are request body; and singular scalar types (e.g. str, int) not in the path are query parameters.",
        "answerable": True,
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
        "reference_answer": "Declare File() (or UploadFile) and Form() parameters together in the same endpoint function signature, receiving data encoded as multipart/form-data.",
        "answerable": True,
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
        "reference_answer": "Create APIRouter instances in dedicated sub-modules (e.g. users.py, items.py) with prefixes and tags, then include them in the root application using `app.include_router(users.router)`.",
        "answerable": True,
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
        "reference_answer": "Build a Linux container image from official Python base. For container clusters (Kubernetes), run one Uvicorn process per container. For single-server deployments, configure multiple worker processes (e.g. `uvicorn main:app --workers 4`).",
        "answerable": True,
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
        "reference_answer": "Create a `get_current_user` dependency that takes `token: Annotated[str, Depends(oauth2_scheme)]`, decodes and validates the token, retrieves the user from the database, and inject it using `current_user: Annotated[User, Depends(get_current_active_user)]`.",
        "answerable": True,
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
        "reference_answer": "Khai báo các tham số trong hàm endpoint không trùng với đường dẫn path. Gán giá trị mặc định để biến thành tham số tùy chọn (optional), ví dụ: `skip: int = 0, limit: int = 10`.",
        "answerable": True,
    },
    {
        "query_id": "q032",
        "question": "Cách kiểm tra độ dài chuỗi và biểu thức chính quy regex cho query parameter?",
        "language": "vi",
        "category": "cross_lingual",
        "relevant_sources": ["fastapi/docs/en/docs/tutorial/query-params-str-validations.md"],
        "reference_answer": "Sử dụng hàm Query() kèm Annotated từ fastapi: `q: Annotated[str | None, Query(min_length=3, max_length=50, pattern=r'^[a-zA-Z0-9_]+$')] = None`.",
        "answerable": True,
    },
    {
        "query_id": "q033",
        "question": "Làm thế nào để đóng gói và triển khai ứng dụng FastAPI trong Docker container?",
        "language": "vi",
        "category": "cross_lingual",
        "relevant_sources": ["fastapi/docs/en/docs/deployment/docker.md"],
        "reference_answer": "Tạo Dockerfile từ Python base image (python:3.11), cài đặt requirements.txt, copy mã nguồn và chạy lệnh `fastapi run app/main.py --port 80` hoặc `uvicorn app.main:app --host 0.0.0.0 --port 80`. Sau đó build và run container.",
        "answerable": True,
    },
    {
        "query_id": "q034",
        "question": "Cách tạo background tasks để xử lý tác vụ ngầm sau khi trả về response?",
        "language": "vi",
        "category": "cross_lingual",
        "relevant_sources": ["fastapi/docs/en/docs/tutorial/background-tasks.md"],
        "reference_answer": "Khai báo tham số kiểu `BackgroundTasks` trong hàm endpoint và gọi `background_tasks.add_task(task_func, *args)` để thực thi hàm ngầm sau khi response được gửi đi.",
        "answerable": True,
    },
    {
        "query_id": "q035",
        "question": "Làm sao để cấu hình CORSMiddleware cho phép frontend React hoặc Vue gọi API?",
        "language": "vi",
        "category": "cross_lingual",
        "relevant_sources": ["fastapi/docs/en/docs/tutorial/cors.md"],
        "reference_answer": "Sử dụng `app.add_middleware(CORSMiddleware, allow_origins=['http://localhost:3000'], allow_credentials=True, allow_methods=['*'], allow_headers=['*'])`.",
        "answerable": True,
    },
    {
        "query_id": "q036",
        "question": "Cách ném ngoại lệ HTTPException kèm theo status code và nội dung lỗi?",
        "language": "vi",
        "category": "cross_lingual",
        "relevant_sources": ["fastapi/docs/en/docs/tutorial/handling-errors.md"],
        "reference_answer": "Import HTTPException từ fastapi và ném lỗi bằng: `raise HTTPException(status_code=404, detail='Item not found')`.",
        "answerable": True,
    },
    {
        "query_id": "q037",
        "question": "Làm thế nào để sử dụng cơ chế Dependency Injection với Depends trong FastAPI?",
        "language": "vi",
        "category": "cross_lingual",
        "relevant_sources": ["fastapi/docs/en/docs/tutorial/dependencies/index.md"],
        "reference_answer": "Định nghĩa một hàm dependency và khai báo trong endpoint bằng `Depends(dependency_func)` (ví dụ: `commons: Annotated[dict, Depends(common_parameters)]`).",
        "answerable": True,
    },
    {
        "query_id": "q038",
        "question": "Cách upload file đơn hoặc danh sách nhiều file bằng UploadFile?",
        "language": "vi",
        "category": "cross_lingual",
        "relevant_sources": ["fastapi/docs/en/docs/tutorial/request-files.md"],
        "reference_answer": "Khai báo `file: UploadFile = File(...)` cho file đơn hoặc `files: list[UploadFile] = File(...)` cho nhiều file. UploadFile đọc ghi theo stream tạm, tránh quá tải RAM.",
        "answerable": True,
    },
    {
        "query_id": "q039",
        "question": "Làm thế nào để cấu hình static files bằng StaticFiles trong FastAPI?",
        "language": "vi",
        "category": "cross_lingual",
        "relevant_sources": ["fastapi/docs/en/docs/tutorial/static-files.md"],
        "reference_answer": "Import StaticFiles từ `fastapi.staticfiles` và gắn vào ứng dụng bằng `app.mount('/static', StaticFiles(directory='static'), name='static')`.",
        "answerable": True,
    },
    {
        "query_id": "q040",
        "question": "Cách tạo và xác thực token JWT với OAuth2 trong FastAPI?",
        "language": "vi",
        "category": "cross_lingual",
        "relevant_sources": ["fastapi/docs/en/docs/tutorial/security/oauth2-jwt.md"],
        "reference_answer": "Xác thực tài khoản qua OAuth2PasswordRequestForm, tạo token JWT chứa claims và thời gian hết hạn bằng `jwt.encode`, rồi trả về access_token kèm token_type='bearer'.",
        "answerable": True,
    },
    {
        "query_id": "q041",
        "question": "Cách viết kiểm thử tự động cho endpoint bằng TestClient và pytest?",
        "language": "vi",
        "category": "cross_lingual",
        "relevant_sources": ["fastapi/docs/en/docs/tutorial/testing.md"],
        "reference_answer": "Khởi tạo `client = TestClient(app)` từ `fastapi.testclient`, gọi `response = client.get('/items/')` và kiểm tra `assert response.status_code == 200`.",
        "answerable": True,
    },
    {
        "query_id": "q042",
        "question": "Làm sao để giải phóng tài nguyên cơ sở dữ liệu bằng dependency có chứa yield?",
        "language": "vi",
        "category": "cross_lingual",
        "relevant_sources": ["fastapi/docs/en/docs/tutorial/dependencies/dependencies-with-yield.md"],
        "reference_answer": "Tạo dependency chứa yield: phần trước yield khởi tạo database session, lệnh yield trả về session, phần trong finally sau yield thực thi đóng kết nối sau khi response hoàn tất.",
        "answerable": True,
    },
    {
        "query_id": "q043",
        "question": "Cách thiết lập giao tiếp WebSocket real-time hai chiều trong FastAPI?",
        "language": "vi",
        "category": "cross_lingual",
        "relevant_sources": ["fastapi/docs/en/docs/advanced/websockets.md"],
        "reference_answer": "Dùng decorator `@app.websocket('/ws')`, gọi `await websocket.accept()`, và dùng vòng lặp `while True` với `await websocket.receive_text()` và `await websocket.send_text()`.",
        "answerable": True,
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
        "reference_answer": "Tạo các router riêng trong từng file chức năng bằng `router = APIRouter(prefix='/users', tags=['users'])`, sau đó trong file chính gọi `app.include_router(users.router)`.",
        "answerable": True,
    },
    {
        "query_id": "q045",
        "question": "Khi nào nên dùng async def và khi nào dùng def thông thường trong FastAPI?",
        "language": "vi",
        "category": "cross_lingual",
        "relevant_sources": ["fastapi/docs/en/docs/async.md"],
        "reference_answer": "Dùng `async def` khi gọi các thư viện I/O hỗ trợ await (như httpx, asyncpg). Dùng `def` thông thường khi gọi các thư viện đồng bộ chặn (như requests, SQLAlchemy cũ); FastAPI sẽ tự động chạy hàm def trong threadpool riêng.",
        "answerable": True,
    },
    {
        "query_id": "q046",
        "question": "Làm sao để lọc dữ liệu trả về bằng cách định nghĩa response_model?",
        "language": "vi",
        "category": "cross_lingual",
        "relevant_sources": ["fastapi/docs/en/docs/tutorial/response-model.md"],
        "reference_answer": "Truyền model Pydantic vào decorator `@app.get('/items/', response_model=ItemOut)`. FastAPI tự động lọc bỏ các trường không có trong model này (như mật khẩu).",
        "answerable": True,
    },
    {
        "query_id": "q047",
        "question": "Cách nhận dữ liệu form thông qua Form thay vì JSON trong FastAPI?",
        "language": "vi",
        "category": "cross_lingual",
        "relevant_sources": ["fastapi/docs/en/docs/tutorial/request-forms.md"],
        "reference_answer": "Import `Form` từ `fastapi` và khai báo: `username: Annotated[str, Form()], password: Annotated[str, Form()]`. Cần cài đặt thêm thư viện `python-multipart`.",
        "answerable": True,
    },
    {
        "query_id": "q048",
        "question": "Cách đọc giá trị Cookie gửi từ trình duyệt bằng Cookie parameter?",
        "language": "vi",
        "category": "cross_lingual",
        "relevant_sources": ["fastapi/docs/en/docs/tutorial/cookie-params.md"],
        "reference_answer": "Import `Cookie` từ `fastapi` và khai báo tham số: `session_token: Annotated[str | None, Cookie()] = None`.",
        "answerable": True,
    },
    {
        "query_id": "q049",
        "question": "Làm thế nào để đọc custom HTTP Headers gửi lên từ client?",
        "language": "vi",
        "category": "cross_lingual",
        "relevant_sources": ["fastapi/docs/en/docs/tutorial/header-params.md"],
        "reference_answer": "Import `Header` từ `fastapi` và khai báo: `x_token: Annotated[str | None, Header()] = None`. FastAPI tự động chuyển đổi dấu gạch ngang thành gạch dưới.",
        "answerable": True,
    },
    {
        "query_id": "q050",
        "question": "Cách quản lý cấu hình và biến môi trường bằng BaseSettings trong FastAPI?",
        "language": "vi",
        "category": "cross_lingual",
        "relevant_sources": ["fastapi/docs/en/docs/advanced/settings.md"],
        "reference_answer": "Tạo class kế thừa `BaseSettings` từ `pydantic-settings`, định nghĩa các biến kèm kiểu dữ liệu và cấu hình `env_file='.env'`. Sau đó đưa vào endpoint qua dependency với `@lru_cache`.",
        "answerable": True,
    },

    # ── Category: Unanswerable / Out of Scope (Negatives) ──
    {
        "query_id": "q051",
        "question": "How do I configure Django ORM models with migrations and foreign keys?",
        "language": "en",
        "category": "unanswerable",
        "relevant_sources": [],
        "reference_answer": "The FastAPI documentation does not cover Django ORM or Django migrations, as FastAPI is a separate framework.",
        "answerable": False,
    },
    {
        "query_id": "q052",
        "question": "How to set up Apache Kafka consumer group with Spring Boot?",
        "language": "en",
        "category": "unanswerable",
        "relevant_sources": [],
        "reference_answer": "This topic is outside the FastAPI documentation scope. Spring Boot and Apache Kafka configurations are not documented here.",
        "answerable": False,
    },
    {
        "query_id": "q053",
        "question": "How to configure Ruby on Rails Active Record callbacks and validations?",
        "language": "en",
        "category": "unanswerable",
        "relevant_sources": [],
        "reference_answer": "Ruby on Rails Active Record is outside the FastAPI documentation scope.",
        "answerable": False,
    },
    {
        "query_id": "q054",
        "question": "How do I setup Angular route guards with RxJS observables?",
        "language": "en",
        "category": "unanswerable",
        "relevant_sources": [],
        "reference_answer": "Angular route guards and RxJS are outside the FastAPI documentation scope.",
        "answerable": False,
    },
    {
        "query_id": "q055",
        "question": "How do I configure CUDA drivers and PyTorch GPU memory pinning on Windows?",
        "language": "en",
        "category": "unanswerable",
        "relevant_sources": [],
        "reference_answer": "CUDA hardware drivers and PyTorch GPU pinning are not documented in the official FastAPI documentation.",
        "answerable": False,
    },
    {
        "query_id": "q056",
        "question": "Làm thế nào để cấu hình Redux Toolkit store và slice trong ứng dụng React frontend?",
        "language": "vi",
        "category": "unanswerable",
        "relevant_sources": [],
        "reference_answer": "Tài liệu FastAPI không hướng dẫn cấu hình Redux Toolkit hay React store.",
        "answerable": False,
    },
    {
        "query_id": "q057",
        "question": "Cách tạo Kubernetes StatefulSet với Persistent Volume Claim trong Helm chart?",
        "language": "vi",
        "category": "unanswerable",
        "relevant_sources": [],
        "reference_answer": "Tài liệu FastAPI không bao gồm hướng dẫn chi tiết về Kubernetes StatefulSet hoặc Helm charts.",
        "answerable": False,
    },
    {
        "query_id": "q058",
        "question": "Làm sao để viết smart contract Solidity bằng Hardhat và deploy lên Ethereum?",
        "language": "vi",
        "category": "unanswerable",
        "relevant_sources": [],
        "reference_answer": "Smart contract Solidity và Ethereum nằm ngoài phạm vi tài liệu FastAPI.",
        "answerable": False,
    },
    {
        "query_id": "q059",
        "question": "Cách cấu hình Nginx reverse proxy với PHP-FPM trên hệ điều hành Ubuntu?",
        "language": "vi",
        "category": "unanswerable",
        "relevant_sources": [],
        "reference_answer": "Cấu hình PHP-FPM với Nginx không thuộc tài liệu của FastAPI.",
        "answerable": False,
    },
    {
        "query_id": "q060",
        "question": "Làm thế nào để train model YOLOv8 nhận diện biển số xe bằng Ultralytics?",
        "language": "vi",
        "category": "unanswerable",
        "relevant_sources": [],
        "reference_answer": "Huấn luyện mô hình YOLOv8 thị giác máy tính không có trong tài liệu FastAPI.",
        "answerable": False,
    },
]


def generate_benchmark() -> None:
    """Validates and saves the enriched benchmark queries."""
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
    answerable_count = sum(1 for q in BENCHMARK_DATA if q["answerable"])
    unans_count = sum(1 for q in BENCHMARK_DATA if not q["answerable"])

    print("\nBenchmark Category Breakdown:")
    for cat in ["factual", "procedural", "multi_source", "cross_lingual", "unanswerable"]:
        cnt = sum(1 for q in BENCHMARK_DATA if q["category"] == cat)
        print(f" • {cat}: {cnt}")
    print(f"Language: EN={en_count}, VI={vi_count}")
    print(f"Answerable queries: {answerable_count}, Unanswerable: {unans_count}")


if __name__ == "__main__":
    generate_benchmark()
