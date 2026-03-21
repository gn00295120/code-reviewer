import json
import uuid as uuid_mod
from datetime import datetime

import redis
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.celery_app import celery_app
from app.core.config import get_settings
from app.core.models import CodeReview, ReviewEvent, ReviewFinding
from app.services.vcs_provider import get_vcs_provider
from app.services.queue_manager import enqueue_review, dequeue_review

settings = get_settings()

# Sync engine for Celery (Celery doesn't support async)
sync_engine = create_engine(settings.database_url_sync)
redis_client = redis.from_url(settings.redis_url, decode_responses=True)


def save_review_event(review_id: str, event_type: str, event_data: dict):
    """Persist a review event to the database for historical replay."""
    with Session(sync_engine) as db:
        event = ReviewEvent(
            review_id=uuid_mod.UUID(review_id),
            event_type=event_type,
            event_data=event_data,
        )
        db.add(event)
        db.commit()


def publish_ws_event(review_id: str, event: str, data: dict):
    """Publish WebSocket event via Redis pub/sub and persist to DB."""
    payload = json.dumps({
        "room": f"review:{review_id}",
        "event": event,
        "data": data,
    })
    redis_client.publish("ws:events", payload)
    save_review_event(review_id, event, data)


@celery_app.task(bind=True, name="review.run")
def run_review_task(self, review_id: str):
    """Main review task: fetch diff → run agents → save findings."""
    with Session(sync_engine) as db:
        review = db.query(CodeReview).filter(CodeReview.id == uuid_mod.UUID(review_id)).first()
        if not review:
            return {"error": "Review not found"}

        if review.status == "cancelled":
            return {"status": "cancelled"}

        # Queue management — max 10 concurrent reviews
        if not enqueue_review(review_id):
            review.status = "pending"
            review.error_message = "Queue full — will retry"
            db.commit()
            raise self.retry(countdown=15, max_retries=20)

        try:
            # Update status to running
            review.status = "running"
            review.started_at = datetime.utcnow()
            db.commit()

            publish_ws_event(review_id, "review:started", {
                "review_id": review_id,
                "pr_url": review.pr_url,
            })

            # Step 1: Fetch PR diff
            publish_ws_event(review_id, "review:agent:started", {
                "agent": "fetch_diff",
                "status": "running",
            })
            provider = get_vcs_provider(review.platform)
            pr_diff = provider.fetch_pr_diff(review.pr_url)
            publish_ws_event(review_id, "review:agent:completed", {
                "agent": "fetch_diff",
                "files_count": len(pr_diff.files),
                "total_lines": pr_diff.total_additions + pr_diff.total_deletions,
            })

            # Step 2: Run LangGraph pipeline
            from agents.pipeline import run_review_pipeline

            result = run_review_pipeline(review_id, pr_diff)

            # Step 3: Save findings to DB
            total_cost = 0
            for finding_data in result["findings"]:
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

            # Update review
            review.status = "completed"
            review.total_issues = len(result["findings"])
            review.total_cost_usd = total_cost
            review.completed_at = datetime.utcnow()
            db.commit()

            publish_ws_event(review_id, "review:completed", {
                "review_id": review_id,
                "total_issues": len(result["findings"]),
                "total_cost_usd": total_cost,
                "summary": result.get("summary", ""),
            })

            dequeue_review(review_id)
            return {
                "status": "completed",
                "total_issues": len(result["findings"]),
                "total_cost_usd": total_cost,
            }

        except Exception as e:
            dequeue_review(review_id)
            review.status = "failed"
            review.error_message = str(e)
            review.completed_at = datetime.utcnow()
            db.commit()

            publish_ws_event(review_id, "review:failed", {
                "review_id": review_id,
                "error": str(e),
            })

            raise self.retry(exc=e, max_retries=1, countdown=30)
