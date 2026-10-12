"""Streamlit Frontend for FastAPI Documentation Assistant (RAG Chatbot)."""

from __future__ import annotations

import os
import sys
import time
from typing import Any, Dict, List, Optional
import requests
import streamlit as st

# Page configuration
st.set_page_config(
    page_title="FastAPI Docs AI Assistant",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Configuration & environment variables
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Custom CSS for rich aesthetics and premium styling
st.markdown(
    """
    <style>
    /* Global header style */
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(90deg, #009688, #00b4d8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #6c757d;
        margin-bottom: 1.5rem;
    }
    /* Metric pill badge */
    .metric-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.82rem;
        font-weight: 600;
        margin-right: 6px;
        margin-top: 4px;
        background-color: #f0f2f6;
        border: 1px solid #dcdfe6;
    }
    .badge-retrieval {
        color: #0d6efd;
        background-color: #e7f1ff;
        border-color: #b6d4fe;
    }
    .badge-gen {
        color: #198754;
        background-color: #e8f5e9;
        border-color: #c8e6c9;
    }
    .badge-total {
        color: #6f42c1;
        background-color: #f3e8fd;
        border-color: #d8b4fe;
    }
    /* Source chip */
    .source-chip {
        display: inline-block;
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 6px;
        padding: 4px 8px;
        margin: 4px 4px 4px 0;
        font-size: 0.85rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def check_backend_health() -> Dict[str, Any]:
    """Queries backend health check endpoint."""
    try:
        resp = requests.get(f"{BACKEND_URL}/health", timeout=3)
        if resp.status_code == 200:
            return resp.json()
        return {"status": "degraded", "code": resp.status_code}
    except Exception as e:
        return {"status": "offline", "error": str(e)}


def call_chat_api(question: str, top_k: int, model: Optional[str]) -> Optional[Dict[str, Any]]:
    """Sends question to backend /chat endpoint."""
    payload = {
        "question": question,
        "top_k": top_k,
    }
    if model:
        payload["model"] = model

    try:
        resp = requests.post(f"{BACKEND_URL}/chat", json=payload, timeout=120)
        if resp.status_code == 200:
            return resp.json()
        else:
            st.error(f"Backend returned error {resp.status_code}: {resp.text}")
            return None
    except Exception as e:
        st.error(f"Failed to connect to backend at {BACKEND_URL}: {e}")
        return None


# Sidebar
with st.sidebar:
    st.image(
        "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png",
        width=180,
    )
    st.markdown("### ⚙️ Cấu hình RAG")

    # Backend status check
    health_data = check_backend_health()
    if health_data.get("status") == "healthy":
        st.success("🟢 Backend: Sẵn sàng (Connected)")
        db_count = health_data.get("chroma_db", {}).get("details", {}).get("chunk_count", 0)
        st.caption(f"📚 Vector DB: **{db_count:,} chunks**")
    elif health_data.get("status") == "warning":
        st.warning("🟡 Backend: Hoạt động (LLM Warning)")
    else:
        st.error(f"🔴 Backend: Ngoại tuyến ({BACKEND_URL})")

    st.markdown("---")
    top_k_slider = st.slider(
        "Số lượng đoạn trích (Top-K Chunks):",
        min_value=1,
        max_value=10,
        value=5,
        step=1,
        help="Số lượng chunks tài liệu liên quan nhất được lấy ra từ ChromaDB làm ngữ cảnh.",
    )

    model_input = st.selectbox(
        "Mô hình LLM (Ollama):",
        options=["gemma2:2b", "gemma-4-E2B", "llama3.2:3b", "qwen2.5:3b"],
        index=0,
        help="Mô hình ngôn ngữ cục bộ chạy qua Ollama.",
    )

    st.markdown("---")
    st.markdown("### 💡 Câu hỏi gợi ý")
    sample_queries = [
        "Làm thế nào để khai báo query parameters trong FastAPI?",
        "Cách cấu hình Docker container cho FastAPI?",
        "How do standard Python type hints help FastAPI?",
        "How to use Dependency Injection with Depends?",
        "Cách xử lý BackgroundTasks trong FastAPI?",
    ]

    selected_sample = None
    for q in sample_queries:
        if st.button(f"📌 {q[:38]}...", key=f"btn_{q}"):
            selected_sample = q

    st.markdown("---")
    if st.button("🗑️ Xóa lịch sử chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()


# Main chat interface
st.markdown('<div class="main-header">⚡ FastAPI Documentation Assistant</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Trợ lý AI hỏi đáp tài liệu chính thức của FastAPI với trích dẫn nguồn chuẩn xác <code>[S1]</code> và thông số thời gian thực.</div>',
    unsafe_allow_html=True,
)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display prior chat messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

        # Render metadata if present
        if msg.get("meta"):
            meta = msg["meta"]

            # Latency badges
            st.markdown(
                f"""
                <div>
                    <span class="metric-badge badge-retrieval">⚡ Retrieval: {meta.get('retrieval_ms', 0):.1f} ms</span>
                    <span class="metric-badge badge-gen">🤖 Generation: {meta.get('gen_ms', 0):.1f} ms</span>
                    <span class="metric-badge badge-total">⏱️ Total: {meta.get('total_ms', 0):.1f} ms</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Sources
            sources = meta.get("sources", [])
            if sources:
                st.markdown("**📚 Tài liệu nguồn trích dẫn:**")
                cols = st.columns(min(len(sources), 3))
                for idx, src in enumerate(sources):
                    col = cols[idx % len(cols)]
                    with col:
                        st.markdown(
                            f"[{src.get('source_id')}] **[{src.get('title')}]({src.get('url')})**\n\n"
                            f"<small>🔗 Canonical Docs</small>",
                            unsafe_allow_html=True,
                        )

            # Optional retrieved chunks viewer
            chunks = meta.get("retrieved_chunks", [])
            if chunks:
                with st.expander(f"🔍 Xem {len(chunks)} chunks đã truy xuất từ ChromaDB"):
                    for i, chunk in enumerate(chunks, start=1):
                        st.markdown(
                            f"**[Chunk #{i}] {chunk.get('title')}** | Score: `{chunk.get('score', 0):.4f}`\n\n"
                            f"- Source: `{chunk.get('source')}`\n"
                            f"- URL: [{chunk.get('url')}]({chunk.get('url')})\n\n"
                            f"```text\n{chunk.get('text')}\n```"
                        )


# Process input
prompt = st.chat_input("Nhập câu hỏi về FastAPI (tiếng Việt hoặc tiếng Anh)...")
if selected_sample:
    prompt = selected_sample

if prompt:
    # Append user question
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate assistant answer
    with st.chat_message("assistant"):
        with st.spinner("Đang tìm kiếm tài liệu và sinh câu trả lời..."):
            response_data = call_chat_api(
                question=prompt,
                top_k=top_k_slider,
                model=model_input,
            )

        if response_data:
            answer_text = response_data.get("answer", "")
            st.markdown(answer_text)

            meta_info = {
                "retrieval_ms": response_data.get("retrieval_latency_ms", 0),
                "gen_ms": response_data.get("generation_latency_ms", 0),
                "total_ms": response_data.get("total_latency_ms", 0),
                "sources": response_data.get("sources", []),
                "retrieved_chunks": response_data.get("retrieved_chunks", []),
            }

            # Render badges
            st.markdown(
                f"""
                <div>
                    <span class="metric-badge badge-retrieval">⚡ Retrieval: {meta_info['retrieval_ms']:.1f} ms</span>
                    <span class="metric-badge badge-gen">🤖 Generation: {meta_info['gen_ms']:.1f} ms</span>
                    <span class="metric-badge badge-total">⏱️ Total: {meta_info['total_ms']:.1f} ms</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Render cited sources
            sources = meta_info["sources"]
            if sources:
                st.markdown("**📚 Tài liệu nguồn trích dẫn:**")
                cols = st.columns(min(len(sources), 3))
                for idx, src in enumerate(sources):
                    col = cols[idx % len(cols)]
                    with col:
                        st.markdown(
                            f"[{src.get('source_id')}] **[{src.get('title')}]({src.get('url')})**\n\n"
                            f"<small>🔗 Canonical Docs</small>",
                            unsafe_allow_html=True,
                        )

            # Expandable full chunks
            chunks = meta_info["retrieved_chunks"]
            if chunks:
                with st.expander(f"🔍 Xem {len(chunks)} chunks đã truy xuất từ ChromaDB"):
                    for i, chunk in enumerate(chunks, start=1):
                        st.markdown(
                            f"**[Chunk #{i}] {chunk.get('title')}** | Score: `{chunk.get('score', 0):.4f}`\n\n"
                            f"- Source: `{chunk.get('source')}`\n"
                            f"- URL: [{chunk.get('url')}]({chunk.get('url')})\n\n"
                            f"```text\n{chunk.get('text')}\n```"
                        )

            # Store in session state
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": answer_text,
                    "meta": meta_info,
                }
            )
