from unittest.mock import patch
from src.agent.tools import consultar_emociones, consultar_resumen_hilo, buscar_comentarios

@patch("src.agent.tools.call_emotions_service")
def test_consultar_emociones(mock_call):
    mock_call.return_value = {"status": "ok"}
    res = consultar_emociones("test", 10)
    mock_call.assert_called_once_with(query="test", limit=10)
    assert res == {"status": "ok"}

@patch("src.agent.tools.call_summary_service")
def test_consultar_resumen_hilo(mock_call):
    mock_call.return_value = {"status": "ok"}
    res = consultar_resumen_hilo("t1", 50)
    mock_call.assert_called_once_with(thread_id="t1", limit=50)
    assert res == {"status": "ok"}

@patch("src.agent.tools.call_search_service")
def test_buscar_comentarios(mock_call):
    mock_call.return_value = {"status": "ok"}
    res = buscar_comentarios("topic", 20)
    mock_call.assert_called_once_with(query="topic", limit=20)
    assert res == {"status": "ok"}
