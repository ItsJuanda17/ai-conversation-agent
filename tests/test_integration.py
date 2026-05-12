"""Integration tests for the complete ai-conversation-agent application.

These tests exercise the real data layer (loaders, queries) and verify
the FastAPI endpoints work end-to-end with the actual dataset.
"""

import pytest
from pathlib import Path

# ── Data Layer ──────────────────────────────────────────────────────────────

DATASET_EXISTS = Path("data/raw/reto_data.parquet").exists()


@pytest.mark.skipif(not DATASET_EXISTS, reason="Dataset not available")
class TestDataLoaders:
    def test_load_normalized_dataset(self):
        from src.data.loaders import load_normalized_dataset

        df = load_normalized_dataset()
        assert len(df) > 0, "Dataset should not be empty"
        assert "id" in df.columns
        assert "text" in df.columns
        assert "isComment" in df.columns
        assert "threadId" in df.columns
        assert "parentId" in df.columns
        assert "createdAtDatetime" in df.columns
        print(f"  Dataset loaded: {len(df)} rows, {len(df.columns)} columns")

    def test_boolean_columns_are_bool(self):
        from src.data.loaders import load_normalized_dataset

        df = load_normalized_dataset()
        assert df["isComment"].dtype == bool, "isComment should be bool"

    def test_text_is_cleaned(self):
        from src.data.loaders import load_normalized_dataset

        df = load_normalized_dataset()
        # No raw HTML entities should remain
        sample = df["text"].dropna().head(100)
        for text in sample:
            assert "&amp;" not in text, "HTML entities should be decoded"


@pytest.mark.skipif(not DATASET_EXISTS, reason="Dataset not available")
class TestDataQueries:
    def test_find_comments_returns_results(self):
        from src.data.queries import find_comments

        results = find_comments("reforma", limit=5)
        assert isinstance(results, list)
        # May or may not find results depending on dataset
        if results:
            assert "text" in results[0]
            assert "id" in results[0]
            assert "sentiment" in results[0]
            print(f"  find_comments('reforma'): {len(results)} results")

    def test_find_comments_empty_query(self):
        from src.data.queries import find_comments

        results = find_comments("", limit=5)
        assert isinstance(results, list)
        assert len(results) <= 5

    def test_find_comments_respects_limit(self):
        from src.data.queries import find_comments

        results = find_comments("", limit=3)
        assert len(results) <= 3

    def test_get_thread_existing(self):
        from src.data.loaders import load_normalized_dataset
        from src.data.queries import get_thread

        df = load_normalized_dataset()
        thread_ids = df["threadId"].dropna().unique()
        assert len(thread_ids) > 0, "Dataset should have thread IDs"

        thread = get_thread(str(thread_ids[0]), limit=10)
        assert "thread_id" in thread
        assert "total_messages" in thread
        assert "messages" in thread
        assert isinstance(thread["messages"], list)
        print(f"  get_thread: {thread['total_messages']} messages")

    def test_get_thread_nonexistent(self):
        from src.data.queries import get_thread

        thread = get_thread("nonexistent_thread_id_xyz", limit=10)
        assert thread["total_messages"] == 0
        assert thread["messages"] == []

    def test_get_response_tree(self):
        from src.data.loaders import load_normalized_dataset
        from src.data.queries import get_response_tree

        df = load_normalized_dataset()
        parent_ids = df[df["parentId"].str.len() > 0]["parentId"].unique()

        if len(parent_ids) > 0:
            tree = get_response_tree(str(parent_ids[0]), max_depth=3)
            assert "root_id" in tree
            assert "root_found" in tree
            assert "metrics" in tree
            assert "descendants" in tree
            print(
                f"  get_response_tree: root_found={tree['root_found']}, "
                f"descendants={tree['total_descendants']}"
            )

    def test_get_response_tree_nonexistent(self):
        from src.data.queries import get_response_tree

        tree = get_response_tree("nonexistent_root_xyz", max_depth=3)
        assert tree["root_found"] is False
        assert tree["root_message"] is None

    def test_row_to_message_fields(self):
        from src.data.loaders import load_normalized_dataset
        from src.data.queries import row_to_message

        df = load_normalized_dataset()
        row = df.iloc[0]
        msg = row_to_message(row)
        expected_keys = {
            "id", "thread_id", "parent_id", "author", "text",
            "sentiment", "is_comment", "created_at", "social_type", "url",
        }
        assert set(msg.keys()) == expected_keys


# ── MCP Services (FastAPI) with real data ───────────────────────────────────

@pytest.mark.skipif(not DATASET_EXISTS, reason="Dataset not available")
class TestFastAPIWithData:
    @pytest.fixture(autouse=True)
    def setup_client(self):
        from unittest.mock import patch, MagicMock

        # Patch LLM calls to avoid needing OpenAI keys
        with patch("src.mcp_services.app.infer_emotions_batch") as mock_emotions, \
             patch("src.mcp_services.app.generate_llm_summary") as mock_summary, \
             patch("src.mcp_services.app.semantic_search") as mock_search:

            mock_emotions.side_effect = lambda comments: ["neutral"] * len(comments)
            mock_summary.return_value = ["Resumen de prueba"]
            mock_search.return_value = [{"id": "1", "text": "test result"}]

            from fastapi.testclient import TestClient
            from src.mcp_services.app import app

            self.client = TestClient(app)
            self.mock_emotions = mock_emotions
            self.mock_summary = mock_summary
            self.mock_search = mock_search
            yield

    def test_health_endpoint(self):
        response = self.client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_emotions_endpoint_with_real_data(self):
        response = self.client.post(
            "/analisis/emociones",
            json={"query": "reforma", "limit": 5},
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_comments" in data
        assert "emotion_distribution" in data
        assert "comments" in data
        print(f"  /analisis/emociones: {data['total_comments']} comments")

    def test_summary_endpoint_with_real_data(self):
        from src.data.loaders import load_normalized_dataset

        df = load_normalized_dataset()
        thread_ids = df["threadId"].dropna().unique()
        if len(thread_ids) == 0:
            pytest.skip("No thread IDs in dataset")

        response = self.client.post(
            "/analisis/resumen",
            json={"thread_id": str(thread_ids[0]), "limit": 10},
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_messages" in data
        assert "representative_messages" in data
        print(f"  /analisis/resumen: {data['total_messages']} messages")

    def test_propagation_endpoint_with_real_data(self):
        from src.data.loaders import load_normalized_dataset

        df = load_normalized_dataset()
        parent_ids = df[df["parentId"].str.len() > 0]["parentId"].unique()
        if len(parent_ids) == 0:
            pytest.skip("No parent IDs in dataset")

        response = self.client.post(
            "/analisis/propagacion",
            json={"root_id": str(parent_ids[0]), "max_depth": 3},
        )
        assert response.status_code == 200
        data = response.json()
        assert "root_id" in data
        assert "metrics" in data
        print(f"  /analisis/propagacion: descendants={data['total_descendants']}")

    def test_semantic_search_endpoint(self):
        response = self.client.post(
            "/analisis/busqueda_semantica",
            json={"query": "reforma laboral", "limit": 5},
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_results" in data
        assert "results" in data

    def test_invalid_emotions_request(self):
        response = self.client.post(
            "/analisis/emociones",
            json={"limit": 5},  # missing 'query'
        )
        assert response.status_code == 422  # Validation error

    def test_invalid_summary_request(self):
        response = self.client.post(
            "/analisis/resumen",
            json={"limit": 5},  # missing 'thread_id'
        )
        assert response.status_code == 422


# ── Schema Validation ──────────────────────────────────────────────────────

class TestSchemas:
    def test_comments_request_valid(self):
        from src.mcp_services.schemas import CommentsRequest

        req = CommentsRequest(query="test", limit=10)
        assert req.query == "test"
        assert req.limit == 10

    def test_comments_request_default_limit(self):
        from src.mcp_services.schemas import CommentsRequest

        req = CommentsRequest(query="test")
        assert req.limit == 20

    def test_comments_request_limit_bounds(self):
        from src.mcp_services.schemas import CommentsRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            CommentsRequest(query="test", limit=0)
        with pytest.raises(ValidationError):
            CommentsRequest(query="test", limit=101)

    def test_thread_summary_request(self):
        from src.mcp_services.schemas import ThreadSummaryRequest

        req = ThreadSummaryRequest(thread_id="t1")
        assert req.thread_id == "t1"
        assert req.limit == 100

    def test_propagation_request(self):
        from src.mcp_services.schemas import PropagationRequest

        req = PropagationRequest(root_id="r1")
        assert req.root_id == "r1"
        assert req.max_depth == 10

    def test_search_request(self):
        from src.mcp_services.schemas import SearchRequest

        req = SearchRequest(query="test")
        assert req.query == "test"
        assert req.limit == 20


# ── Agent Tools (unit) ─────────────────────────────────────────────────────

class TestAgentTools:
    def test_tools_list_has_4_tools(self):
        from src.agent.tools import TOOLS

        assert len(TOOLS) == 4
        names = [t.name for t in TOOLS]
        assert "consultar_emociones" in names
        assert "consultar_resumen_hilo" in names
        assert "consultar_propagacion" in names
        assert "buscar_comentarios" in names

    def test_tools_have_descriptions(self):
        from src.agent.tools import TOOLS

        for tool in TOOLS:
            assert tool.description, f"Tool {tool.name} should have a description"

    def test_tools_have_schemas(self):
        from src.agent.tools import TOOLS

        for tool in TOOLS:
            assert tool.args_schema is not None, f"Tool {tool.name} should have args_schema"


# ── Rule-based CLI routing ─────────────────────────────────────────────────

class TestRuleBasedRouting:
    def test_extract_after_label(self):
        from src.agent.rule_based_cli import extract_after_label

        assert extract_after_label("thread_id abc123", "thread_id") == "abc123"
        assert extract_after_label("no match here", "thread_id") is None

    def test_route_emotions(self):
        from unittest.mock import patch

        with patch("src.agent.rule_based_cli.call_emotions_service") as mock:
            mock.return_value = {
                "total_comments": 3,
                "emotion_distribution": {"joy": 2, "anger": 1},
            }
            from src.agent.rule_based_cli import route_message

            result = route_message("Analiza las emociones sobre reforma laboral")
            assert "3" in result
            assert "reforma" in result.lower() or "emoci" in result.lower()

    def test_route_summary_no_id(self):
        from src.agent.rule_based_cli import route_message

        result = route_message("Resume el hilo")
        assert "thread_id" in result.lower()

    def test_route_propagation_no_id(self):
        from src.agent.rule_based_cli import route_message

        result = route_message("Analiza la propagacion")
        assert "root_id" in result.lower() or "id" in result.lower()

    def test_route_unknown(self):
        from src.agent.rule_based_cli import route_message

        result = route_message("hola que tal")
        assert "emociones" in result.lower() or "ayudar" in result.lower()


# ── MCP Client ─────────────────────────────────────────────────────────────

class TestMCPClient:
    def test_base_url(self):
        from src.agent.mcp_client import BASE_URL

        assert BASE_URL == "http://127.0.0.1:8000"

    def test_functions_exist(self):
        from src.agent import mcp_client

        assert callable(mcp_client.call_emotions_service)
        assert callable(mcp_client.call_summary_service)
        assert callable(mcp_client.call_propagation_service)
        assert callable(mcp_client.call_search_service)
