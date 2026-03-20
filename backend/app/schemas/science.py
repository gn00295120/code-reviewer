"""Pydantic schemas for AI Science Engine API (v3.0)."""

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class ExperimentCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=256)
    hypothesis: str | None = None
    methodology: dict[str, Any] = Field(default_factory=dict)
    variables: dict[str, Any] = Field(default_factory=dict)
    company_id: UUID | None = None


class ExperimentRunCreate(BaseModel):
    parameters: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class ExperimentRunResponse(BaseModel):
    id: UUID
    experiment_id: UUID
    run_number: int
    parameters: dict[str, Any]
    results: dict[str, Any]
    metrics: dict[str, Any]
    status: str
    duration_seconds: float
    cost_usd: Decimal
    created_at: datetime

    model_config = {"from_attributes": True}


class ExperimentResponse(BaseModel):
    id: UUID
    company_id: UUID | None
    title: str
    hypothesis: str | None
    methodology: dict[str, Any]
    status: str
    variables: dict[str, Any]
    results: dict[str, Any]
    analysis: str | None
    conclusion: str | None
    confidence: float
    total_runs: int
    total_cost_usd: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ExperimentDetailResponse(ExperimentResponse):
    runs: list[ExperimentRunResponse] = []


class ExperimentListResponse(BaseModel):
    items: list[ExperimentResponse]
    total: int
