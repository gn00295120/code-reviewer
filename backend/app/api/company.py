"""REST API for Self-hosting Agent Company (v3.0)."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.models import AgentCompany, CompanyAgent
from app.schemas.company import (
    AgentCompanyCreate,
    AgentCompanyDetailResponse,
    AgentCompanyListResponse,
    AgentCompanyResponse,
    AgentCompanyUpdate,
    BudgetSummaryResponse,
    CompanyAgentCreate,
    CompanyAgentResponse,
    CompanyAgentUpdate,
)

router = APIRouter(prefix="/api/companies", tags=["companies"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _get_company_or_404(company_id: UUID, db: AsyncSession) -> AgentCompany:
    result = await db.execute(select(AgentCompany).where(AgentCompany.id == company_id))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Agent company not found")
    return company


async def _get_agent_or_404(company_id: UUID, agent_id: UUID, db: AsyncSession) -> CompanyAgent:
    result = await db.execute(
        select(CompanyAgent).where(
            CompanyAgent.id == agent_id,
            CompanyAgent.company_id == company_id,
        )
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found in this company")
    return agent


# ---------------------------------------------------------------------------
# Company endpoints
# ---------------------------------------------------------------------------


@router.post("", response_model=AgentCompanyResponse, status_code=201)
async def create_company(
    payload: AgentCompanyCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new agent company."""
    company = AgentCompany(
        name=payload.name,
        description=payload.description,
        owner=payload.owner,
        org_chart=payload.org_chart,
        processes=payload.processes,
        shared_state=payload.shared_state,
        budget_usd=payload.budget_usd,
        status="draft",
    )
    db.add(company)
    await db.flush()
    return company


@router.get("", response_model=AgentCompanyListResponse)
async def list_companies(
    status: str | None = Query(None, description="Filter by status"),
    owner: str | None = Query(None, description="Filter by owner"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List all agent companies."""
    query = select(AgentCompany).order_by(AgentCompany.created_at.desc())

    if status:
        query = query.where(AgentCompany.status == status)
    if owner:
        query = query.where(AgentCompany.owner == owner)

    count_q = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_q) or 0

    result = await db.execute(query.limit(limit).offset(offset))
    items = result.scalars().all()

    return AgentCompanyListResponse(items=list(items), total=total)


@router.get("/{company_id}", response_model=AgentCompanyDetailResponse)
async def get_company(
    company_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a company with its agents."""
    result = await db.execute(
        select(AgentCompany)
        .options(selectinload(AgentCompany.agents))
        .where(AgentCompany.id == company_id)
    )
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Agent company not found")
    return company


@router.put("/{company_id}", response_model=AgentCompanyResponse)
async def update_company(
    company_id: UUID,
    payload: AgentCompanyUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update an agent company."""
    company = await _get_company_or_404(company_id, db)

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(company, field, value)

    await db.flush()
    return company


@router.post("/{company_id}/activate", response_model=AgentCompanyResponse)
async def activate_company(
    company_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Activate an agent company."""
    company = await _get_company_or_404(company_id, db)

    if company.status == "active":
        raise HTTPException(status_code=409, detail="Company is already active")
    if company.status == "archived":
        raise HTTPException(status_code=409, detail="Cannot activate an archived company")

    company.status = "active"
    await db.flush()
    return company


@router.post("/{company_id}/pause", response_model=AgentCompanyResponse)
async def pause_company(
    company_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Pause an active agent company."""
    company = await _get_company_or_404(company_id, db)

    if company.status != "active":
        raise HTTPException(
            status_code=409,
            detail=f"Company is not active (current status: {company.status})",
        )

    company.status = "paused"
    await db.flush()
    return company


@router.get("/{company_id}/budget", response_model=BudgetSummaryResponse)
async def get_budget(
    company_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get budget and spend summary for a company."""
    company = await _get_company_or_404(company_id, db)

    budget = Decimal(str(company.budget_usd)) if company.budget_usd else Decimal("0")
    spent = Decimal(str(company.spent_usd)) if company.spent_usd else Decimal("0")
    remaining = budget - spent
    utilization = float(spent / budget * 100) if budget > 0 else 0.0

    return BudgetSummaryResponse(
        company_id=company_id,
        budget_usd=budget,
        spent_usd=spent,
        remaining_usd=remaining,
        utilization_pct=round(utilization, 2),
    )


# ---------------------------------------------------------------------------
# Agent endpoints
# ---------------------------------------------------------------------------


@router.post("/{company_id}/agents", response_model=CompanyAgentResponse, status_code=201)
async def add_agent(
    company_id: UUID,
    payload: CompanyAgentCreate,
    db: AsyncSession = Depends(get_db),
):
    """Add an agent to a company."""
    company = await _get_company_or_404(company_id, db)

    # Validate reports_to if provided
    if payload.reports_to is not None:
        manager_result = await db.execute(
            select(CompanyAgent).where(
                CompanyAgent.id == payload.reports_to,
                CompanyAgent.company_id == company_id,
            )
        )
        if manager_result.scalar_one_or_none() is None:
            raise HTTPException(status_code=404, detail="reports_to agent not found in this company")

    agent = CompanyAgent(
        company_id=company_id,
        role=payload.role,
        title=payload.title,
        model=payload.model,
        system_prompt=payload.system_prompt,
        capabilities=payload.capabilities,
        reports_to=payload.reports_to,
        status="idle",
    )
    db.add(agent)

    # Increment company agent count
    company.agent_count = (company.agent_count or 0) + 1
    await db.flush()
    return agent


@router.get("/{company_id}/agents", response_model=list[CompanyAgentResponse])
async def list_agents(
    company_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """List all agents in a company."""
    await _get_company_or_404(company_id, db)

    result = await db.execute(
        select(CompanyAgent)
        .where(CompanyAgent.company_id == company_id)
        .order_by(CompanyAgent.created_at)
    )
    return result.scalars().all()


@router.put("/{company_id}/agents/{agent_id}", response_model=CompanyAgentResponse)
async def update_agent(
    company_id: UUID,
    agent_id: UUID,
    payload: CompanyAgentUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update an agent in a company."""
    agent = await _get_agent_or_404(company_id, agent_id, db)

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(agent, field, value)

    await db.flush()
    return agent


@router.delete("/{company_id}/agents/{agent_id}", status_code=204)
async def remove_agent(
    company_id: UUID,
    agent_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Remove an agent from a company."""
    company = await _get_company_or_404(company_id, db)
    agent = await _get_agent_or_404(company_id, agent_id, db)

    await db.delete(agent)

    # Decrement company agent count
    company.agent_count = max(0, (company.agent_count or 1) - 1)
    await db.flush()
