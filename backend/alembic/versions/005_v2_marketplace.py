"""v2.0 — Memory Palace, Enterprise Guard, Marketplace

Revision ID: 005
Revises: 004
Create Date: 2026-03-20
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # agent_memories
    # ------------------------------------------------------------------
    op.create_table(
        "agent_memories",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("agent_role", sa.String(64), nullable=False),
        sa.Column("memory_type", sa.String(64), nullable=False),
        sa.Column("content", JSONB, nullable=False, server_default="{}"),
        sa.Column("source_review_id", UUID(as_uuid=True), sa.ForeignKey("code_reviews.id"), nullable=True),
        sa.Column("relevance_score", sa.Float, nullable=False, server_default="1.0"),
        sa.Column("access_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("last_accessed_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_agent_memories_agent_role", "agent_memories", ["agent_role"])
    op.create_index("ix_agent_memories_memory_type", "agent_memories", ["memory_type"])

    # ------------------------------------------------------------------
    # audit_logs
    # ------------------------------------------------------------------
    op.create_table(
        "audit_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("action", sa.String(128), nullable=False),
        sa.Column("actor", sa.String(256), nullable=True),
        sa.Column("resource_type", sa.String(64), nullable=False),
        sa.Column("resource_id", UUID(as_uuid=True), nullable=True),
        sa.Column("details", JSONB, nullable=False, server_default="{}"),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])

    # ------------------------------------------------------------------
    # security_policies
    # ------------------------------------------------------------------
    op.create_table(
        "security_policies",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(128), nullable=False, unique=True),
        sa.Column("policy_type", sa.String(64), nullable=False),
        sa.Column("config", JSONB, nullable=False, server_default="{}"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    # ------------------------------------------------------------------
    # marketplace_listings
    # ------------------------------------------------------------------
    op.create_table(
        "marketplace_listings",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("listing_type", sa.String(64), nullable=False),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("author", sa.String(128), nullable=True),
        sa.Column("version", sa.String(32), nullable=False, server_default="1.0.0"),
        sa.Column("config", JSONB, nullable=False, server_default="{}"),
        sa.Column("tags", JSONB, nullable=False, server_default="[]"),
        sa.Column("downloads", sa.Integer, nullable=False, server_default="0"),
        sa.Column("rating", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("rating_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_published", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_marketplace_listings_listing_type", "marketplace_listings", ["listing_type"])
    op.create_index("ix_marketplace_listings_is_published", "marketplace_listings", ["is_published"])


def downgrade() -> None:
    op.drop_table("marketplace_listings")
    op.drop_table("security_policies")
    op.drop_table("audit_logs")
    op.drop_table("agent_memories")
