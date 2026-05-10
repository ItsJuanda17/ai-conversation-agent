from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage
from openai import APIError, AuthenticationError, RateLimitError

from src.agent.agent import build_agent, get_last_message_text


def main() -> None:
    agent = build_agent()
    messages = []

    print("Agente de conversaciones listo. Escribe 'salir' para terminar.")

    while True:
        user_input = input("\nTu: ").strip()
        if user_input.lower() in {"salir", "exit", "quit"}:
            break

        messages.append(HumanMessage(content=user_input))
        try:
            result = agent.invoke({"messages": messages})
        except RateLimitError:
            print(
                "\nAgente: OpenAI rechazo la llamada por cuota insuficiente. "
                "Puedes revisar billing/cuota o usar el modo sin LLM: "
                "python -m src.agent.rule_based_cli"
            )
            messages.pop()
            continue
        except AuthenticationError:
            print("\nAgente: La OPENAI_API_KEY no es valida o no esta configurada correctamente.")
            messages.pop()
            continue
        except APIError as error:
            print(f"\nAgente: OpenAI devolvio un error de API: {error}")
            messages.pop()
            continue

        assistant_text = get_last_message_text(result["messages"])
        messages.append(AIMessage(content=assistant_text))

        print(f"\nAgente: {assistant_text}")


if __name__ == "__main__":
    main()
