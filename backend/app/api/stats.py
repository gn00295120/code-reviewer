"""API endpoints for queue status and aggregate stats."""

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.models import CodeReview, ReviewFinding
from app.services.queue_manager import active_count, active_reviews, MAX_CONCURRENT

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/queue")
async def queue_status():
    """Get current queue status."""
    count = active_count()
    return {
        "active": count,
        "max_concurrent": MAX_CONCURRENT,
        "available": MAX_CONCURRENT - count,
        "active_review_ids": list(active_reviews()),
    }


@router.get("/overview")
async def overview_stats(db: AsyncSession = Depends(get_db)):
    """Get aggregate review stats."""
    # Total reviews by status
    status_result = await db.execute(
        select(CodeReview.status, func.count(CodeReview.id))
        .group_by(CodeReview.status)
    )
    status_counts = dict(status_result.all())

    # Total cost
    cost_result = await db.scalar(
        select(func.sum(CodeReview.total_cost_usd))
    )

    # Total findings by severity
    severity_result = await db.execute(
        select(ReviewFinding.severity, func.count(ReviewFinding.id))
        .group_by(ReviewFinding.severity)
    )
    severity_counts = dict(severity_result.all())

    # Average issues per review
    avg_result = await db.scalar(
        select(func.avg(CodeReview.total_issues))
        .where(CodeReview.status == "completed")
    )

    return {
        "reviews_by_status": status_counts,
        "total_cost_usd": float(cost_result or 0),
        "findings_by_severity": severity_counts,
        "avg_issues_per_review": float(avg_result or 0),
        "queue": {
            "active": active_count(),
            "max_concurrent": MAX_CONCURRENT,
        },
    }
