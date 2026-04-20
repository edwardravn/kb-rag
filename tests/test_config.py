from pathlib import Path

from app.config import PROJECT_ROOT, Settings


def test_settings_resolve_relative_paths_from_project_root() -> None:
    settings = Settings(
        OPENAI_API_KEY="test-key",
        RAG_DOCS_DIR=Path("sample_docs"),
        RAG_VECTOR_STORE_DIR=Path("vector_store"),
    )

    assert settings.docs_dir == PROJECT_ROOT / "sample_docs"
    assert settings.vector_store_dir == PROJECT_ROOT / "vector_store"
