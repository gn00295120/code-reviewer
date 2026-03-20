"""REST API for DAO Governance (v3.0)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.models import AgentCompany, CompanyAgent, Proposal, Vote
from app.schemas.governance import (
    ProposalCreate,
    ProposalDetailResponse,
    ProposalListResponse,
    ProposalResponse,
    VoteCreate,
    VoteResponse,
)

# Proposals under /api/companies/{id}/proposals
company_router = APIRouter(prefix="/api/companies", tags=["governance"])
proposal_router = APIRouter(prefix="/api/proposals", tags=["governance"])

# Export both routers individually — main.py registers them directly
router = company_router  # For backward compat with main.py import


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _get_company_or_404(company_id: UUID, db: AsyncSession) -> AgentCompany:
    result = await db.execute(select(AgentCompany).where(AgentCompany.id == company_id))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Agent company not found")
    return company


async def _get_proposal_or_404(proposal_id: UUID, db: AsyncSession) -> Proposal:
    result = await db.execute(select(Proposal).where(Proposal.id == proposal_id))
    proposal = result.scalar_one_or_none()
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    return proposal


# ---------------------------------------------------------------------------
# Proposal endpoints (scoped to a company)
# ---------------------------------------------------------------------------


@company_router.post("/{company_id}/proposals", response_model=ProposalResponse, status_code=201)
async def create_proposal(
    company_id: UUID,
    payload: ProposalCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new DAO proposal for a company."""
    await _get_company_or_404(company_id, db)

    # Validate proposed_by agent if given
    if payload.proposed_by is not None:
        agent_result = await db.execute(
            select(CompanyAgent).where(
                CompanyAgent.id == payload.proposed_by,
                CompanyAgent.company_id == company_id,
            )
        )
        if agent_result.scalar_one_or_none() is None:
            raise HTTPException(status_code=404, detail="Proposing agent not found in this company")

    proposal = Proposal(
        company_id=company_id,
        title=payload.title,
        description=payload.description,
        proposal_type=payload.proposal_type,
        proposed_changes=payload.proposed_changes,
        proposed_by=payload.proposed_by,
        quorum_required=payload.quorum_required,
        deadline=payload.deadline,
        status="open",
    )
    db.add(proposal)
    await db.flush()
    return proposal


@company_router.get("/{company_id}/proposals", response_model=ProposalListResponse)
async def list_proposals(
    company_id: UUID,
    status: str | None = Query(None, description="Filter by status"),
    proposal_type: str | None = Query(None, description="Filter by proposal_type"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List proposals for a company."""
    await _get_company_or_404(company_id, db)

    query = select(Proposal).where(Proposal.company_id == company_id).order_by(Proposal.created_at.desc())

    if status:
        query = query.where(Proposal.status == status)
    if proposal_type:
        query = query.where(Proposal.proposal_type == proposal_type)

    count_q = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_q) or 0

    result = await db.execute(query.limit(limit).offset(offset))
    items = result.scalars().all()

    return ProposalListResponse(items=list(items), total=total)


# ---------------------------------------------------------------------------
# Proposal endpoints (direct, by proposal ID)
# ---------------------------------------------------------------------------


@proposal_router.get("/{proposal_id}", response_model=ProposalDetailResponse)
async def get_proposal(
    proposal_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a proposal with its votes."""
    result = await db.execute(
        select(Proposal)
        .options(selectinload(Proposal.votes))
        .where(Proposal.id == proposal_id)
    )
    proposal = result.scalar_one_or_none()
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    return proposal


@proposal_router.post("/{proposal_id}/vote", response_model=VoteResponse, status_code=201)
async def cast_vote(
    proposal_id: UUID,
    payload: VoteCreate,
    db: AsyncSession = Depends(get_db),
):
    """Cast a vote on a proposal."""
    proposal = await _get_proposal_or_404(proposal_id, db)

    if proposal.status != "open":
        raise HTTPException(
            status_code=409,
            detail=f"Proposal is not open for voting (status: {proposal.status})",
        )

    # Validate allowed vote values
    if payload.vote not in ("for", "against", "abstain"):
        raise HTTPException(status_code=422, detail="vote must be 'for', 'against', or 'abstain'")

    # Prevent duplicate votes from the same voter
    existing = await db.execute(
        select(Vote).where(
            Vote.proposal_id == proposal_id,
            Vote.voter_id == payload.voter_id,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="This agent has already voted on this proposal")

    vote = Vote(
        proposal_id=proposal_id,
        voter_id=payload.voter_id,
        vote=payload.vote,
        reason=payload.reason,
    )
    db.add(vote)

    # Update tally
    if payload.vote == "for":
        proposal.votes_for = (proposal.votes_for or 0) + 1
    elif payload.vote == "against":
        proposal.votes_against = (proposal.votes_against or 0) + 1
    # abstain does not change tally counts

    await db.flush()
    return vote


@proposal_router.post("/{proposal_id}/execute", response_model=ProposalResponse)
async def execute_proposal(
    proposal_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Execute a passed proposal."""
    proposal = await _get_proposal_or_404(proposal_id, db)

    if proposal.status != "passed":
        raise HTTPException(
            status_code=409,
            detail=f"Only passed proposals can be executed (current status: {proposal.status})",
        )

    proposal.status = "executed"
    await db.flush()
    return proposal


@proposal_router.post("/{proposal_id}/close", response_model=ProposalResponse)
async def close_proposal(
    proposal_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Close voting on a proposal, auto-determining pass/reject based on votes."""
    proposal = await _get_proposal_or_404(proposal_id, db)

    if proposal.status != "open":
        raise HTTPException(
            status_code=409,
            detail=f"Proposal is not open (current status: {proposal.status})",
        )

    total_votes = (proposal.votes_for or 0) + (proposal.votes_against or 0)
    quorum_met = total_votes >= (proposal.quorum_required or 3)

    if quorum_met and (proposal.votes_for or 0) > (proposal.votes_against or 0):
        proposal.status = "passed"
    else:
        proposal.status = "rejected"

    await db.flush()
    return proposal
