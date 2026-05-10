from __future__ import annotations

from typing import Any

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from src.agent.mcp_client import (
    call_emotions_service,
    call_propagation_service,
    call_summary_service,
)


class EmotionsInput(BaseModel):
    query: str = Field(..., description="Topic or text to search in comments.")
    limit: int = Field(default=10, ge=1, le=100)


class SummaryInput(BaseModel):
    thread_id: str = Field(..., description="Conversation thread id to summarize.")
    limit: int = Field(default=50, ge=1, le=500)


class PropagationInput(BaseModel):
    root_id: str = Field(..., description="Message id used as propagation root.")
    max_depth: int = Field(default=10, ge=1, le=50)


def consultar_emociones(query: str, limit: int = 10) -> dict[str, Any]:
    """Query comments and return an emotion distribution."""
    return call_emotions_service(query=query, limit=limit)


def consultar_resumen_hilo(thread_id: str, limit: int = 50) -> dict[str, Any]:
    """Query a conversation thread and return a structured summary."""
    return call_summary_service(thread_id=thread_id, limit=limit)


def consultar_propagacion(root_id: str, max_depth: int = 10) -> dict[str, Any]:
    """Query the response tree and return propagation metrics."""
    return call_propagation_service(root_id=root_id, max_depth=max_depth)


TOOLS = [
    StructuredTool.from_function(
        func=consultar_emociones,
        name="consultar_emociones",
        description=(
            "Use this tool when the user asks about emotions, emotional climate, "
            "reactions, anger, fear, joy, sadness, or emotional distribution in comments."
        ),
        args_schema=EmotionsInput,
    ),
    StructuredTool.from_function(
        func=consultar_resumen_hilo,
        name="consultar_resumen_hilo",
        description=(
            "Use this tool when the user asks for a summary of a conversation thread "
            "and provides a thread_id."
        ),
        args_schema=SummaryInput,
    ),
    StructuredTool.from_function(
        func=consultar_propagacion,
        name="consultar_propagacion",
        description=(
            "Use this tool when the user asks how a message propagated, asks about "
            "response tree, reach, depth, direct replies, impact, or provides a root_id."
        ),
        args_schema=PropagationInput,
    ),
]
