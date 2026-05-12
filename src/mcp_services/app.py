import os
from pathlib import Path
from collections import Counter
from typing import Literal

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from openai import APIError

from src.data.queries import find_comments, get_response_tree, get_thread
from src.data.rag import semantic_search
from src.mcp_services.schemas import (
    CommentsRequest,
    PropagationRequest,
    SearchRequest,
    ThreadSummaryRequest,
)

BASE_DIR = Path(__file__).resolve().parents[1]
WEB_DIR = BASE_DIR / "web"
STATIC_DIR = WEB_DIR / "static"

app = FastAPI(
    title="Conversation Analysis MCP Services",
    description="Analytical microservices for comments, threads, and propagation.",
    version="0.1.0",
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class CommentEmotion(BaseModel):
    emotion: Literal["joy", "anger", "fear", "sadness", "neutral"] = Field(
        ..., description="The primary emotion of the comment."
    )

def get_llm():
    model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    return ChatOpenAI(model=model_name, temperature=0)


def use_llm_analysis() -> bool:
    return os.getenv("USE_LLM_ANALYSIS", "false").lower() == "true"


def infer_emotion_heuristic(text: str, sentiment: str) -> str:
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


def infer_emotions_batch(comments: list[dict]) -> list[str]:
    """Infer emotions for a batch of comments using an LLM."""
    if not comments:
        return []

    if not use_llm_analysis():
        return [infer_emotion_heuristic(c["text"], c.get("sentiment", "")) for c in comments]

    llm = get_llm()
    structured_llm = llm.with_structured_output(CommentEmotion)
    
    emotions = []
    # Can batch if the model supports it, but for simplicity we can just map or batch
    # Langchain batch
    texts = [c["text"] for c in comments]
    try:
        results = structured_llm.batch(texts)
    except APIError:
        return [infer_emotion_heuristic(c["text"], c.get("sentiment", "")) for c in comments]
    
    for res in results:
        if res and hasattr(res, "emotion"):
            emotions.append(res.emotion)
        else:
            emotions.append("neutral")
            
    return emotions


def build_extractive_summary(messages: list[dict], max_items: int = 5) -> list[str]:
    candidates = [
        message["text"].strip()
        for message in messages
        if message.get("text") and len(message["text"].strip()) > 40
    ]
    return candidates[:max_items]


def generate_llm_summary(messages: list[dict], max_items: int = 5) -> list[str]:
    """Generate a summary of the thread using an LLM."""
    if not messages:
        return []

    if not use_llm_analysis():
        return build_extractive_summary(messages, max_items=max_items)
        
    llm = get_llm()
    
    text_content = "\n".join([f"- {msg['text']}" for msg in messages if msg.get('text')])
    
    prompt = PromptTemplate.from_template(
        "Eres un analista experto. Resume el siguiente hilo de conversación en máximo {max_items} puntos clave o mensajes representativos.\n"
        "Hilo:\n{text_content}\n\n"
        "Devuelve cada punto en una nueva línea comenzando con un guión (-)."
    )
    
    chain = prompt | llm
    try:
        result = chain.invoke({"max_items": max_items, "text_content": text_content[:10000]})
    except APIError:
        return build_extractive_summary(messages, max_items=max_items)
    
    lines = str(result.content).split("\n")
    summary = [line.strip("- *").strip() for line in lines if line.strip()]
    return summary[:max_items]


@app.get("/")
def frontend() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

@app.post("/analisis/emociones")
def analyze_emotions(request: CommentsRequest) -> dict:
    comments = find_comments(request.query, limit=request.limit)
    enriched_comments = []
    emotion_counts: Counter[str] = Counter()
    
    emotions = infer_emotions_batch(comments)

    for comment, emotion in zip(comments, emotions):
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
        "representative_messages": generate_llm_summary(messages),
        "messages": messages,
    }

@app.post("/analisis/propagacion")
def analyze_propagation(request: PropagationRequest) -> dict:
    return get_response_tree(request.root_id, max_depth=request.max_depth)

@app.post("/analisis/busqueda_semantica")
def search_semantic(request: SearchRequest) -> dict:
    results = semantic_search(request.query, limit=request.limit)
    return {
        "query": request.query,
        "total_results": len(results),
        "results": results,
    }
