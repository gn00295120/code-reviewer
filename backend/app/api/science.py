"""REST API for AI Science Engine (v3.0)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.models import Experiment, ExperimentRun
from app.schemas.science import (
    ExperimentCreate,
    ExperimentDetailResponse,
    ExperimentListResponse,
    ExperimentResponse,
    ExperimentRunCreate,
    ExperimentRunResponse,
)

router = APIRouter(prefix="/api/experiments", tags=["science"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _get_experiment_or_404(experiment_id: UUID, db: AsyncSession) -> Experiment:
    result = await db.execute(select(Experiment).where(Experiment.id == experiment_id))
    experiment = result.scalar_one_or_none()
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return experiment


# ---------------------------------------------------------------------------
# Experiment endpoints
# ---------------------------------------------------------------------------


@router.post("", response_model=ExperimentResponse, status_code=201)
async def create_experiment(
    payload: ExperimentCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new experiment."""
    experiment = Experiment(
        company_id=payload.company_id,
        title=payload.title,
        hypothesis=payload.hypothesis,
        methodology=payload.methodology,
        variables=payload.variables,
        status="draft",
    )
    db.add(experiment)
    await db.flush()
    return experiment


@router.get("", response_model=ExperimentListResponse)
async def list_experiments(
    status: str | None = Query(None, description="Filter by status"),
    company_id: UUID | None = Query(None, description="Filter by company_id"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List all experiments."""
    query = select(Experiment).order_by(Experiment.created_at.desc())

    if status:
        query = query.where(Experiment.status == status)
    if company_id:
        query = query.where(Experiment.company_id == company_id)

    count_q = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_q) or 0

    result = await db.execute(query.limit(limit).offset(offset))
    items = result.scalars().all()

    return ExperimentListResponse(items=list(items), total=total)


@router.get("/{experiment_id}", response_model=ExperimentDetailResponse)
async def get_experiment(
    experiment_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get an experiment with all its runs."""
    result = await db.execute(
        select(Experiment)
        .options(selectinload(Experiment.runs))
        .where(Experiment.id == experiment_id)
    )
    experiment = result.scalar_one_or_none()
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return experiment


@router.post("/{experiment_id}/run", response_model=ExperimentRunResponse, status_code=201)
async def start_run(
    experiment_id: UUID,
    payload: ExperimentRunCreate | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Start a new experiment run."""
    experiment = await _get_experiment_or_404(experiment_id, db)

    if experiment.status == "published":
        raise HTTPException(status_code=409, detail="Cannot add runs to a published experiment")

    # Compute next run number
    count_result = await db.execute(
        select(func.count()).select_from(
            select(ExperimentRun).where(ExperimentRun.experiment_id == experiment_id).subquery()
        )
    )
    run_number = (count_result.scalar() or 0) + 1

    run = ExperimentRun(
        experiment_id=experiment_id,
        run_number=run_number,
        parameters=payload.parameters if payload else {},
        status="pending",
    )
    db.add(run)

    # Update experiment status and run count
    if experiment.status == "draft":
        experiment.status = "running"
    experiment.total_runs = (experiment.total_runs or 0) + 1

    await db.flush()
    return run


@router.get("/{experiment_id}/runs", response_model=list[ExperimentRunResponse])
async def list_runs(
    experiment_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """List all runs for an experiment."""
    await _get_experiment_or_404(experiment_id, db)

    result = await db.execute(
        select(ExperimentRun)
        .where(ExperimentRun.experiment_id == experiment_id)
        .order_by(ExperimentRun.run_number)
    )
    return result.scalars().all()


@router.post("/{experiment_id}/analyze", response_model=ExperimentResponse)
async def analyze_experiment(
    experiment_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Trigger AI analysis on an experiment's results."""
    experiment = await _get_experiment_or_404(experiment_id, db)

    if experiment.status not in ("running", "completed"):
        raise HTTPException(
            status_code=409,
            detail=f"Analysis requires status 'running' or 'completed' (current: {experiment.status})",
        )

    experiment.status = "analyzing"
    # Placeholder: real implementation would enqueue an AI analysis task
    experiment.analysis = "Analysis pending — AI task enqueued."
    await db.flush()
    return experiment


@router.post("/{experiment_id}/publish", response_model=ExperimentResponse)
async def publish_experiment(
    experiment_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Mark an experiment as published."""
    experiment = await _get_experiment_or_404(experiment_id, db)

    if experiment.status not in ("completed", "analyzing"):
        raise HTTPException(
            status_code=409,
            detail=f"Only completed or analyzed experiments can be published (current: {experiment.status})",
        )

    experiment.status = "published"
    await db.flush()
    return experiment
