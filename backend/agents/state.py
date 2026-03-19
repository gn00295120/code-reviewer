"""LangGraph state definition for the review pipeline."""

import operator
from typing import Annotated, TypedDict


class ReviewState(TypedDict):
    """Shared state across all review agents."""

    # Input
    review_id: str
    pr_diff: dict  # Serialized PRDiff
    files: list[dict]  # Individual file diffs

    # Agent outputs (accumulated via reducer)
    findings: Annotated[list[dict], operator.add]

    # Cost tracking (accumulated via reducer)
    total_tokens: Annotated[int, operator.add]
    total_cost_usd: Annotated[float, operator.add]

    # Supervisor output (last-write-wins, no reducer needed)
    deduplicated_findings: list[dict]
    summary: str
    severity_counts: dict  # {"high": N, "medium": N, "low": N}

    # Control
    error: str | None
