from src.data.loaders import load_normalized_dataset


def main() -> None:
    df = load_normalized_dataset()

    print(df[["id", "isComment", "createdAtDatetime", "text"]].head(10))
    print()
    print(df.dtypes[["isComment", "createdAt", "createdAtDatetime"]])


if __name__ == "__main__":
    main()
