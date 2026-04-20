from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.embeddings import SimpleTokenEmbeddingClient
from app.main import create_app
from app.rag_pipeline import RagPipeline
from app.security import GROUNDING_WARNING_SINGLE_SOURCE, INSUFFICIENT_CONTEXT_MESSAGE


class FakeAnswerGenerator:
    def generate(self, messages: list[dict[str, str]]) -> str:
        return "Privileged accounts require multi-factor authentication. [password_policy.md#chunk_0]"


def build_test_app(tmp_path: Path) -> TestClient:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "password_policy.md").write_text(
        "Privileged accounts must use multi-factor authentication.",
        encoding="utf-8",
    )

    settings = Settings(
        OPENAI_API_KEY="test-key",
        RAG_DOCS_DIR=docs_dir,
        RAG_VECTOR_STORE_DIR=tmp_path / "vector_store",
        RAG_CHUNK_SIZE=120,
        RAG_CHUNK_OVERLAP=20,
        RAG_TOP_K=2,
        RAG_MIN_SIMILARITY=0.2,
        RAG_MIN_AVG_SIMILARITY=0.1,
        RAG_MIN_LEXICAL_OVERLAP=0.02,
    )
    pipeline = RagPipeline(
        settings=settings,
        embedding_client=SimpleTokenEmbeddingClient(dimensions=256),
        answer_generator=FakeAnswerGenerator(),
    )
    app = create_app(settings=settings, pipeline=pipeline)
    return TestClient(app)


def test_health_endpoint(tmp_path: Path) -> None:
    client = build_test_app(tmp_path)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ask_endpoint_returns_grounded_answer_with_warnings_and_citations(tmp_path: Path) -> None:
    client = build_test_app(tmp_path)
    client.post("/index", json={})

    response = client.post("/ask", json={"question": "What is required for privileged accounts?"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["grounding"]["grounded"] is True
    assert GROUNDING_WARNING_SINGLE_SOURCE in payload["grounding"]["warnings"]
    assert payload["citations"] == ["[password_policy.md#chunk_0]"]
    assert payload["chunks"][0]["source_path"] == "password_policy.md"
    assert "retrieval" in payload


def test_ask_endpoint_refuses_when_context_is_insufficient(tmp_path: Path) -> None:
    client = build_test_app(tmp_path)
    client.post("/index", json={})

    response = client.post("/ask", json={"question": "What is the travel reimbursement policy?"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["grounding"]["grounded"] is False
    assert payload["answer"] == INSUFFICIENT_CONTEXT_MESSAGE


def test_ask_endpoint_rejects_blank_question(tmp_path: Path) -> None:
    client = build_test_app(tmp_path)

    response = client.post("/ask", json={"question": "   "})

    assert response.status_code == 422


def test_index_endpoint_allows_chunk_overrides(tmp_path: Path) -> None:
    client = build_test_app(tmp_path)

    response = client.post("/index", json={"chunk_size": 150, "chunk_overlap": 30})

    assert response.status_code == 200
    payload = response.json()
    assert payload["chunk_size"] == 150
    assert payload["chunk_overlap"] == 30
