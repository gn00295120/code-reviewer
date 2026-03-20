from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


# --- Request schemas ---


class MemoryCreate(BaseModel):
    agent_role: str = Field(..., max_length=64, description="Agent role (logic, security, etc.)")
    memory_type: str = Field(..., max_length=64, description="Memory type (pattern, learning, preference)")
    content: dict[str, Any] = Field(default_factory=dict, description="Memory content payload")
    source_review_id: UUID | None = Field(None, description="Review that produced this memory")
    relevance_score: float = Field(1.0, ge=0.0, le=1.0, description="Initial relevance score")


class MemoryConsolidateRequest(BaseModel):
    agent_role: str = Field(..., max_length=64, description="Agent role to consolidate memories for")


# --- Response schemas ---


class MemoryResponse(BaseModel):
    id: UUID
    agent_role: str
    memory_type: str
    content: dict[str, Any]
    source_review_id: UUID | None
    relevance_score: float
    access_count: int
    created_at: datetime
    last_accessed_at: datetime

    model_config = {"from_attributes": True}


class MemoryListResponse(BaseModel):
    items: list[MemoryResponse]
    total: int


class MemorySearchResponse(BaseModel):
    items: list[MemoryResponse]
    query: str
