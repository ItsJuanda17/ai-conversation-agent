from __future__ import annotations

import pandas as pd
import pytest

from src.rag import index as rag_index


def build_dataset() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "id": "c1",
                "threadId": "t1",
                "parentId": "",
                "author": "ana",
                "text": "La reforma laboral genera debate entre trabajadores",
                "sentiment": "NEUTRAL",
                "isComment": True,
                "createdAtDatetime": pd.Timestamp("2024-01-01T08:00:00Z"),
                "socialType": "x",
                "url": "https://example.com/c1",
                "sourceURL": "",
            },
            {
                "id": "c2",
                "threadId": "t1",
                "parentId": "",
                "author": "luis",
                "text": "Los usuarios celebran las nuevas medidas economicas",
                "sentiment": "POSITIVE",
                "isComment": True,
                "createdAtDatetime": pd.Timestamp("2024-01-01T09:00:00Z"),
                "socialType": "x",
                "url": "https://example.com/c2",
                "sourceURL": "",
            },
            {
                "id": "p1",
                "threadId": "t2",
                "parentId": "",
                "author": "medio",
                "text": "Publicacion principal",
                "sentiment": "NEUTRAL",
                "isComment": False,
                "createdAtDatetime": pd.Timestamp("2024-01-01T07:00:00Z"),
                "socialType": "facebook",
                "url": "https://example.com/p1",
                "sourceURL": "",
            },
        ]
    )


@pytest.fixture(autouse=True)
def reset_rag_state(monkeypatch, tmp_path):
    index_dir = tmp_path / "chroma_db"
    monkeypatch.setattr(rag_index, "CHROMA_PERSIST_DIR", index_dir)
    monkeypatch.setattr(rag_index, "INDEX_METADATA_PATH", index_dir / "index_config.json")
    monkeypatch.setenv("APP_MODE", "development")
    monkeypatch.delenv("RAG_EMBEDDING_BACKEND", raising=False)
    monkeypatch.setenv("RAG_AUTO_BUILD", "false")
    rag_index.reset_vector_store_cache()
    yield
    rag_index.reset_vector_store_cache()


def test_semantic_search_requires_existing_index() -> None:
    with pytest.raises(RuntimeError, match="RAG index not found"):
        rag_index.semantic_search("reforma laboral")


def test_build_vector_store_and_search_with_local_embeddings(mocker) -> None:
    mocker.patch("src.rag.index.load_normalized_dataset", return_value=build_dataset())

    store = rag_index.build_vector_store(force_rebuild=True)
    results = rag_index.semantic_search("reforma laboral", limit=2)

    assert store._collection.count() == 2
    assert len(results) == 2
    assert results[0]["text"]
    assert any("reforma laboral" in item["text"].lower() for item in results)