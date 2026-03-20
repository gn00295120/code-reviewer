from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


# --- Audit log schemas ---


class AuditLogResponse(BaseModel):
    id: UUID
    action: str
    actor: str | None
    resource_type: str
    resource_id: UUID | None
    details: dict[str, Any]
    ip_address: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditLogListResponse(BaseModel):
    items: list[AuditLogResponse]
    total: int


# --- Security policy schemas ---


class SecurityPolicyCreate(BaseModel):
    name: str = Field(..., max_length=128, description="Unique policy name")
    policy_type: str = Field(
        ...,
        max_length=64,
        description="Policy type: rate_limit | secret_detection | access_control",
    )
    config: dict[str, Any] = Field(default_factory=dict, description="Policy configuration payload")
    is_active: bool = Field(True, description="Whether the policy is currently enforced")


class SecurityPolicyUpdate(BaseModel):
    name: str | None = Field(None, max_length=128)
    policy_type: str | None = Field(None, max_length=64)
    config: dict[str, Any] | None = None
    is_active: bool | None = None


class SecurityPolicyResponse(BaseModel):
    id: UUID
    name: str
    policy_type: str
    config: dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}


class PolicyToggleResponse(BaseModel):
    id: UUID
    is_active: bool
    message: str
