from __future__ import annotations

from pydantic import BaseModel, Field


class CommentsRequest(BaseModel):
    query: str = Field(..., description="Text or topic to search in comments.")
    limit: int = Field(default=20, ge=1, le=100)


class ThreadSummaryRequest(BaseModel):
    thread_id: str = Field(..., description="Conversation thread identifier.")
    limit: int = Field(default=100, ge=1, le=500)


class PropagationRequest(BaseModel):
    root_id: str = Field(..., description="Message id used as propagation root.")
    max_depth: int = Field(default=10, ge=1, le=50)
