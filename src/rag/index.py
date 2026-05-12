from __future__ import annotations

import hashlib
import json
import math
import shutil
from pathlib import Path
from typing import Any

from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings

from src.config import get_rag_embedding_backend, rag_auto_build_enabled
from src.data.loaders import load_normalized_dataset
from src.data.queries import row_to_message

CHROMA_PERSIST_DIR = Path("data/chroma_db")
INDEX_METADATA_PATH = CHROMA_PERSIST_DIR / "index_config.json"

_vector_store: Chroma | None = None


class LocalHashEmbeddings(Embeddings):
    """Deterministic local embeddings for development and tests."""

    def __init__(self, dimensions: int = 256) -> None:
        self.dimensions = dimensions

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_text(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed_text(text)

    def _embed_text(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions

        for token in text.lower().split():
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            weight = 1.0 + (digest[5] / 255.0)
            vector[index] += sign * weight

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector

        return [value / norm for value in vector]


def reset_vector_store_cache() -> None:
    global _vector_store
    _vector_store = None


def get_embeddings() -> Embeddings:
    backend = get_rag_embedding_backend()
    if backend == "openai":
        return OpenAIEmbeddings(model="text-embedding-3-small")
    return LocalHashEmbeddings()


def vector_store_exists() -> bool:
    if not CHROMA_PERSIST_DIR.exists():
        return False
    return any(CHROMA_PERSIST_DIR.iterdir())


def load_index_metadata() -> dict[str, Any]:
    if not INDEX_METADATA_PATH.exists():
        return {}
    return json.loads(INDEX_METADATA_PATH.read_text(encoding="utf-8"))


def write_index_metadata() -> None:
    CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_METADATA_PATH.write_text(
        json.dumps({"embedding_backend": get_rag_embedding_backend()}, indent=2),
        encoding="utf-8",
    )


def ensure_backend_matches_index() -> None:
    metadata = load_index_metadata()
    expected_backend = metadata.get("embedding_backend")
    current_backend = get_rag_embedding_backend()

    if expected_backend and expected_backend != current_backend:
        raise RuntimeError(
            "The RAG index was built with a different embedding backend. "
            f"Current backend: {current_backend}. Indexed backend: {expected_backend}. "
            "Rebuild the index with `python -m src.rag.build_index --force-rebuild`."
        )


def build_documents() -> list[Document]:
    df = load_normalized_dataset()
    comments = df[df["isComment"]].copy()

    documents: list[Document] = []
    for _, row in comments.iterrows():
        message = row_to_message(row)
        text = message.get("text", "")
        if not text or len(text.strip()) <= 5:
            continue

        metadata = {
            key: str(value) if value is not None else ""
            for key, value in message.items()
            if key != "text"
        }
        documents.append(Document(page_content=text, metadata=metadata))

    return documents


def build_vector_store(force_rebuild: bool = False) -> Chroma:
    global _vector_store

    if force_rebuild and CHROMA_PERSIST_DIR.exists():
        shutil.rmtree(CHROMA_PERSIST_DIR)

    CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)
    documents = build_documents()
    embeddings = get_embeddings()

    _vector_store = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory=str(CHROMA_PERSIST_DIR),
    )
    write_index_metadata()
    return _vector_store


def get_vector_store() -> Chroma:
    """Load an existing vector store or build it only when auto-build is enabled."""
    global _vector_store
    if _vector_store is not None:
        return _vector_store

    if not vector_store_exists():
        if rag_auto_build_enabled():
            return build_vector_store(force_rebuild=False)
        raise RuntimeError(
            "RAG index not found. Build it first with `python -m src.rag.build_index`."
        )

    ensure_backend_matches_index()
    _vector_store = Chroma(
        persist_directory=str(CHROMA_PERSIST_DIR),
        embedding_function=get_embeddings(),
    )
    return _vector_store


def semantic_search(query: str, limit: int = 20) -> list[dict[str, Any]]:
    """Search for comments similar to the query using vector embeddings."""
    store = get_vector_store()

    try:
        if store._collection.count() == 0:
            return []
    except Exception:
        pass

    documents = store.similarity_search(query, k=limit)

    results = []
    for document in documents:
        item = dict(document.metadata)
        item["text"] = document.page_content
        results.append(item)

    return results