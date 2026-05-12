from __future__ import annotations

import argparse

from src.config import get_rag_embedding_backend
from src.rag.index import CHROMA_PERSIST_DIR, build_vector_store


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build the persistent Chroma index used by semantic search."
    )
    parser.add_argument(
        "--force-rebuild",
        action="store_true",
        help="Delete the existing index directory before rebuilding it.",
    )
    args = parser.parse_args()

    store = build_vector_store(force_rebuild=args.force_rebuild)
    total_documents = store._collection.count()

    print(f"RAG index ready in {CHROMA_PERSIST_DIR}")
    print(f"Embedding backend: {get_rag_embedding_backend()}")
    print(f"Indexed documents: {total_documents}")


if __name__ == "__main__":
    main()