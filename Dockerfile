FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/
COPY data/raw/ data/raw/

# Bake the local RAG index into the image so semantic search works immediately on deploy.
RUN APP_MODE=development RAG_EMBEDDING_BACKEND=local python -m src.rag.build_index --force-rebuild

CMD uvicorn src.mcp_services.app:app --host 0.0.0.0 --port ${PORT:-8000}
