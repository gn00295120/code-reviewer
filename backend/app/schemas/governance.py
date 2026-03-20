"""Pydantic schemas for DAO Governance API (v3.0)."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class ProposalCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=256)
    description: str | None = None
    proposal_type: str = Field(..., description="budget | role_change | process | policy")
    proposed_changes: dict[str, Any] = Field(default_factory=dict)
    proposed_by: UUID | None = None
    quorum_required: int = Field(3, ge=1)
    deadline: datetime | None = None


class VoteCreate(BaseModel):
    voter_id: UUID
    vote: str = Field(..., description="for | against | abstain")
    reason: str | None = None


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class VoteResponse(BaseModel):
    id: UUID
    proposal_id: UUID
    voter_id: UUID
    vote: str
    reason: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ProposalResponse(BaseModel):
    id: UUID
    company_id: UUID
    title: str
    description: str | None
    proposal_type: str
    proposed_changes: dict[str, Any]
    proposed_by: UUID | None
    status: str
    votes_for: int
    votes_against: int
    quorum_required: int
    deadline: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ProposalDetailResponse(ProposalResponse):
    votes: list[VoteResponse] = []


class ProposalListResponse(BaseModel):
    items: list[ProposalResponse]
    total: int
