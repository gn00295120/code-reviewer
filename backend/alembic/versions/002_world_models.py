"""Add world_models and physics_events tables.

Revision ID: 002
Revises: 001
Create Date: 2026-03-19
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enum types
    op.execute(
        "CREATE TYPE world_model_status AS ENUM "
        "('idle', 'running', 'paused', 'completed', 'error')"
    )

    # world_models
    op.create_table(
        "world_models",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("mujoco_xml", sa.Text, nullable=True),
        sa.Column("model_type", sa.String(64), server_default="custom", nullable=False),
        sa.Column("current_state", JSONB, server_default="{}"),
        sa.Column("agent_config", JSONB, server_default="{}"),
        sa.Column("total_steps", sa.Integer, server_default="0", nullable=False),
        sa.Column("total_cost_usd", sa.Numeric(10, 6), server_default="0", nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "idle",
                "running",
                "paused",
                "completed",
                "error",
                name="world_model_status",
                create_type=False,
            ),
            server_default="idle",
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_world_models_status", "world_models", ["status"])
    op.create_index("ix_world_models_model_type", "world_models", ["model_type"])
    op.create_index("ix_world_models_created_at", "world_models", ["created_at"])

    # physics_events
    op.create_table(
        "physics_events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "model_id",
            UUID(as_uuid=True),
            sa.ForeignKey("world_models.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("step", sa.Integer, nullable=False),
        sa.Column("action", JSONB, server_default="{}"),
        sa.Column("observation", JSONB, server_default="{}"),
        sa.Column("reward", sa.Float, server_default="0.0"),
        sa.Column("agent_reasoning", sa.Text, nullable=True),
        sa.Column("tokens_used", sa.Integer, server_default="0"),
        sa.Column("cost_usd", sa.Numeric(10, 6), server_default="0"),
        sa.Column("timestamp", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_physics_events_model_id", "physics_events", ["model_id"])
    op.create_index("ix_physics_events_step", "physics_events", ["model_id", "step"])


def downgrade() -> None:
    op.drop_table("physics_events")
    op.drop_table("world_models")
    op.execute("DROP TYPE world_model_status")
