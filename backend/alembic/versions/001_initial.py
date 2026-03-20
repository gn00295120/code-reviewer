"""Initial migration - code reviews, findings, templates

Revision ID: 001
Revises: None
Create Date: 2026-03-19
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # code_reviews
    op.create_table(
        "code_reviews",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("pr_url", sa.String(512), nullable=False),
        sa.Column("repo_name", sa.String(256), nullable=False),
        sa.Column("pr_number", sa.Integer, nullable=True),
        sa.Column("status", sa.String(20), default="pending", nullable=False),
        sa.Column("total_issues", sa.Integer, default=0),
        sa.Column("total_cost_usd", sa.Numeric(10, 6), default=0),
        sa.Column("config", JSONB, server_default="{}"),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("started_at", sa.DateTime, nullable=True),
        sa.Column("completed_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_code_reviews_status", "code_reviews", ["status"])
    op.create_index("ix_code_reviews_repo_name", "code_reviews", ["repo_name"])
    op.create_index("ix_code_reviews_created_at", "code_reviews", ["created_at"])

    # review_findings
    op.create_table(
        "review_findings",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("review_id", UUID(as_uuid=True), sa.ForeignKey("code_reviews.id", ondelete="CASCADE"), nullable=False),
        sa.Column("agent_role", sa.String(64), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("file_path", sa.String(512), nullable=False),
        sa.Column("line_number", sa.Integer, nullable=True),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("suggested_fix", sa.Text, nullable=True),
        sa.Column("confidence", sa.Float, default=0.0),
        sa.Column("tokens_used", sa.Integer, default=0),
        sa.Column("cost_usd", sa.Numeric(10, 6), default=0),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_review_findings_review_id", "review_findings", ["review_id"])
    op.create_index("ix_review_findings_severity", "review_findings", ["severity"])

    # review_templates
    op.create_table(
        "review_templates",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(128), nullable=False, unique=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("rules", JSONB, server_default="{}"),
        sa.Column("created_by", sa.String(128), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("review_templates")
    op.drop_table("review_findings")
    op.drop_table("code_reviews")
