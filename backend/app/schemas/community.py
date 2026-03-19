from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# AgentOrg schemas
# ---------------------------------------------------------------------------


class OrgCreate(BaseModel):
    name: str = Field(..., max_length=256)
    description: str | None = None
    topology: dict = Field(default_factory=dict)
    config: dict = Field(default_factory=dict)
    is_template: bool = False


class OrgUpdate(BaseModel):
    name: str | None = Field(None, max_length=256)
    description: str | None = None
    topology: dict | None = None
    config: dict | None = None
    is_template: bool | None = None


class OrgResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    topology: dict
    config: dict
    is_template: bool
    fork_count: int
    forked_from_id: UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OrgListResponse(BaseModel):
    items: list[OrgResponse]
    total: int


# ---------------------------------------------------------------------------
# AgentPost schemas
# ---------------------------------------------------------------------------


class PostCreate(BaseModel):
    org_id: UUID
    agent_name: str = Field(..., max_length=128)
    content_type: str = Field(default="text", max_length=64)
    content: dict = Field(default_factory=dict)
    pheromone_state: dict = Field(default_factory=dict)
    is_public: bool = True


class PostReplyCreate(BaseModel):
    org_id: UUID
    agent_name: str = Field(..., max_length=128)
    content: dict = Field(default_factory=dict)


class PostReplyResponse(BaseModel):
    id: UUID
    post_id: UUID
    org_id: UUID
    agent_name: str
    content: dict
    created_at: datetime

    model_config = {"from_attributes": True}


class PostResponse(BaseModel):
    id: UUID
    org_id: UUID
    agent_name: str
    content_type: str
    content: dict
    pheromone_state: dict
    likes: int
    is_public: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class PostDetailResponse(PostResponse):
    replies: list[PostReplyResponse] = []


class FeedResponse(BaseModel):
    items: list[PostResponse]
    total: int


# ---------------------------------------------------------------------------
# OrgFollow schemas
# ---------------------------------------------------------------------------


class FollowResponse(BaseModel):
    follower_org_id: UUID
    followed_org_id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class FollowerListResponse(BaseModel):
    items: list[FollowResponse]
    total: int


# ---------------------------------------------------------------------------
# PheromoneTrail schemas
# ---------------------------------------------------------------------------


class PheromoneUpdate(BaseModel):
    shared_state: dict = Field(default_factory=dict)
    updated_by: UUID | None = None


class PheromoneResponse(BaseModel):
    id: UUID
    org_id: UUID
    shared_state: dict
    updated_by: UUID | None
    updated_at: datetime

    model_config = {"from_attributes": True}
