from __future__ import annotations

from pathlib import Path

from app.chunking import TextChunker
from app.config import Settings
from app.grounding import assess_grounding, extract_citations
from app.ingestion import load_documents
from app.prompts import build_messages
from app.retrieval import Retriever
from app.schemas import (
    AskResponse,
    ChunkRecord,
    GroundingAssessment,
    IndexResponse,
    RetrievedChunk,
    RetrievalSummary,
)
from app.security import (
    GROUNDING_WARNING_INVALID_CITATIONS,
    GROUNDING_WARNING_NO_CITATIONS,
    GROUNDING_WARNING_SUSPICIOUS_FILTERED,
    INSUFFICIENT_CONTEXT_MESSAGE,
    is_suspicious_chunk,
)
from app.vector_store import FaissVectorStore


class RagPipeline:
    def __init__(
        self,
        settings: Settings,
        embedding_client: object,
        answer_generator: object | None = None,
        vector_store: FaissVectorStore | None = None,
    ) -> None:
        self._settings = settings
        self._chunker = TextChunker(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            max_chunk_chars=settings.max_chunk_chars,
        )
        self._embedding_client = embedding_client
        self._answer_generator = answer_generator
        self._vector_store = vector_store or FaissVectorStore(
            persist_dir=settings.vector_store_dir,
            index_name=settings.index_name,
        )
        self._retriever = Retriever(
            vector_store=self._vector_store,
            embedding_client=embedding_client,
        )

    @property
    def vector_store(self) -> FaissVectorStore:
        return self._vector_store

    def index_documents(
        self,
        docs_dir: Path | None = None,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
    ) -> IndexResponse:
        resolved_docs_dir = docs_dir or self._settings.docs_dir
        active_chunker = TextChunker(
            chunk_size=chunk_size or self._settings.chunk_size,
            chunk_overlap=chunk_overlap if chunk_overlap is not None else self._settings.chunk_overlap,
            max_chunk_chars=self._settings.max_chunk_chars,
        )
        documents = load_documents(resolved_docs_dir)

        chunks: list[ChunkRecord] = []
        indexed_sources: list[str] = []
        for source, source_path, text in documents:
            indexed_sources.append(source_path)
            chunks.extend(active_chunker.chunk_text(text=text, source=source, source_path=source_path))

        embeddings = self._embedding_client.embed_texts(chunk.text for chunk in chunks)
        self._vector_store.reset()
        self._vector_store.add_chunks(chunks=chunks, embeddings=embeddings)

        return IndexResponse(
            indexed_chunks=len(chunks),
            documents_indexed=len(documents),
            index_name=self._vector_store.index_name,
            chunk_size=active_chunker.chunk_size,
            chunk_overlap=active_chunker.chunk_overlap,
            sources=indexed_sources,
        )

    def ask(self, question: str, top_k: int | None = None) -> AskResponse:
        cleaned_question = question.strip()
        if not cleaned_question:
            raise ValueError("question must not be blank")
        if len(cleaned_question) > self._settings.max_question_chars:
            raise ValueError(
                f"question exceeds max length of {self._settings.max_question_chars} characters"
            )

        effective_top_k = top_k or self._settings.top_k
        retrieved_chunks = self._retriever.retrieve(question=cleaned_question, top_k=effective_top_k)
        chunks, suspicious_filtered = self._select_context_chunks(retrieved_chunks)
        grounding = assess_grounding(
            chunks=chunks,
            min_top_score=self._settings.min_similarity,
            min_average_score=self._settings.min_average_similarity,
            min_lexical_overlap=self._settings.min_lexical_overlap,
        )
        if suspicious_filtered:
            grounding = grounding.model_copy(
                update={"warnings": [*grounding.warnings, GROUNDING_WARNING_SUSPICIOUS_FILTERED]}
            )

        if not grounding.grounded:
            return self._build_fallback_response(chunks=chunks, grounding=grounding, top_k=effective_top_k)

        if self._answer_generator is None:
            raise RuntimeError("Answer generation is not configured")

        messages = build_messages(question=cleaned_question, chunks=chunks)
        answer = self._answer_generator.generate(messages=messages)
        return self._build_grounded_response(answer=answer, chunks=chunks, grounding=grounding, top_k=effective_top_k)

    def inspect_retrieval(self, question: str, top_k: int | None = None) -> RetrievalSummary | AskResponse:
        return self.ask(question=question, top_k=top_k)

    def _build_fallback_response(
        self,
        chunks: list[RetrievedChunk],
        grounding: GroundingAssessment,
        top_k: int,
    ) -> AskResponse:
        return AskResponse(
            answer=INSUFFICIENT_CONTEXT_MESSAGE,
            citations=[],
            chunks=chunks,
            grounding=grounding,
            retrieval=self._build_retrieval_summary(chunks=chunks, top_k=top_k),
        )

    def _build_grounded_response(
        self,
        answer: str,
        chunks: list[RetrievedChunk],
        grounding: GroundingAssessment,
        top_k: int,
    ) -> AskResponse:
        allowed_citations = [chunk.citation for chunk in chunks]
        answer_citations = extract_citations(answer)
        warnings = list(grounding.warnings)

        if not answer_citations:
            warnings.append(GROUNDING_WARNING_NO_CITATIONS)
            # We preserve the model's text, but add explicit sources so the
            # caller still gets a grounded, inspectable response shape.
            answer = f"{answer}\n\nSources: {', '.join(allowed_citations)}"
            answer_citations = allowed_citations

        if any(citation not in allowed_citations for citation in answer_citations):
            warnings.append(GROUNDING_WARNING_INVALID_CITATIONS)
            # If the model emits citations we did not retrieve, replace them
            # with the validated set rather than returning misleading evidence.
            answer = f"{_strip_citations(answer)}\n\nSources: {', '.join(allowed_citations)}"
            answer_citations = allowed_citations

        final_grounding = grounding.model_copy(update={"warnings": warnings})
        return AskResponse(
            answer=answer,
            citations=allowed_citations,
            chunks=chunks,
            grounding=final_grounding,
            retrieval=self._build_retrieval_summary(chunks=chunks, top_k=top_k),
        )

    @staticmethod
    def _build_retrieval_summary(chunks: list[RetrievedChunk], top_k: int) -> RetrievalSummary:
        return RetrievalSummary(
            top_k_requested=top_k,
            chunks_returned=len(chunks),
            sources_considered=sorted({chunk.source for chunk in chunks}),
        )

    @staticmethod
    def _select_context_chunks(chunks: list[RetrievedChunk]) -> tuple[list[RetrievedChunk], bool]:
        trusted_chunks = [
            chunk for chunk in chunks if not is_suspicious_chunk(source=chunk.source, text=chunk.text)
        ]
        if trusted_chunks and len(trusted_chunks) != len(chunks):
            return trusted_chunks, True
        return chunks, False


def _strip_citations(text: str) -> str:
    for citation in extract_citations(text):
        text = text.replace(citation, "")
    return " ".join(text.split())
