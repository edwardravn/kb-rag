from __future__ import annotations

import math
import re
from collections.abc import Iterable

from openai import OpenAI


class OpenAIEmbeddingClient:
    def __init__(self, api_key: str, model: str) -> None:
        self._client = OpenAI(api_key=api_key)
        self._model = model

    def embed_texts(self, texts: Iterable[str]) -> list[list[float]]:
        items = list(texts)
        if not items:
            return []
        response = self._client.embeddings.create(model=self._model, input=items)
        return [list(item.embedding) for item in response.data]


class SimpleTokenEmbeddingClient:
    """Deterministic local embedder for tests and offline debugging."""

    def __init__(self, dimensions: int = 64) -> None:
        self._dimensions = dimensions

    def embed_texts(self, texts: Iterable[str]) -> list[list[float]]:
        return [self._embed_single(text) for text in texts]

    def _embed_single(self, text: str) -> list[float]:
        vector = [0.0] * self._dimensions
        tokens = re.findall(r"[a-z0-9]+", text.lower())
        if not tokens:
            return vector

        for token in tokens:
            index = hash(token) % self._dimensions
            vector[index] += 1.0

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]
