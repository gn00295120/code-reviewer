"""In-process async review task for desktop mode (replaces Celery)."""

import uuid as uuid_mod
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session
from app.core.models import CodeReview, ReviewEvent, ReviewFinding
from app.core.websocket import ws_manager
from app.services.vcs_provider import get_vcs_provider
from app.services.queue_manager import enqueue_review, dequeue_review


async def save_review_event(db: AsyncSession, review_id: str, event_type: str, event_data: dict):
    """Persist a review event to the database for historical replay."""
    event = ReviewEvent(
        review_id=uuid_mod.UUID(review_id),
        event_type=event_type,
        event_data=event_data,
    )
    db.add(event)
    await db.flush()


async def run_review_in_process(review_id: str):
    """Main review task running in-process (no Celery)."""
    async with async_session() as db:
        result = await db.execute(
            select(CodeReview).where(CodeReview.id == uuid_mod.UUID(review_id))
        )
        review = result.scalar_one_or_none()
        if not review:
            return

        if review.status == "cancelled":
            return

        # Queue management — max 10 concurrent reviews
        if not enqueue_review(review_id):
            review.status = "failed"
            review.error_message = "Queue full — retry later"
            await db.commit()
            return

        try:
            review.status = "running"
            review.started_at = datetime.utcnow()
            await db.commit()

            await ws_manager.publish(f"review:{review_id}", "review:started", {
                "review_id": review_id,
                "pr_url": review.pr_url,
            })
            await save_review_event(db, review_id, "review:started", {
                "review_id": review_id,
                "pr_url": review.pr_url,
            })

            # Step 1: Fetch PR diff
            fetch_started = {"agent": "fetch_diff", "status": "running"}
            await ws_manager.publish(f"review:{review_id}", "review:agent:started", fetch_started)
            await save_review_event(db, review_id, "review:agent:started", fetch_started)

            provider = get_vcs_provider(review.platform)
            pr_diff = provider.fetch_pr_diff(review.pr_url)

            fetch_completed = {
                "agent": "fetch_diff",
                "files_count": len(pr_diff.files),
                "total_lines": pr_diff.total_additions + pr_diff.total_deletions,
            }
            await ws_manager.publish(f"review:{review_id}", "review:agent:completed", fetch_completed)
            await save_review_event(db, review_id, "review:agent:completed", fetch_completed)

            # Step 2: Run LangGraph pipeline
            from agents.pipeline import run_review_pipeline

            pipeline_result = run_review_pipeline(review_id, pr_diff)

            # Step 3: Save findings to DB
            total_cost = 0
            for finding_data in pipeline_result["findings"]:
                finding = ReviewFinding(
                    review_id=review.id,
                    agent_role=finding_data["agent_role"],
                    severity=finding_data["severity"],
                    file_path=finding_data["file_path"],
                    line_number=finding_data.get("line_number"),
                    title=finding_data["title"],
                    description=finding_data["description"],
                    suggested_fix=finding_data.get("suggested_fix"),
                    confidence=finding_data.get("confidence", 0.8),
                    tokens_used=finding_data.get("tokens_used", 0),
                    cost_usd=finding_data.get("cost_usd", 0),
                )
                db.add(finding)
                total_cost += finding_data.get("cost_usd", 0)

            review.status = "completed"
            review.total_issues = len(pipeline_result["findings"])
            review.total_cost_usd = total_cost
            review.completed_at = datetime.utcnow()
            await db.commit()

            await ws_manager.publish(f"review:{review_id}", "review:completed", {
                "review_id": review_id,
                "total_issues": len(pipeline_result["findings"]),
                "total_cost_usd": total_cost,
                "summary": pipeline_result.get("summary", ""),
            })

        except Exception as e:
            review.status = "failed"
            review.error_message = str(e)
            review.completed_at = datetime.utcnow()
            await db.commit()

            await ws_manager.publish(f"review:{review_id}", "review:failed", {
                "review_id": review_id,
                "error": str(e),
            })
        finally:
            dequeue_review(review_id)
