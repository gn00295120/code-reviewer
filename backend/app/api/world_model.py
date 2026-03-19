"""REST API router for the World Model Sandbox."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.models import PhysicsEvent, WorldModel
from app.schemas.world_model import (
    PhysicsEventListResponse,
    PhysicsEventResponse,
    StepAction,
    WorldModelCreate,
    WorldModelDetailResponse,
    WorldModelListResponse,
    WorldModelResponse,
)

router = APIRouter(prefix="/api/world-models", tags=["world-models"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _get_or_404(model_id: UUID, db: AsyncSession) -> WorldModel:
    result = await db.execute(
        select(WorldModel).where(WorldModel.id == model_id)
    )
    wm = result.scalar_one_or_none()
    if not wm:
        raise HTTPException(status_code=404, detail="WorldModel not found")
    return wm


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("", response_model=WorldModelResponse, status_code=201)
async def create_world_model(
    payload: WorldModelCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new world model sandbox."""
    wm = WorldModel(
        name=payload.name,
        description=payload.description,
        mujoco_xml=payload.mujoco_xml,
        model_type=payload.model_type,
        agent_config=payload.agent_config,
        current_state={},
        status="idle",
    )
    db.add(wm)
    await db.flush()
    return wm


@router.get("", response_model=WorldModelListResponse)
async def list_world_models(
    status: str | None = Query(None, description="Filter by status"),
    model_type: str | None = Query(None, description="Filter by model_type"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List all world model sandboxes."""
    query = select(WorldModel).order_by(WorldModel.created_at.desc())

    if status:
        query = query.where(WorldModel.status == status)
    if model_type:
        query = query.where(WorldModel.model_type == model_type)

    count_q = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_q)

    result = await db.execute(query.limit(limit).offset(offset))
    items = result.scalars().all()

    return WorldModelListResponse(items=list(items), total=total)


@router.get("/{model_id}", response_model=WorldModelDetailResponse)
async def get_world_model(
    model_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a world model with its 20 most recent physics events."""
    result = await db.execute(
        select(WorldModel)
        .options(
            selectinload(WorldModel.events)
        )
        .where(WorldModel.id == model_id)
    )
    wm = result.scalar_one_or_none()
    if not wm:
        raise HTTPException(status_code=404, detail="WorldModel not found")

    # Sort and limit events in Python to avoid complex subquery
    recent_events = sorted(wm.events, key=lambda e: e.step, reverse=True)[:20]
    recent_events.reverse()  # chronological order

    response = WorldModelDetailResponse.model_validate(wm)
    response.recent_events = [PhysicsEventResponse.model_validate(e) for e in recent_events]
    return response


@router.post("/{model_id}/start", response_model=WorldModelResponse)
async def start_simulation(
    model_id: UUID,
    max_steps: int = Query(100, ge=1, le=10_000, description="Maximum simulation steps"),
    db: AsyncSession = Depends(get_db),
):
    """Start the simulation (enqueues a Celery task)."""
    wm = await _get_or_404(model_id, db)

    if wm.status == "running":
        raise HTTPException(status_code=409, detail="Simulation is already running")

    if wm.status in ("completed", "error"):
        raise HTTPException(
            status_code=409,
            detail=f"Cannot start a simulation in '{wm.status}' state. Reset first.",
        )

    # Late import to avoid circular deps at module load time
    from app.tasks.simulation_task import run_simulation_task

    run_simulation_task.delay(str(model_id), max_steps=max_steps)

    # Optimistically mark as running — the task will confirm
    wm.status = "running"
    await db.flush()

    return wm


@router.post("/{model_id}/pause", response_model=WorldModelResponse)
async def pause_simulation(
    model_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Pause a running simulation."""
    wm = await _get_or_404(model_id, db)

    if wm.status != "running":
        raise HTTPException(
            status_code=409,
            detail=f"Simulation is not running (current status: {wm.status})",
        )

    wm.status = "paused"
    await db.flush()
    return wm


@router.post("/{model_id}/step", response_model=dict)
async def manual_step(
    model_id: UUID,
    payload: StepAction | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Execute a single simulation step manually (enqueues a Celery task)."""
    wm = await _get_or_404(model_id, db)

    if wm.status not in ("idle", "paused"):
        raise HTTPException(
            status_code=409,
            detail=f"Manual step requires status idle or paused (current: {wm.status})",
        )

    from app.tasks.simulation_task import step_once_task

    action = payload.action if payload else None
    task = step_once_task.delay(str(model_id), action)

    return {"task_id": task.id, "message": "Step enqueued"}


@router.post("/{model_id}/reset", response_model=WorldModelResponse)
async def reset_simulation(
    model_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Reset the simulation to its initial state."""
    wm = await _get_or_404(model_id, db)

    if wm.status == "running":
        raise HTTPException(
            status_code=409,
            detail="Cannot reset while simulation is running. Pause first.",
        )

    wm.status = "idle"
    wm.total_steps = 0
    wm.total_cost_usd = 0
    wm.current_state = {}

    # Delete existing events
    from sqlalchemy import delete
    await db.execute(
        delete(PhysicsEvent).where(PhysicsEvent.model_id == model_id)
    )
    await db.flush()

    return wm


@router.get("/{model_id}/events", response_model=PhysicsEventListResponse)
async def list_events(
    model_id: UUID,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Get paginated physics events for a world model."""
    # Ensure model exists
    await _get_or_404(model_id, db)

    query = (
        select(PhysicsEvent)
        .where(PhysicsEvent.model_id == model_id)
        .order_by(PhysicsEvent.step)
    )

    count_q = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_q)

    result = await db.execute(query.limit(limit).offset(offset))
    items = result.scalars().all()

    return PhysicsEventListResponse(
        items=list(items),
        total=total,
        model_id=model_id,
    )


@router.delete("/{model_id}", status_code=204)
async def delete_world_model(
    model_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete a world model and all its physics events."""
    wm = await _get_or_404(model_id, db)

    if wm.status == "running":
        raise HTTPException(
            status_code=409,
            detail="Cannot delete a running simulation. Pause it first.",
        )

    await db.delete(wm)
    await db.flush()
