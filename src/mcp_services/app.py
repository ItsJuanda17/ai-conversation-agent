from __future__ import annotations

from collections import Counter

from fastapi import FastAPI

from src.data.queries import find_comments, get_response_tree, get_thread
from src.mcp_services.schemas import (
    CommentsRequest,
    PropagationRequest,
    ThreadSummaryRequest,
)


app = FastAPI(
    title="Conversation Analysis MCP Services",
    description="Analytical microservices for comments, threads, and propagation.",
    version="0.1.0",
)


def infer_emotion(text: str, sentiment: str) -> str:
    """Infer a simple emotion label using sentiment and keywords.

    This is a baseline. Later we can replace it with an LLM classifier while
    preserving the same endpoint contract.
    """
    normalized = text.lower()
    if any(word in normalized for word in ["jaj", "excelente", "bueno", "gracias"]):
        return "joy"
    if any(word in normalized for word in ["rabia", "asco", "odio", "corrupto", "hdp"]):
        return "anger"
    if any(word in normalized for word in ["miedo", "preocupa", "grave", "terrible"]):
        return "fear"
    if any(word in normalized for word in ["triste", "dolor", "pobre"]):
        return "sadness"
    if sentiment == "NEGATIVE":
        return "anger"
    if sentiment == "POSITIVE":
        return "joy"
    return "neutral"


def build_extractive_summary(messages: list[dict], max_items: int = 5) -> list[str]:
    """Select short representative messages as a first summary baseline."""
    candidates = [
        message["text"].strip()
        for message in messages
        if message.get("text") and len(message["text"].strip()) > 40
    ]
    return candidates[:max_items]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/analisis/emociones")
def analyze_emotions(request: CommentsRequest) -> dict:
    comments = find_comments(request.query, limit=request.limit)
    enriched_comments = []
    emotion_counts: Counter[str] = Counter()

    for comment in comments:
        emotion = infer_emotion(comment["text"], comment["sentiment"])
        emotion_counts[emotion] += 1
        enriched_comments.append({**comment, "emotion": emotion})

    return {
        "query": request.query,
        "total_comments": len(enriched_comments),
        "emotion_distribution": dict(emotion_counts),
        "comments": enriched_comments,
    }


@app.post("/analisis/resumen")
def summarize_thread(request: ThreadSummaryRequest) -> dict:
    thread = get_thread(request.thread_id, limit=request.limit)
    messages = thread["messages"]
    sentiments = Counter(message["sentiment"] for message in messages if message.get("sentiment"))

    return {
        "thread_id": request.thread_id,
        "total_messages": thread["total_messages"],
        "sentiment_distribution": dict(sentiments),
        "representative_messages": build_extractive_summary(messages),
        "messages": messages,
    }


@app.post("/analisis/propagacion")
def analyze_propagation(request: PropagationRequest) -> dict:
    return get_response_tree(request.root_id, max_depth=request.max_depth)
