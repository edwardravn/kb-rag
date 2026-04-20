from __future__ import annotations

import json
from pathlib import Path

import faiss
import numpy as np

from app.schemas import ChunkRecord, RetrievedChunk


class FaissVectorStore:
    def __init__(self, persist_dir: Path, index_name: str) -> None:
        self._persist_dir = persist_dir
        self._persist_dir.mkdir(parents=True, exist_ok=True)
        self._index_name = index_name
        self._index_path = self._persist_dir / f"{index_name}.faiss"
        self._metadata_path = self._persist_dir / f"{index_name}.json"
        self._index: faiss.IndexFlatIP | None = None
        self._metadata: list[dict[str, object]] = []

    @property
    def index_name(self) -> str:
        return self._index_name

    def reset(self) -> None:
        self._index = None
        self._metadata = []
        if self._index_path.exists():
            self._index_path.unlink()
        if self._metadata_path.exists():
            self._metadata_path.unlink()

    def add_chunks(self, chunks: list[ChunkRecord], embeddings: list[list[float]]) -> None:
        if len(chunks) != len(embeddings):
            raise ValueError("chunks and embeddings must be the same length")
        if not chunks:
            return

        matrix = np.array(embeddings, dtype="float32")
        self._normalize(matrix)
        dimensions = int(matrix.shape[1])
        self._index = faiss.IndexFlatIP(dimensions)
        self._index.add(matrix)
        self._metadata = [chunk.model_dump() for chunk in chunks]
        faiss.write_index(self._index, str(self._index_path))
        self._metadata_path.write_text(
            json.dumps(self._metadata, ensure_ascii=True, indent=2),
            encoding="utf-8",
        )

    def query(self, query_embedding: list[float], top_k: int) -> list[RetrievedChunk]:
        self._ensure_loaded()
        if self._index is None or not self._metadata:
            return []

        vector = np.array([query_embedding], dtype="float32")
        self._normalize(vector)
        limit = min(top_k, len(self._metadata))
        scores, indices = self._index.search(vector, limit)

        retrieved: list[RetrievedChunk] = []
        for score, index in zip(scores[0], indices[0], strict=False):
            if index < 0:
                continue
            metadata = self._metadata[int(index)]
            retrieved.append(
                RetrievedChunk(
                    **metadata,
                    score=max(0.0, min(1.0, float(score))),
                    lexical_overlap=0.0,
                )
            )
        return retrieved

    def _ensure_loaded(self) -> None:
        if self._index is None and self._index_path.exists():
            self._index = faiss.read_index(str(self._index_path))
        if not self._metadata and self._metadata_path.exists():
            self._metadata = json.loads(self._metadata_path.read_text(encoding="utf-8"))

    @staticmethod
    def _normalize(matrix: np.ndarray) -> None:
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms[norms == 0.0] = 1.0
        matrix /= norms
