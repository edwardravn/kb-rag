from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.config import get_settings
from app.embeddings import OpenAIEmbeddingClient
from app.llm import OpenAIAnswerGenerator
from app.rag_pipeline import RagPipeline
from app.schemas import AskResponse

EVAL_DATASET_PATH = PROJECT_ROOT / "eval" / "eval_dataset.json"


def load_eval_dataset(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def normalize_text(value: str) -> str:
    normalized = value.casefold().strip()
    normalized = normalized.replace("multi-factor authentication", "mfa")
    normalized = normalized.replace("multi factor authentication", "mfa")
    normalized = normalized.replace("-", " ")
    return " ".join(normalized.split())


def extract_source_names(result: AskResponse) -> set[str]:
    sources = {chunk.source for chunk in result.chunks}
    for citation in result.citations:
        cleaned = citation.strip("[]")
        source = cleaned.split("#", 1)[0].strip()
        if source:
            sources.add(source)
    return sources


def contains_all_expected_phrases(answer: str, phrases: list[str]) -> tuple[bool, list[str]]:
    answer_norm = normalize_text(answer)
    missing = [phrase for phrase in phrases if normalize_text(phrase) not in answer_norm]
    return (len(missing) == 0, missing)


def contains_forbidden_phrases(answer: str, phrases: list[str]) -> list[str]:
    answer_norm = normalize_text(answer)
    return [phrase for phrase in phrases if normalize_text(phrase) in answer_norm]


def evaluate_case(result: AskResponse, case: dict[str, Any]) -> dict[str, Any]:
    answer = result.answer
    retrieved_sources = extract_source_names(result)
    expected_sources = set(case.get("expected_sources", []))
    expected_phrases = case.get("expected_phrases", [])
    forbidden_phrases = case.get("forbidden_phrases", [])
    warning_flags = result.grounding.warnings

    source_match = expected_sources.issubset(retrieved_sources)
    phrases_ok, missing_phrases = contains_all_expected_phrases(answer, expected_phrases)
    forbidden_found = contains_forbidden_phrases(answer, forbidden_phrases)
    passed = source_match and phrases_ok and not forbidden_found

    return {
        "question": case["question"],
        "passed": passed,
        "source_match": source_match,
        "retrieved_sources": sorted(retrieved_sources),
        "expected_sources": sorted(expected_sources),
        "phrases_ok": phrases_ok,
        "missing_phrases": missing_phrases,
        "forbidden_found": forbidden_found,
        "warning_flags": warning_flags,
        "grounded": result.grounding.grounded,
        "refusal_reason": result.grounding.refusal_reason,
        "answer": answer,
        "notes": case.get("notes", ""),
    }


def print_case_result(index: int, total: int, evaluation: dict[str, Any]) -> None:
    status = "PASS" if evaluation["passed"] else "FAIL"
    print(f"\n[{index}/{total}] {status} - {evaluation['question']}")
    if evaluation["notes"]:
        print(f"  Notes:             {evaluation['notes']}")

    print(f"  Grounded:          {evaluation['grounded']}")
    if evaluation["refusal_reason"]:
        print(f"  Refusal reason:    {evaluation['refusal_reason']}")
    print(f"  Retrieved sources: {evaluation['retrieved_sources']}")
    print(f"  Expected sources:  {evaluation['expected_sources']}")
    print(f"  Source match:      {evaluation['source_match']}")
    print(f"  Phrase check:      {evaluation['phrases_ok']}")

    if evaluation["missing_phrases"]:
        print(f"  Missing phrases:   {evaluation['missing_phrases']}")

    if evaluation["forbidden_found"]:
        print(f"  Forbidden found:   {evaluation['forbidden_found']}")

    if evaluation["warning_flags"]:
        print(f"  Warning flags:     {evaluation['warning_flags']}")

    print("  Answer preview:")
    preview = evaluation["answer"].replace("\n", " ")
    print(f"    {preview[:300]}{'...' if len(preview) > 300 else ''}")


def build_pipeline() -> RagPipeline:
    settings = get_settings()
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY must be set in the repo .env or environment.")

    embedding_client = OpenAIEmbeddingClient(
        api_key=settings.openai_api_key,
        model=settings.embedding_model,
    )
    answer_generator = OpenAIAnswerGenerator(
        api_key=settings.openai_api_key,
        model=settings.chat_model,
    )
    return RagPipeline(
        settings=settings,
        embedding_client=embedding_client,
        answer_generator=answer_generator,
    )


def main() -> None:
    if not EVAL_DATASET_PATH.exists():
        raise FileNotFoundError(f"Evaluation dataset not found: {EVAL_DATASET_PATH}")

    cases = load_eval_dataset(EVAL_DATASET_PATH)
    pipeline = build_pipeline()
    pipeline.index_documents()

    results: list[dict[str, Any]] = []
    for case in cases:
        result = pipeline.ask(case["question"])
        results.append(evaluate_case(result, case))

    passed_count = sum(1 for result in results if result["passed"])
    total_count = len(results)

    for index, evaluation in enumerate(results, start=1):
        print_case_result(index, total_count, evaluation)

    print("\n=== Evaluation Summary ===")
    print(f"Passed: {passed_count}/{total_count}")
    print(f"Failed: {total_count - passed_count}/{total_count}")

    if total_count > 0:
        score = (passed_count / total_count) * 100
        print(f"Score: {score:.1f}%")

    if passed_count != total_count:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
