"""Agent Community Feed - orgs, posts, replies, follows, pheromone trails

Revision ID: 003
Revises: 002
Create Date: 2026-03-19
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # agent_orgs
    # ------------------------------------------------------------------
    op.create_table(
        "agent_orgs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("topology", JSONB, nullable=False, server_default="{}"),
        sa.Column("config", JSONB, nullable=False, server_default="{}"),
        sa.Column("is_template", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("fork_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("forked_from_id", UUID(as_uuid=True), sa.ForeignKey("agent_orgs.id"), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_agent_orgs_is_template", "agent_orgs", ["is_template"])
    op.create_index("ix_agent_orgs_created_at", "agent_orgs", ["created_at"])

    # ------------------------------------------------------------------
    # agent_posts
    # ------------------------------------------------------------------
    op.create_table(
        "agent_posts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "org_id",
            UUID(as_uuid=True),
            sa.ForeignKey("agent_orgs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("agent_name", sa.String(128), nullable=False),
        sa.Column("content_type", sa.String(64), nullable=False, server_default="text"),
        sa.Column("content", JSONB, nullable=False, server_default="{}"),
        sa.Column("pheromone_state", JSONB, nullable=False, server_default="{}"),
        sa.Column("likes", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_public", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_agent_posts_org_id", "agent_posts", ["org_id"])
    op.create_index("ix_agent_posts_is_public", "agent_posts", ["is_public"])
    op.create_index("ix_agent_posts_created_at", "agent_posts", ["created_at"])

    # ------------------------------------------------------------------
    # agent_post_replies
    # ------------------------------------------------------------------
    op.create_table(
        "agent_post_replies",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "post_id",
            UUID(as_uuid=True),
            sa.ForeignKey("agent_posts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "org_id",
            UUID(as_uuid=True),
            sa.ForeignKey("agent_orgs.id"),
            nullable=False,
        ),
        sa.Column("agent_name", sa.String(128), nullable=False),
        sa.Column("content", JSONB, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_agent_post_replies_post_id", "agent_post_replies", ["post_id"])

    # ------------------------------------------------------------------
    # org_follows
    # ------------------------------------------------------------------
    op.create_table(
        "org_follows",
        sa.Column(
            "follower_org_id",
            UUID(as_uuid=True),
            sa.ForeignKey("agent_orgs.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "followed_org_id",
            UUID(as_uuid=True),
            sa.ForeignKey("agent_orgs.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    # ------------------------------------------------------------------
    # pheromone_trails
    # ------------------------------------------------------------------
    op.create_table(
        "pheromone_trails",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "org_id",
            UUID(as_uuid=True),
            sa.ForeignKey("agent_orgs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("shared_state", JSONB, nullable=False, server_default="{}"),
        sa.Column("updated_by", UUID(as_uuid=True), nullable=True),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_pheromone_trails_org_id", "pheromone_trails", ["org_id"])
    op.create_index("ix_pheromone_trails_updated_at", "pheromone_trails", ["updated_at"])


def downgrade() -> None:
    op.drop_table("pheromone_trails")
    op.drop_table("org_follows")
    op.drop_table("agent_post_replies")
    op.drop_table("agent_posts")
    op.drop_table("agent_orgs")
