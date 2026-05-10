from __future__ import annotations

import re

from src.agent.mcp_client import (
    call_emotions_service,
    call_propagation_service,
    call_summary_service,
)


def extract_after_label(text: str, label: str) -> str | None:
    pattern = rf"{label}\s+([A-Za-z0-9_:-]+)"
    match = re.search(pattern, text, flags=re.IGNORECASE)
    return match.group(1) if match else None


def explain_emotions(query: str) -> str:
    result = call_emotions_service(query=query, limit=5)
    distribution = result["emotion_distribution"]
    return (
        f"Encontre {result['total_comments']} comentarios para '{query}'. "
        f"Distribucion emocional: {distribution}."
    )


def explain_summary(thread_id: str) -> str:
    result = call_summary_service(thread_id=thread_id, limit=10)
    messages = result["representative_messages"]
    sample = messages[0] if messages else "No encontre mensajes representativos."
    return (
        f"El hilo tiene {result['total_messages']} mensajes consultados. "
        f"Distribucion de sentimiento: {result['sentiment_distribution']}. "
        f"Mensaje representativo: {sample[:300]}"
    )


def explain_propagation(root_id: str) -> str:
    result = call_propagation_service(root_id=root_id, max_depth=10)
    metrics = result["metrics"]
    return (
        f"Propagacion para root_id {root_id}: "
        f"respuestas directas={result['direct_replies']}, "
        f"descendientes={result['total_descendants']}, "
        f"profundidad maxima={result['max_depth_observed']}, "
        f"metricas={metrics}."
    )


def route_message(user_input: str) -> str:
    lowered = user_input.lower()

    if any(word in lowered for word in ["propag", "arbol", "alcance", "impacto", "root_id"]):
        root_id = extract_after_label(user_input, "root_id") or extract_after_label(user_input, "mensaje")
        if not root_id:
            return "Para analizar propagacion necesito un root_id o id de mensaje."
        return explain_propagation(root_id)

    if any(word in lowered for word in ["resumen", "resume", "hilo", "thread_id"]):
        thread_id = extract_after_label(user_input, "thread_id") or extract_after_label(user_input, "hilo")
        if not thread_id:
            return "Para resumir necesito un thread_id."
        return explain_summary(thread_id)

    if any(word in lowered for word in ["emocion", "emociones", "clima", "reacciones"]):
        query = user_input
        for removable in ["analiza", "las", "emociones", "en", "comentarios", "sobre"]:
            query = re.sub(rf"\b{removable}\b", "", query, flags=re.IGNORECASE)
        return explain_emotions(query.strip() or "reforma")

    return (
        "Puedo ayudarte con emociones, resumen de hilos o propagacion. "
        "Por ejemplo: 'Analiza emociones sobre reforma laboral'."
    )


def main() -> None:
    print("Agente local sin LLM listo. Escribe 'salir' para terminar.")

    while True:
        user_input = input("\nTu: ").strip()
        if user_input.lower() in {"salir", "exit", "quit"}:
            break
        print(f"\nAgente: {route_message(user_input)}")


if __name__ == "__main__":
    main()
