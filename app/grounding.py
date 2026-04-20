from __future__ import annotations

import re

from app.schemas import GroundingAssessment, RetrievedChunk
from app.security import (
    GROUNDING_WARNING_LOW_EVIDENCE,
    GROUNDING_WARNING_LOW_OVERLAP,
    GROUNDING_WARNING_SINGLE_SOURCE,
)


def assess_grounding(
    chunks: list[RetrievedChunk],
    min_top_score: float,
    min_average_score: float,
    min_lexical_overlap: float,
) -> GroundingAssessment:
    if not chunks:
        return GroundingAssessment(
            grounded=False,
            weakly_grounded=True,
            warnings=[GROUNDING_WARNING_LOW_EVIDENCE],
            refusal_reason="no_retrieved_chunks",
            top_score=0.0,
            average_score=0.0,
        )

    top_score = chunks[0].score
    average_score = sum(chunk.score for chunk in chunks) / len(chunks)
    warnings: list[str] = []
    weakly_grounded = False
    refusal_reason: str | None = None

    # These checks are intentionally heuristic rather than model-based. They
    # make the refusal path easy to inspect and discuss in an interview.
    if top_score < min_top_score or average_score < min_average_score:
        warnings.append(GROUNDING_WARNING_LOW_EVIDENCE)
        weakly_grounded = True
        refusal_reason = "retrieval_scores_below_threshold"

    if max(chunk.lexical_overlap for chunk in chunks) < min_lexical_overlap:
        warnings.append(GROUNDING_WARNING_LOW_OVERLAP)
        weakly_grounded = True
        refusal_reason = refusal_reason or "low_question_context_overlap"

    if len({chunk.source for chunk in chunks}) == 1:
        warnings.append(GROUNDING_WARNING_SINGLE_SOURCE)

    grounded = refusal_reason is None
    return GroundingAssessment(
        grounded=grounded,
        weakly_grounded=weakly_grounded,
        warnings=warnings,
        refusal_reason=refusal_reason,
        top_score=top_score,
        average_score=average_score,
    )


def extract_citations(text: str) -> list[str]:
    return re.findall(r"\[[^\]]+\]", text)
