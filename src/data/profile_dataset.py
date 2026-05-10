from pathlib import Path

import pandas as pd

DATASET_PATH = Path("data/raw/reto_data.parquet")

def main() -> None:
    df = pd.read_parquet(DATASET_PATH)
    print("=== Basic profile ===")
    print(f"Rows: {len(df)}")
    print(f"Columns: {len(df.columns)}")

    print("\n=== Column types and missing values ===")
    
    key_columns = ["id",
                   "threadId",
                   "parentId",
                   "isComment",
                   "createdAt",
                   "author",
                   "text",
                   "sentiment", 
                   "type",
                   "socialType", 
    ]

    for column in key_columns:
        print(f"\n--- {column} ---")
        print(df[column].head(10).to_string(index=False))

    print("\n=== Value counts ===")
    for column in ["isComment", "sentiment", "type", "socialType", "language", "country"]:
        print(f"\n--- {column} ---")
        print(df[column].value_counts(dropna=False).to_string())

if __name__ == "__main__":    
    main()
