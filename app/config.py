from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    embedding_model: str = Field(default="text-embedding-3-small", alias="RAG_EMBEDDING_MODEL")
    chat_model: str = Field(default="gpt-4.1-mini", alias="RAG_CHAT_MODEL")
    docs_dir: Path = Field(default=Path("sample_docs"), alias="RAG_DOCS_DIR")
    vector_store_dir: Path = Field(
        default=Path("vector_store"),
        validation_alias=AliasChoices("RAG_VECTOR_STORE_DIR", "RAG_CHROMA_DIR"),
    )
    index_name: str = Field(
        default="policy_chunks",
        validation_alias=AliasChoices("RAG_INDEX_NAME", "RAG_COLLECTION_NAME"),
    )
    chunk_size: int = Field(default=800, alias="RAG_CHUNK_SIZE")
    chunk_overlap: int = Field(default=120, alias="RAG_CHUNK_OVERLAP")
    top_k: int = Field(default=4, alias="RAG_TOP_K")
    min_similarity: float = Field(default=0.3, alias="RAG_MIN_SIMILARITY")
    min_average_similarity: float = Field(default=0.18, alias="RAG_MIN_AVG_SIMILARITY")
    min_lexical_overlap: float = Field(default=0.05, alias="RAG_MIN_LEXICAL_OVERLAP")
    max_question_chars: int = Field(default=2000, alias="RAG_MAX_QUESTION_CHARS")
    max_chunk_chars: int = Field(default=4000, alias="RAG_MAX_CHUNK_CHARS")
    log_level: str = Field(default="INFO", alias="RAG_LOG_LEVEL")

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        populate_by_name=True,
        extra="ignore",
    )

    @model_validator(mode="after")
    def resolve_paths(self) -> "Settings":
        if not self.docs_dir.is_absolute():
            self.docs_dir = PROJECT_ROOT / self.docs_dir
        if not self.vector_store_dir.is_absolute():
            self.vector_store_dir = PROJECT_ROOT / self.vector_store_dir
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
