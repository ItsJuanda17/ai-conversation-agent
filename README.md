# ai-conversation-agent

Agente conversacional para analizar conversaciones digitales usando servicios MCP,
LangChain, LangSmith y RAG.

## Demo actual

Por ahora el proyecto permite ejecutar una interfaz web monolitica y cuatro
servicios analiticos:

- Emociones en comentarios.
- Resumen basico de hilos.
- Propagacion y arbol de respuestas.
- Busqueda semantica RAG.

### 1. Activar entorno

```powershell
.\.venv\Scripts\Activate.ps1
```

### 2. Levantar servicios MCP

```powershell
uvicorn src.mcp_services.app:app --reload
```

Swagger queda disponible en:

```text
http://127.0.0.1:8000/docs
```

La interfaz web queda disponible en:

```text
http://127.0.0.1:8000/
```

### 3. Probar sin consumir tokens desde terminal

En otra terminal:

```powershell
.\.venv\Scripts\Activate.ps1
python -m src.agent.rule_based_cli
```

Ejemplos:

```text
Analiza las emociones en comentarios sobre reforma laboral
Resume el hilo thread_id tikapi_7520430294948793606
Analiza la propagacion del root_id 106064209472141_767905085584441
```

### 4. Probar con LangChain y OpenAI

Este modo consume tokens de la API de OpenAI.

Crear un archivo `.env` basado en `.env.example` y configurar:

```env
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4.1-mini
USE_LLM_ANALYSIS=false
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=
LANGSMITH_PROJECT=agente-conversaciones-reto
```

Luego ejecutar:

```powershell
python -m src.agent.chat_cli
```

Si no hay cuota disponible en OpenAI, usar el modo sin LLM mientras se desarrolla.

Para activar resumen y emociones con LLM en los endpoints MCP, cambiar:

```env
USE_LLM_ANALYSIS=true
```

La busqueda RAG usa embeddings de OpenAI cuando necesita construir o consultar
el indice vectorial.
