from src.data.queries import find_comments, get_response_tree, get_thread


def main() -> None:
    print("=== Comments containing 'reforma' ===")
    comments = find_comments("reforma", limit=3)
    for comment in comments:
        print(f"- {comment['id']} | {comment['text'][:120]}")

    if not comments:
        return

    thread_id = comments[0]["thread_id"]
    root_id = comments[0]["parent_id"] or comments[0]["id"]

    print("\n=== Thread sample ===")
    thread = get_thread(thread_id, limit=5)
    print(f"Thread: {thread['thread_id']}")
    print(f"Messages returned: {len(thread['messages'])}")

    print("\n=== Response tree sample ===")
    tree = get_response_tree(root_id)
    print(f"Root id: {tree['root_id']}")
    print(f"Root found: {tree['root_found']}")
    print(f"Direct replies: {tree['direct_replies']}")
    print(f"Total descendants: {tree['total_descendants']}")
    print(f"Max depth: {tree['max_depth_observed']}")


if __name__ == "__main__":
    main()
