import hashlib
import hmac
import json

from fastapi import APIRouter, Header, HTTPException, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.models import CodeReview
from app.tasks.review_task import run_review_task

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])
settings = get_settings()


def verify_github_signature(payload_body: bytes, signature: str, secret: str) -> bool:
    if not secret:
        return True  # Skip verification if no secret configured
    expected = "sha256=" + hmac.new(secret.encode(), payload_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


@router.post("/github")
async def github_webhook(
    request: Request,
    x_hub_signature_256: str = Header(None),
    x_github_event: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    body = await request.body()

    if settings.github_webhook_secret:
        if not x_hub_signature_256 or not verify_github_signature(
            body, x_hub_signature_256, settings.github_webhook_secret
        ):
            raise HTTPException(status_code=401, detail="Invalid signature")

    if x_github_event != "pull_request":
        return {"status": "ignored", "reason": f"event type: {x_github_event}"}

    payload = json.loads(body)
    action = payload.get("action")

    if action not in ("opened", "synchronize", "reopened"):
        return {"status": "ignored", "reason": f"action: {action}"}

    pr = payload["pull_request"]
    pr_url = pr["html_url"]
    repo_name = payload["repository"]["full_name"]
    pr_number = payload["number"]

    review = CodeReview(
        pr_url=pr_url,
        repo_name=repo_name,
        pr_number=pr_number,
        platform="github",
        status="pending",
    )
    db.add(review)
    await db.flush()

    run_review_task.delay(str(review.id))

    return {"status": "queued", "review_id": str(review.id)}


@router.post("/gitlab")
async def gitlab_webhook(
    request: Request,
    x_gitlab_token: str = Header(None),
    x_gitlab_event: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    body = await request.body()

    # GitLab uses a plain secret token (not HMAC) — use timing-safe comparison
    if settings.gitlab_webhook_secret:
        if not x_gitlab_token or not hmac.compare_digest(
            x_gitlab_token, settings.gitlab_webhook_secret
        ):
            raise HTTPException(status_code=401, detail="Invalid GitLab webhook token")

    if x_gitlab_event != "Merge Request Hook":
        return {"status": "ignored", "reason": f"event: {x_gitlab_event}"}

    payload = json.loads(body)
    attrs = payload.get("object_attributes", {})
    action = attrs.get("action")

    if action not in ("open", "update", "reopen"):
        return {"status": "ignored", "reason": f"action: {action}"}

    try:
        project = payload["project"]
        pr_url = attrs["url"]
        repo_name = project["path_with_namespace"]
        mr_number = attrs["iid"]
    except KeyError as e:
        raise HTTPException(status_code=422, detail=f"Missing required field in payload: {e}")

    review = CodeReview(
        pr_url=pr_url,
        repo_name=repo_name,
        pr_number=mr_number,
        platform="gitlab",
        status="pending",
    )
    db.add(review)
    await db.flush()

    run_review_task.delay(str(review.id))

    return {"status": "queued", "review_id": str(review.id)}
