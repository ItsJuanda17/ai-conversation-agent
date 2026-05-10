from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

from src.data.loaders import load_normalized_dataset
from src.data.queries import row_to_message

load_dotenv()

CHROMA_PERSIST_DIR = Path("data/chroma_db")

_vector_store: Chroma | None = None


def get_vector_store() -> Chroma:
    """Initialize and return the Chroma vector store.
    
    If the persistence directory does not exist, it attempts to load the dataset
    and build the vector store from the 'isComment' entries.
    """
    global _vector_store
    if _vector_store is not None:
        return _vector_store

    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small"
    )

    if CHROMA_PERSIST_DIR.exists() and os.listdir(CHROMA_PERSIST_DIR):
        _vector_store = Chroma(
            persist_directory=str(CHROMA_PERSIST_DIR),
            embedding_function=embeddings,
        )
    else:
        # Build the vector store if dataset exists
        try:
            df = load_normalized_dataset()
            comments = df[df["isComment"]].copy()
            
            documents = []
            for _, row in comments.iterrows():
                msg = row_to_message(row)
                text = msg.get("text", "")
                if text and len(text.strip()) > 5:
                    # Storing string values in metadata, Chroma requires primitives
                    metadata = {
                        k: str(v) if v is not None else "" 
                        for k, v in msg.items() 
                        if k != "text"
                    }
                    doc = Document(page_content=text, metadata=metadata)
                    documents.append(doc)
            
            _vector_store = Chroma.from_documents(
                documents=documents,
                embedding=embeddings,
                persist_directory=str(CHROMA_PERSIST_DIR),
            )
        except FileNotFoundError:
            print("WARNING: Dataset not found. Creating an empty ChromaDB store.")
            _vector_store = Chroma(
                persist_directory=str(CHROMA_PERSIST_DIR),
                embedding_function=embeddings,
            )

    return _vector_store


def semantic_search(query: str, limit: int = 20) -> list[dict[str, Any]]:
    """Search for comments similar to the query using vector embeddings."""
    store = get_vector_store()
    
    # Check if empty
    try:
        if store._collection.count() == 0:
            return []
    except Exception:
        pass
        
    docs = store.similarity_search(query, k=limit)
    
    results = []
    for doc in docs:
        item = dict(doc.metadata)
        item["text"] = doc.page_content
        results.append(item)
        
    return results
