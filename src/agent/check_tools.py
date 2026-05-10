from src.agent.tools import TOOLS


def main() -> None:
    print("=== Available LangChain tools ===")
    for tool in TOOLS:
        print(f"- {tool.name}: {tool.description[:90]}...")

    print("\n=== Direct tool call ===")
    emotions_tool = next(tool for tool in TOOLS if tool.name == "consultar_emociones")
    result = emotions_tool.invoke({"query": "reforma", "limit": 3})
    print(result["emotion_distribution"])


if __name__ == "__main__":
    main()
