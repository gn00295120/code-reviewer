import re
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.models import CodeReview, ReviewEvent, ReviewFinding, ReviewTemplate
from app.schemas.review import (
    FindingResponse,
    ReviewCreate,
    ReviewDetailResponse,
    ReviewEventResponse,
    ReviewListResponse,
    ReviewResponse,
)
from app.tasks.review_task import run_review_task

router = APIRouter(prefix="/api/reviews", tags=["reviews"])


def parse_pr_url(pr_url: str) -> tuple[str, int]:
    """Extract repo name and PR number from GitHub PR URL."""
    match = re.match(r"https?://github\.com/([^/]+/[^/]+)/pull/(\d+)", pr_url)
    if not match:
        raise HTTPException(status_code=400, detail="Invalid GitHub PR URL format")
    return match.group(1), int(match.group(2))


@router.post("", response_model=ReviewResponse, status_code=201)
async def create_review(payload: ReviewCreate, db: AsyncSession = Depends(get_db)):
    repo_name, pr_number = parse_pr_url(payload.pr_url)

    # Build config: start from caller-supplied config then layer template rules on top
    effective_config: dict = dict(payload.config)
    if payload.template_id is not None:
        tmpl_result = await db.execute(
            select(ReviewTemplate).where(ReviewTemplate.id == payload.template_id)
        )
        template = tmpl_result.scalar_one_or_none()
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        # Template rules take precedence over caller-supplied config
        effective_config = {**effective_config, **template.rules}

    review = CodeReview(
        pr_url=payload.pr_url,
        repo_name=repo_name,
        pr_number=pr_number,
        status="pending",
        config=effective_config,
    )
    db.add(review)
    await db.flush()

    # Enqueue Celery task
    run_review_task.delay(str(review.id))

    return review


@router.get("", response_model=ReviewListResponse)
async def list_reviews(
    status: str | None = Query(None),
    repo: str | None = Query(None),
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    query = select(CodeReview).order_by(CodeReview.created_at.desc())

    if status:
        query = query.where(CodeReview.status == status)
    if repo:
        query = query.where(CodeReview.repo_name.ilike(f"%{repo}%"))

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    result = await db.execute(query.limit(limit).offset(offset))
    items = result.scalars().all()

    return ReviewListResponse(items=items, total=total)


@router.get("/{review_id}", response_model=ReviewDetailResponse)
async def get_review(review_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CodeReview)
        .options(selectinload(CodeReview.findings))
        .where(CodeReview.id == review_id)
    )
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    return review


@router.delete("/{review_id}", status_code=204)
async def cancel_review(review_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CodeReview).where(CodeReview.id == review_id))
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    if review.status in ("pending", "running"):
        review.status = "cancelled"
        await db.flush()
    else:
        raise HTTPException(status_code=400, detail=f"Cannot cancel review in {review.status} state")


@router.get("/{review_id}/timeline", response_model=list[ReviewEventResponse])
async def get_review_timeline(review_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get all events for a review in chronological order for replay."""
    query = (
        select(ReviewEvent)
        .where(ReviewEvent.review_id == review_id)
        .order_by(ReviewEvent.timestamp)
    )
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{review_id}/findings", response_model=list[FindingResponse])
async def list_findings(
    review_id: UUID,
    severity: str | None = Query(None),
    agent_role: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(ReviewFinding).where(ReviewFinding.review_id == review_id)

    if severity:
        query = query.where(ReviewFinding.severity == severity)
    if agent_role:
        query = query.where(ReviewFinding.agent_role == agent_role)

    query = query.order_by(ReviewFinding.created_at)
    result = await db.execute(query)
    return result.scalars().all()
