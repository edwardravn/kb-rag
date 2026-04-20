from __future__ import annotations

from openai import OpenAI


class OpenAIAnswerGenerator:
    def __init__(self, api_key: str, model: str) -> None:
        self._client = OpenAI(api_key=api_key)
        self._model = model

    def generate(self, messages: list[dict[str, str]]) -> str:
        response = self._client.responses.create(model=self._model, input=messages)
        return response.output_text.strip()
