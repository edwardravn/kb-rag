from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class ChunkRecord(BaseModel):
    chunk_id: str
    source: str
    source_path: str
    chunk_index: int = Field(ge=0)
    text: str
    citation: str
    char_start: int = Field(ge=0)
    char_end: int = Field(ge=0)
    token_count: int = Field(ge=0)


class RetrievedChunk(ChunkRecord):
    score: float = Field(ge=0.0, le=1.0)
    lexical_overlap: float = Field(ge=0.0, le=1.0, default=0.0)


class GroundingAssessment(BaseModel):
    grounded: bool
    weakly_grounded: bool
    warnings: list[str]
    refusal_reason: str | None = None
    top_score: float = Field(ge=0.0, le=1.0, default=0.0)
    average_score: float = Field(ge=0.0, le=1.0, default=0.0)


class RetrievalSummary(BaseModel):
    top_k_requested: int = Field(ge=1)
    chunks_returned: int = Field(ge=0)
    sources_considered: list[str]


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    top_k: int | None = Field(default=None, ge=1, le=20)

    @field_validator("question")
    @classmethod
    def strip_question(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("question must not be blank")
        return cleaned


class AskResponse(BaseModel):
    answer: str
    citations: list[str]
    chunks: list[RetrievedChunk]
    grounding: GroundingAssessment
    retrieval: RetrievalSummary


class IndexRequest(BaseModel):
    docs_dir: str | None = None
    chunk_size: int | None = Field(default=None, ge=100, le=4000)
    chunk_overlap: int | None = Field(default=None, ge=0, le=2000)


class IndexResponse(BaseModel):
    indexed_chunks: int
    documents_indexed: int
    index_name: str
    chunk_size: int = Field(ge=1)
    chunk_overlap: int = Field(ge=0)
    sources: list[str]


class HealthResponse(BaseModel):
    status: str
