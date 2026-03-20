from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


# --- Request schemas ---


class TemplateCreate(BaseModel):
    name: str = Field(..., max_length=128, description="Unique template name")
    description: str | None = Field(None, description="What this template does")
    rules: dict[str, Any] = Field(
        default_factory=dict,
        description="Agent rule configuration (agents + global settings)",
    )


class TemplateUpdate(BaseModel):
    name: str | None = Field(None, max_length=128)
    description: str | None = None
    rules: dict[str, Any] | None = None


# --- Response schema ---


class TemplateResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    rules: dict[str, Any]
    created_by: str | None
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}
