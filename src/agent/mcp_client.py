from __future__ import annotations

from typing import Any

import requests


BASE_URL = "http://127.0.0.1:8000"


def call_emotions_service(query: str, limit: int = 10) -> dict[str, Any]:
    response = requests.post(
        f"{BASE_URL}/analisis/emociones",
        json={"query": query, "limit": limit},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def call_summary_service(thread_id: str, limit: int = 50) -> dict[str, Any]:
    response = requests.post(
        f"{BASE_URL}/analisis/resumen",
        json={"thread_id": thread_id, "limit": limit},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def call_propagation_service(root_id: str, max_depth: int = 10) -> dict[str, Any]:
    response = requests.post(
        f"{BASE_URL}/analisis/propagacion",
        json={"root_id": root_id, "max_depth": max_depth},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def call_search_service(query: str, limit: int = 20) -> dict[str, Any]:
    response = requests.post(
        f"{BASE_URL}/analisis/busqueda_semantica",
        json={"query": query, "limit": limit},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()
