from __future__ import annotations

import argparse

from langchain_core.messages import HumanMessage

from src.agent.agent import build_agent, get_last_message_text


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Invoke the LangChain agent once to validate tool calling and tracing."
    )
    parser.add_argument(
        "prompt",
        nargs="?",
        default="Resume el hilo thread_id tikapi_7520430294948793606",
        help="User prompt sent to the agent.",
    )
    args = parser.parse_args()

    agent = build_agent()
    result = agent.invoke({"messages": [HumanMessage(content=args.prompt)]})
    print(get_last_message_text(result["messages"]))


if __name__ == "__main__":
    main()