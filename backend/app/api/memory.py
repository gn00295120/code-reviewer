"""Memory Palace API — agent memory CRUD + search + consolidation."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.models import AgentMemory
from app.schemas.memory import (
    MemoryConsolidateRequest,
    MemoryCreate,
    MemoryListResponse,
    MemoryResponse,
    MemorySearchResponse,
)
from app.services import memory_service

router = APIRouter(prefix="/api/memory", tags=["memory"])


# ---------------------------------------------------------------------------
# GET /api/memory
# ---------------------------------------------------------------------------


@router.get("", response_model=MemoryListResponse)
async def list_memories(
    agent_role: str | None = Query(None, description="Filter by agent role"),
    memory_type: str | None = Query(None, description="Filter by memory type"),
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List agent memories with optional filters."""
    query = select(AgentMemory).order_by(
        AgentMemory.relevance_score.desc(),
        AgentMemory.last_accessed_at.desc(),
    )
    if agent_role:
        query = query.where(AgentMemory.agent_role == agent_role)
    if memory_type:
        query = query.where(AgentMemory.memory_type == memory_type)

    count_q = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_q) or 0

    result = await db.execute(query.limit(limit).offset(offset))
    items = result.scalars().all()

    return MemoryListResponse(items=items, total=total)


# ---------------------------------------------------------------------------
# GET /api/memory/search  (must be before /{id} to avoid route conflict)
# ---------------------------------------------------------------------------


@router.get("/search", response_model=MemorySearchResponse)
async def search_memories(
    q: str = Query(..., min_length=1, description="Search text"),
    agent_role: str | None = Query(None),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Search memories by text content (case-insensitive JSON substring match)."""
    # Cast JSONB to text for ilike search.
    from sqlalchemy import cast
    from sqlalchemy.dialects.postgresql import JSONB
    from sqlalchemy import Text

    query = (
        select(AgentMemory)
        .where(cast(AgentMemory.content, Text).ilike(f"%{q}%"))
        .order_by(AgentMemory.relevance_score.desc())
        .limit(limit)
    )
    if agent_role:
        query = query.where(AgentMemory.agent_role == agent_role)

    result = await db.execute(query)
    items = result.scalars().all()
    return MemorySearchResponse(items=items, query=q)


# ---------------------------------------------------------------------------
# GET /api/memory/{id}
# ---------------------------------------------------------------------------


@router.get("/{memory_id}", response_model=MemoryResponse)
async def get_memory(memory_id: UUID, db: AsyncSession = Depends(get_db)):
    """Retrieve a single memory by ID (increments access_count)."""
    result = await db.execute(select(AgentMemory).where(AgentMemory.id == memory_id))
    memory = result.scalar_one_or_none()
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")

    memory.access_count += 1
    await db.flush()
    return memory


# ---------------------------------------------------------------------------
# POST /api/memory
# ---------------------------------------------------------------------------


@router.post("", response_model=MemoryResponse, status_code=201)
async def create_memory(payload: MemoryCreate, db: AsyncSession = Depends(get_db)):
    """Manually create a memory record."""
    memory = await memory_service.store_memory(
        db=db,
        agent_role=payload.agent_role,
        memory_type=payload.memory_type,
        content=payload.content,
        source_review_id=payload.source_review_id,
        relevance_score=payload.relevance_score,
    )
    return memory


# ---------------------------------------------------------------------------
# DELETE /api/memory/{id}
# ---------------------------------------------------------------------------


@router.delete("/{memory_id}", status_code=204)
async def delete_memory(memory_id: UUID, db: AsyncSession = Depends(get_db)):
    """Delete a memory by ID."""
    result = await db.execute(select(AgentMemory).where(AgentMemory.id == memory_id))
    memory = result.scalar_one_or_none()
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    await db.delete(memory)
    await db.flush()


# ---------------------------------------------------------------------------
# POST /api/memory/consolidate
# ---------------------------------------------------------------------------


@router.post("/consolidate")
async def consolidate_memories(
    payload: MemoryConsolidateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Merge duplicate memories and prune low-relevance entries for an agent role."""
    summary = await memory_service.consolidate_memories(db, payload.agent_role)
    return summary
