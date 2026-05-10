from __future__ import annotations

import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import AnyMessage
from langchain_openai import ChatOpenAI

from src.agent.tools import TOOLS


SYSTEM_PROMPT = """Eres un agente conversacional experto en analisis de conversaciones digitales.

Tu tarea es ayudar a usuarios de negocio a entender comentarios, hilos y propagacion
de mensajes. Usa las herramientas disponibles cuando la pregunta requiera datos del
dataset. No inventes metricas ni ids.

Reglas:
- Si el usuario pregunta por emociones, clima emocional o reacciones, usa consultar_emociones.
- Si el usuario pide resumen de un hilo y proporciona thread_id, usa consultar_resumen_hilo.
- Si el usuario pregunta por propagacion, alcance, impacto, arbol de respuestas o root_id,
  usa consultar_propagacion.
- Si el usuario quiere buscar información general, temas específicos, o preguntas de búsqueda semántica en los comentarios, usa buscar_comentarios.
- Si falta un id necesario, pide el dato exacto antes de llamar la herramienta.
- Responde en espanol claro y resume los resultados tecnicos en lenguaje entendible.
"""


def configure_observability() -> None:
    """Enable LangSmith only when the required credentials are present."""
    tracing_enabled = os.getenv("LANGSMITH_TRACING", "").lower() == "true"
    has_langsmith_key = bool(os.getenv("LANGSMITH_API_KEY"))

    if tracing_enabled and not has_langsmith_key:
        os.environ["LANGSMITH_TRACING"] = "false"


def build_agent():
    """Build the LangChain agent with MCP tools and LangSmith tracing support."""
    load_dotenv()
    configure_observability()

    model_name = os.getenv("OPENAI_MODEL")
    if not model_name:
        raise RuntimeError(
            "Missing OPENAI_MODEL. Add it to your .env file, for example OPENAI_MODEL=gpt-4.1-mini."
        )

    llm = ChatOpenAI(
        model=model_name,
        temperature=0,
    )

    return create_agent(
        model=llm,
        tools=TOOLS,
        system_prompt=SYSTEM_PROMPT,
    )


def get_last_message_text(messages: list[AnyMessage]) -> str:
    """Extract the final assistant message from a LangChain agent response."""
    if not messages:
        return ""

    content = messages[-1].content
    if isinstance(content, str):
        return content

    return str(content)
