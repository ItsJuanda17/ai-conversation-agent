from fastapi.testclient import TestClient

from src.mcp_services.app import app


def main() -> None:
    client = TestClient(app)

    print("=== Health ===")
    print(client.get("/health").json())

    print("\n=== Emotions ===")
    emotions = client.post(
        "/analisis/emociones",
        json={"query": "reforma", "limit": 3},
    )
    print(emotions.json())

    comments = emotions.json()["comments"]
    if not comments:
        return

    print("\n=== Summary ===")
    thread_id = comments[0]["thread_id"]
    summary = client.post(
        "/analisis/resumen",
        json={"thread_id": thread_id, "limit": 5},
    )
    print(summary.json())

    print("\n=== Propagation ===")
    root_id = comments[0]["parent_id"] or comments[0]["id"]
    propagation = client.post(
        "/analisis/propagacion",
        json={"root_id": root_id, "max_depth": 5},
    )
    print(propagation.json())


if __name__ == "__main__":
    main()
