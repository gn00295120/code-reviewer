from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl  # noqa: F401


# --- Request schemas ---


class ReviewCreate(BaseModel):
    pr_url: str = Field(
        ...,
        description="GitHub PR URL or GitLab MR URL",
        examples=[
            "https://github.com/owner/repo/pull/123",
            "https://gitlab.com/group/project/-/merge_requests/456",
        ],
    )
    config: dict = Field(default_factory=dict, description="Optional review configuration overrides")
    template_id: UUID | None = Field(None, description="Optional review template ID; its rules are merged into config")


class WebhookPayload(BaseModel):
    action: str
    number: int
    pull_request: dict
    repository: dict


# --- Response schemas ---


class FindingResponse(BaseModel):
    id: UUID
    agent_role: str
    severity: str
    file_path: str
    line_number: int | None
    title: str
    description: str
    suggested_fix: str | None
    confidence: float
    cost_usd: Decimal
    created_at: datetime

    model_config = {"from_attributes": True}


class ReviewResponse(BaseModel):
    id: UUID
    pr_url: str
    repo_name: str
    pr_number: int | None
    platform: str = "github"
    status: str
    total_issues: int
    total_cost_usd: Decimal
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ReviewDetailResponse(ReviewResponse):
    findings: list[FindingResponse] = []
    config: dict = {}


class ReviewListResponse(BaseModel):
    items: list[ReviewResponse]
    total: int


class ReviewEventResponse(BaseModel):
    id: UUID
    event_type: str
    event_data: dict
    timestamp: datetime

    model_config = {"from_attributes": True}
