from __future__ import annotations

import os
from typing import Literal

from dotenv import load_dotenv

load_dotenv()

AppMode = Literal["development", "demo"]
RagEmbeddingBackend = Literal["local", "openai"]


def get_app_mode() -> AppMode:
    mode = os.getenv("APP_MODE", "development").strip().lower()
    if mode == "demo":
        return "demo"
    return "development"


def use_llm_analysis() -> bool:
    return (
        get_app_mode() == "demo"
        and os.getenv("USE_LLM_ANALYSIS", "false").strip().lower() == "true"
    )


def get_rag_embedding_backend() -> RagEmbeddingBackend:
    configured = os.getenv("RAG_EMBEDDING_BACKEND", "").strip().lower()
    if configured == "openai":
        return "openai"
    if configured == "local":
        return "local"
    return "openai" if get_app_mode() == "demo" else "local"


def rag_auto_build_enabled() -> bool:
    return os.getenv("RAG_AUTO_BUILD", "false").strip().lower() == "true"


def langsmith_tracing_enabled() -> bool:
    return os.getenv("LANGSMITH_TRACING", "false").strip().lower() == "true"


def has_langsmith_api_key() -> bool:
    return bool(os.getenv("LANGSMITH_API_KEY"))
