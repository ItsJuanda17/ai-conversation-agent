from src.agent.mcp_client import (
    call_emotions_service,
    call_propagation_service,
    call_summary_service,
)


def main() -> None:
    emotions = call_emotions_service("reforma", limit=3)

    print("=== Emotions client ===")
    print(emotions["emotion_distribution"])

    first_comment = emotions["comments"][0]
    thread_id = first_comment["thread_id"]
    root_id = first_comment["parent_id"] or first_comment["id"]

    print("\n=== Summary client ===")
    summary = call_summary_service(thread_id, limit=5)
    print(summary["sentiment_distribution"])

    print("\n=== Propagation client ===")
    propagation = call_propagation_service(root_id, max_depth=5)
    print(propagation["metrics"])


if __name__ == "__main__":
    main()
