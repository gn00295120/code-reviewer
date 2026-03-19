"""API endpoint for posting review findings to GitHub as PR comments."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.models import CodeReview
from app.services.github_service import post_inline_comments

router = APIRouter(prefix="/api/reviews", tags=["github-actions"])


@router.post("/{review_id}/post-to-github")
async def post_findings_to_github(
    review_id: UUID,
    severity_threshold: str = "low",
    db: AsyncSession = Depends(get_db),
):
    """Post review findings as inline comments on the GitHub PR.

    Args:
        review_id: The review to post findings from
        severity_threshold: Minimum severity to post (high, medium, low, info)
    """
    result = await db.execute(
        select(CodeReview)
        .options(selectinload(CodeReview.findings))
        .where(CodeReview.id == review_id)
    )
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    if review.status != "completed":
        raise HTTPException(status_code=400, detail=f"Review is {review.status}, not completed")

    if not review.findings:
        return {"posted": 0, "message": "No findings to post"}

    # Filter by severity threshold
    severity_order = {"high": 0, "medium": 1, "low": 2, "info": 3}
    threshold = severity_order.get(severity_threshold, 2)

    filtered = [
        {
            "agent_role": f.agent_role,
            "severity": f.severity,
            "file_path": f.file_path,
            "line_number": f.line_number,
            "title": f.title,
            "description": f.description,
            "suggested_fix": f.suggested_fix,
            "confidence": f.confidence,
        }
        for f in review.findings
        if severity_order.get(f.severity, 3) <= threshold
    ]

    if not filtered:
        return {"posted": 0, "message": "No findings above severity threshold"}

    try:
        posted = post_inline_comments(review.pr_url, filtered)
        return {"posted": posted, "message": f"Posted {posted} comments to GitHub"}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to post to GitHub: {str(e)}")
