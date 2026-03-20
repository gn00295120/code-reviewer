"""Review Events - persist WebSocket events for historical replay

Revision ID: 004
Revises: 003
Create Date: 2026-03-20
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "review_events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "review_id",
            UUID(as_uuid=True),
            sa.ForeignKey("code_reviews.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("event_data", JSONB, nullable=False, server_default="{}"),
        sa.Column("timestamp", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_review_events_review_id", "review_events", ["review_id"])
    op.create_index("ix_review_events_timestamp", "review_events", ["timestamp"])


def downgrade() -> None:
    op.drop_index("ix_review_events_timestamp", table_name="review_events")
    op.drop_index("ix_review_events_review_id", table_name="review_events")
    op.drop_table("review_events")
