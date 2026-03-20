import copy
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.models import ReviewTemplate
from app.schemas.template import TemplateCreate, TemplateResponse, TemplateUpdate

router = APIRouter(prefix="/api/templates", tags=["templates"])


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------


@router.get("", response_model=list[TemplateResponse])
async def list_templates(
    created_by: str | None = Query(None, description="Filter by creator"),
    db: AsyncSession = Depends(get_db),
):
    query = select(ReviewTemplate).order_by(ReviewTemplate.created_at.desc())
    if created_by is not None:
        query = query.where(ReviewTemplate.created_by == created_by)
    result = await db.execute(query)
    return result.scalars().all()


# ---------------------------------------------------------------------------
# Get
# ---------------------------------------------------------------------------


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(template_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ReviewTemplate).where(ReviewTemplate.id == template_id))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


@router.post("", response_model=TemplateResponse, status_code=201)
async def create_template(payload: TemplateCreate, db: AsyncSession = Depends(get_db)):
    # Enforce unique name at application level (DB also has a unique constraint)
    existing = await db.execute(select(ReviewTemplate).where(ReviewTemplate.name == payload.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"Template with name '{payload.name}' already exists")

    template = ReviewTemplate(
        name=payload.name,
        description=payload.description,
        rules=payload.rules,
    )
    db.add(template)
    await db.flush()
    return template


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------


@router.put("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: UUID,
    payload: TemplateUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ReviewTemplate).where(ReviewTemplate.id == template_id))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    if payload.name is not None:
        # Check name uniqueness (excluding self)
        dup = await db.execute(
            select(ReviewTemplate).where(
                ReviewTemplate.name == payload.name,
                ReviewTemplate.id != template_id,
            )
        )
        if dup.scalar_one_or_none():
            raise HTTPException(status_code=409, detail=f"Template with name '{payload.name}' already exists")
        template.name = payload.name

    if payload.description is not None:
        template.description = payload.description

    if payload.rules is not None:
        template.rules = payload.rules

    await db.flush()
    return template


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------


@router.delete("/{template_id}", status_code=204)
async def delete_template(template_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ReviewTemplate).where(ReviewTemplate.id == template_id))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    await db.delete(template)
    await db.flush()


# ---------------------------------------------------------------------------
# Fork
# ---------------------------------------------------------------------------


@router.post("/{template_id}/fork", response_model=TemplateResponse, status_code=201)
async def fork_template(template_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ReviewTemplate).where(ReviewTemplate.id == template_id))
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Template not found")

    # Build a unique forked name
    base_name = f"{source.name} (fork)"
    fork_name = base_name
    counter = 1
    while True:
        dup = await db.execute(select(ReviewTemplate).where(ReviewTemplate.name == fork_name))
        if not dup.scalar_one_or_none():
            break
        counter += 1
        fork_name = f"{base_name} {counter}"

    forked = ReviewTemplate(
        name=fork_name,
        description=source.description,
        rules=copy.deepcopy(source.rules),
        created_by=source.created_by,
    )
    db.add(forked)
    await db.flush()
    return forked
