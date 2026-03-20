"""Pydantic schemas for Self-hosting Agent Company API (v3.0)."""

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class AgentCompanyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=256)
    description: str | None = None
    owner: str | None = None
    org_chart: dict[str, Any] = Field(default_factory=dict)
    processes: list[Any] = Field(default_factory=list)
    shared_state: dict[str, Any] = Field(default_factory=dict)
    budget_usd: Decimal = Field(default=Decimal("0"), ge=0)


class AgentCompanyUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=256)
    description: str | None = None
    owner: str | None = None
    org_chart: dict[str, Any] | None = None
    processes: list[Any] | None = None
    shared_state: dict[str, Any] | None = None
    budget_usd: Decimal | None = Field(None, ge=0)


class CompanyAgentCreate(BaseModel):
    role: str = Field(..., min_length=1, max_length=128)
    title: str | None = Field(None, max_length=256)
    model: str = Field("claude-sonnet", max_length=128)
    system_prompt: str | None = None
    capabilities: list[Any] = Field(default_factory=list)
    reports_to: UUID | None = None


class CompanyAgentUpdate(BaseModel):
    role: str | None = Field(None, min_length=1, max_length=128)
    title: str | None = Field(None, max_length=256)
    model: str | None = Field(None, max_length=128)
    system_prompt: str | None = None
    capabilities: list[Any] | None = None
    reports_to: UUID | None = None
    status: str | None = None


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class CompanyAgentResponse(BaseModel):
    id: UUID
    company_id: UUID
    role: str
    title: str | None
    model: str
    system_prompt: str | None
    capabilities: list[Any]
    reports_to: UUID | None
    status: str
    total_tasks: int
    total_cost_usd: Decimal
    created_at: datetime

    model_config = {"from_attributes": True}


class AgentCompanyResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    owner: str | None
    org_chart: dict[str, Any]
    processes: list[Any]
    shared_state: dict[str, Any]
    budget_usd: Decimal
    spent_usd: Decimal
    status: str
    agent_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AgentCompanyDetailResponse(AgentCompanyResponse):
    agents: list[CompanyAgentResponse] = []


class AgentCompanyListResponse(BaseModel):
    items: list[AgentCompanyResponse]
    total: int


class BudgetSummaryResponse(BaseModel):
    company_id: UUID
    budget_usd: Decimal
    spent_usd: Decimal
    remaining_usd: Decimal
    utilization_pct: float
