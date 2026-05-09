from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv


DEFAULT_DATASET_URL = (
    "https://raw.githubusercontent.com/armandoordonez/AI-Engineering/main/"
    "data/Reto_data_20251023_122206.parquet"
)
DEFAULT_DATASET_PATH = "data/raw/reto_data.parquet"


def download_dataset(url: str, destination: Path) -> None:
    """Download the dataset only when it is not already present locally."""
    destination.parent.mkdir(parents=True, exist_ok=True)

    response = requests.get(url, timeout=60)
    response.raise_for_status()
    destination.write_bytes(response.content)


def load_dataset(path: Path) -> pd.DataFrame:
    """Load the parquet dataset into a pandas DataFrame."""
    return pd.read_parquet(path)


def inspect_dataset(df: pd.DataFrame) -> None:
    """Print the first facts we need before designing the MCP services."""
    print("\n=== Dataset shape ===")
    print(f"Rows: {df.shape[0]:,}")
    print(f"Columns: {df.shape[1]:,}")

    print("\n=== Columns and types ===")
    for column, dtype in df.dtypes.items():
        missing = df[column].isna().sum()
        print(f"- {column}: {dtype} | missing: {missing:,}")

    print("\n=== Sample rows ===")
    with pd.option_context("display.max_columns", None, "display.width", 160):
        print(df.head(5))


def main() -> None:
    load_dotenv()

    dataset_url = os.getenv("DATASET_URL", DEFAULT_DATASET_URL)
    dataset_path = Path(os.getenv("DATASET_PATH", DEFAULT_DATASET_PATH))

    if not dataset_path.exists():
        print(f"Downloading dataset to {dataset_path}...")
        download_dataset(dataset_url, dataset_path)
    else:
        print(f"Using local dataset at {dataset_path}")

    df = load_dataset(dataset_path)
    inspect_dataset(df)


if __name__ == "__main__":
    main()
