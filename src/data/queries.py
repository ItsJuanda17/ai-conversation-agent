from __future__ import annotations

from collections import deque
from typing import Any

import pandas as pd

from src.data.loaders import load_normalized_dataset


def row_to_message(row: pd.Series) -> dict[str, Any]:
    """Convert a pandas row into a small JSON-friendly message."""
    created_at = row.get("createdAtDatetime")

    return {
        "id": row.get("id", ""),
        "thread_id": row.get("threadId", ""),
        "parent_id": row.get("parentId", ""),
        "author": row.get("author", ""),
        "text": row.get("text", ""),
        "sentiment": row.get("sentiment", ""),
        "is_comment": bool(row.get("isComment", False)),
        "created_at": created_at.isoformat() if pd.notna(created_at) else None,
        "social_type": row.get("socialType", ""),
        "url": row.get("url") or row.get("sourceURL", ""),
    }


def find_comments(query: str, limit: int = 20) -> list[dict[str, Any]]:
    """Return comments whose text contains the query terms."""
    df = load_normalized_dataset()
    comments = df[df["isComment"]].copy()

    query = query.strip()
    if query:
        terms = [term for term in query.split() if len(term) > 2]
        mask = pd.Series(True, index=comments.index)
        for term in terms:
            mask &= comments["text"].str.contains(term, case=False, na=False, regex=False)
        comments = comments[mask]

    comments = comments.sort_values("createdAtDatetime", ascending=True).head(limit)
    return [row_to_message(row) for _, row in comments.iterrows()]


def get_thread(thread_id: str, limit: int = 100) -> dict[str, Any]:
    """Return the messages that belong to one conversation thread."""
    df = load_normalized_dataset()
    thread = df[df["threadId"] == thread_id].copy()
    thread = thread.sort_values("createdAtDatetime", ascending=True).head(limit)

    return {
        "thread_id": thread_id,
        "total_messages": int(len(thread)),
        "messages": [row_to_message(row) for _, row in thread.iterrows()],
    }


def calculate_propagation_metrics(
    root: pd.Series | None,
    descendants: list[dict[str, Any]],
) -> dict[str, Any]:
    """Calculate impact metrics for a response tree."""
    authors = {
        item["author"]
        for item in descendants
        if item.get("author")
    }
    timestamps = pd.to_datetime(
        [item["created_at"] for item in descendants if item.get("created_at")],
        errors="coerce",
    ).dropna()

    first_reply_at = timestamps.min() if len(timestamps) else None
    last_reply_at = timestamps.max() if len(timestamps) else None
    propagation_minutes = None
    average_replies_per_hour = None

    if first_reply_at is not None and last_reply_at is not None:
        propagation_minutes = (last_reply_at - first_reply_at).total_seconds() / 60
        hours = max(propagation_minutes / 60, 1)
        average_replies_per_hour = len(descendants) / hours

    root_created_at = root.get("createdAtDatetime") if root is not None else None
    first_reply_delay_minutes = None

    if root_created_at is not None and first_reply_at is not None and pd.notna(root_created_at):
        first_reply_delay_minutes = (first_reply_at - root_created_at).total_seconds() / 60

    return {
        "reach": len(descendants),
        "unique_authors": len(authors),
        "first_reply_at": first_reply_at.isoformat() if first_reply_at is not None else None,
        "last_reply_at": last_reply_at.isoformat() if last_reply_at is not None else None,
        "propagation_minutes": propagation_minutes,
        "first_reply_delay_minutes": first_reply_delay_minutes,
        "average_replies_per_hour": average_replies_per_hour,
    }


def get_response_tree(root_id: str, max_depth: int = 10) -> dict[str, Any]:
    """Build a response tree starting from a message id."""
    df = load_normalized_dataset()
    by_id = {row["id"]: row for _, row in df.iterrows()}
    children_by_parent: dict[str, list[pd.Series]] = {}

    for _, row in df.iterrows():
        parent_id = row.get("parentId", "")
        if parent_id:
            children_by_parent.setdefault(parent_id, []).append(row)

    root = by_id.get(root_id)
    queue: deque[tuple[str, int]] = deque([(root_id, 0)])
    visited: set[str] = set()
    descendants: list[dict[str, Any]] = []

    while queue:
        current_id, depth = queue.popleft()
        if current_id in visited or depth >= max_depth:
            continue

        visited.add(current_id)
        children = children_by_parent.get(current_id, [])

        for child in children:
            child_id = child["id"]
            descendants.append(
                {
                    **row_to_message(child),
                    "depth": depth + 1,
                }
            )
            queue.append((child_id, depth + 1))

    metrics = calculate_propagation_metrics(root, descendants)

    return {
        "root_id": root_id,
        "root_found": root is not None,
        "root_message": row_to_message(root) if root is not None else None,
        "direct_replies": len(children_by_parent.get(root_id, [])),
        "total_descendants": len(descendants),
        "max_depth_observed": max([item["depth"] for item in descendants], default=0),
        "metrics": metrics,
        "descendants": descendants,
    }
