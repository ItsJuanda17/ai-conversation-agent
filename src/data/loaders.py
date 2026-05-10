from __future__ import annotations

from html import unescape
from pathlib import Path

import pandas as pd


DATASET_PATH = Path("data/raw/reto_data.parquet")


def parse_bool(value: object) -> bool:
    """Convert string values like 'True'/'False' into real booleans."""
    return str(value).strip().lower() == "true"


def clean_text(value: object) -> str:
    """Normalize empty values and decode HTML entities like &aacute;."""
    text = str(value or "").strip()
    return unescape(text)


def load_raw_dataset(path: Path = DATASET_PATH) -> pd.DataFrame:
    """Load the original parquet file without modifying it."""
    return pd.read_parquet(path)


def load_normalized_dataset(path: Path = DATASET_PATH) -> pd.DataFrame:
    """Load and normalize the fields we need for the agent and MCP services."""
    df = load_raw_dataset(path).copy()

    text_columns = [
        "id",
        "threadId",
        "parentId",
        "parentText",
        "author",
        "authorId",
        "text",
        "title",
        "context",
        "sentiment",
        "type",
        "socialType",
        "language",
        "country",
        "url",
        "sourceURL",
    ]

    for column in text_columns:
        if column in df.columns:
            df[column] = df[column].map(clean_text)

    bool_columns = [
        "isComment",
        "isBot",
        "isDeleted",
        "isHidden",
        "isRead",
        "isReplied",
        "hasImageOrVideo",
    ]

    for column in bool_columns:
        if column in df.columns:
            df[column] = df[column].map(parse_bool)

    if "createdAt" in df.columns:
        df["createdAt"] = pd.to_numeric(df["createdAt"], errors="coerce")
        df["createdAtDatetime"] = pd.to_datetime(
            df["createdAt"],
            unit="ms",
            errors="coerce",
        )

    return df
