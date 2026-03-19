"""Pydantic schemas for World Model Sandbox API."""

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class WorldModelCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=256, description="Display name for this sandbox")
    description: str | None = Field(None, description="Optional description")
    mujoco_xml: str | None = Field(None, description="MuJoCo MJCF XML model definition")
    model_type: str = Field(
        "custom",
        description="Preset model type: crazyflie | jaco | ur5 | custom",
    )
    agent_config: dict[str, Any] = Field(
        default_factory=dict,
        description="LLM agent configuration (model, temperature, max_tokens, etc.)",
    )


class WorldModelUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=256)
    description: str | None = None
    mujoco_xml: str | None = None
    agent_config: dict[str, Any] | None = None


class StepAction(BaseModel):
    """Payload for a manual single-step execution."""

    action: dict[str, Any] = Field(
        default_factory=dict,
        description="Joint torques / velocities to apply. Empty dict lets the agent decide.",
    )


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class PhysicsEventResponse(BaseModel):
    id: UUID
    model_id: UUID
    step: int
    action: dict[str, Any]
    observation: dict[str, Any]
    reward: float
    agent_reasoning: str | None
    tokens_used: int
    cost_usd: Decimal
    timestamp: datetime

    model_config = {"from_attributes": True}


class WorldModelResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    model_type: str
    status: str
    total_steps: int
    total_cost_usd: Decimal
    current_state: dict[str, Any]
    agent_config: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WorldModelDetailResponse(WorldModelResponse):
    mujoco_xml: str | None
    recent_events: list[PhysicsEventResponse] = []


class WorldModelListResponse(BaseModel):
    items: list[WorldModelResponse]
    total: int


class PhysicsEventListResponse(BaseModel):
    items: list[PhysicsEventResponse]
    total: int
    model_id: UUID
