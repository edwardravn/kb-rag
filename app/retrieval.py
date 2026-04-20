from __future__ import annotations

import re
from dataclasses import dataclass

from app.schemas import RetrievedChunk
from app.vector_store import FaissVectorStore


def _tokenize(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9]+", text.lower()) if len(token) > 1}


@dataclass(slots=True)
class Retriever:
    vector_store: FaissVectorStore
    embedding_client: object

    def retrieve(self, question: str, top_k: int) -> list[RetrievedChunk]:
        embeddings = self.embedding_client.embed_texts([question])
        if not embeddings:
            return []

        # Pull a slightly wider candidate set first, then rerank locally.
        # This keeps the implementation simple while improving explainability
        # for policy-style questions where a small lexical signal matters.
        chunks = self.vector_store.query(query_embedding=embeddings[0], top_k=max(top_k * 2, top_k))
        question_tokens = _tokenize(question)
        reranked: list[RetrievedChunk] = []
        for chunk in chunks:
            chunk_tokens = _tokenize(chunk.text)
            overlap = len(question_tokens & chunk_tokens) / max(len(question_tokens), 1)
            combined_score = (0.8 * chunk.score) + (0.2 * overlap)
            reranked.append(chunk.model_copy(update={"score": combined_score, "lexical_overlap": overlap}))

        reranked.sort(key=lambda item: item.score, reverse=True)
        return reranked[:top_k]
