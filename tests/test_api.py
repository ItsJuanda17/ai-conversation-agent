from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from src.mcp_services.app import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_frontend_index():
    response = client.get("/")
    assert response.status_code == 200
    assert "Agente IA" in response.text


@patch("src.mcp_services.app.find_comments")
@patch("src.mcp_services.app.infer_emotions_batch")
def test_analyze_emotions(mock_infer, mock_find):
    mock_find.return_value = [
        {"id": "1", "text": "Me encanta esto", "sentiment": "POSITIVE"}
    ]
    mock_infer.return_value = ["joy"]
    
    response = client.post("/analisis/emociones", json={"query": "reforma", "limit": 10})
    assert response.status_code == 200
    data = response.json()
    assert data["total_comments"] == 1
    assert "joy" in data["emotion_distribution"]
    assert data["comments"][0]["emotion"] == "joy"

@patch("src.mcp_services.app.get_thread")
@patch("src.mcp_services.app.generate_llm_summary")
def test_summarize_thread(mock_generate, mock_get_thread):
    mock_get_thread.return_value = {
        "thread_id": "t1",
        "total_messages": 2,
        "messages": [
            {"id": "1", "text": "hello", "sentiment": "NEUTRAL"},
            {"id": "2", "text": "world", "sentiment": "NEUTRAL"}
        ]
    }
    mock_generate.return_value = ["Resumen del hilo"]
    
    response = client.post("/analisis/resumen", json={"thread_id": "t1", "limit": 50})
    assert response.status_code == 200
    data = response.json()
    assert data["total_messages"] == 2
    assert data["representative_messages"] == ["Resumen del hilo"]

@patch("src.mcp_services.app.semantic_search")
def test_search_semantic(mock_search):
    mock_search.return_value = [{"id": "1", "text": "test_text"}]
    
    response = client.post("/analisis/busqueda_semantica", json={"query": "test", "limit": 20})
    assert response.status_code == 200
    data = response.json()
    assert data["total_results"] == 1
    assert data["results"][0]["text"] == "test_text"
