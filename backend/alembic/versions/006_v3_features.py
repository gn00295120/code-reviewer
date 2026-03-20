"""v3.0 — Self-hosting Agent Company, DAO Governance, AI Science Engine

Revision ID: 006
Revises: 005
Create Date: 2026-03-20
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # agent_companies
    # ------------------------------------------------------------------
    op.create_table(
        "agent_companies",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("owner", sa.String(256), nullable=True),
        sa.Column("org_chart", JSONB, nullable=False, server_default="{}"),
        sa.Column("processes", JSONB, nullable=False, server_default="[]"),
        sa.Column("shared_state", JSONB, nullable=False, server_default="{}"),
        sa.Column("budget_usd", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("spent_usd", sa.Numeric(10, 6), nullable=False, server_default="0"),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("agent_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_agent_companies_status", "agent_companies", ["status"])
    op.create_index("ix_agent_companies_owner", "agent_companies", ["owner"])
    op.create_index("ix_agent_companies_created_at", "agent_companies", ["created_at"])

    # ------------------------------------------------------------------
    # company_agents
    # ------------------------------------------------------------------
    op.create_table(
        "company_agents",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "company_id",
            UUID(as_uuid=True),
            sa.ForeignKey("agent_companies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(128), nullable=False),
        sa.Column("title", sa.String(256), nullable=True),
        sa.Column("model", sa.String(128), nullable=False, server_default="claude-sonnet"),
        sa.Column("system_prompt", sa.Text, nullable=True),
        sa.Column("capabilities", JSONB, nullable=False, server_default="[]"),
        sa.Column("reports_to", UUID(as_uuid=True), sa.ForeignKey("company_agents.id"), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="idle"),
        sa.Column("total_tasks", sa.Integer, nullable=False, server_default="0"),
        sa.Column("total_cost_usd", sa.Numeric(10, 6), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_company_agents_company_id", "company_agents", ["company_id"])
    op.create_index("ix_company_agents_role", "company_agents", ["role"])
    op.create_index("ix_company_agents_status", "company_agents", ["status"])

    # ------------------------------------------------------------------
    # proposals
    # ------------------------------------------------------------------
    op.create_table(
        "proposals",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "company_id",
            UUID(as_uuid=True),
            sa.ForeignKey("agent_companies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("proposal_type", sa.String(64), nullable=False),
        sa.Column("proposed_changes", JSONB, nullable=False, server_default="{}"),
        sa.Column(
            "proposed_by",
            UUID(as_uuid=True),
            sa.ForeignKey("company_agents.id"),
            nullable=True,
        ),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("votes_for", sa.Integer, nullable=False, server_default="0"),
        sa.Column("votes_against", sa.Integer, nullable=False, server_default="0"),
        sa.Column("quorum_required", sa.Integer, nullable=False, server_default="3"),
        sa.Column("deadline", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_proposals_company_id", "proposals", ["company_id"])
    op.create_index("ix_proposals_status", "proposals", ["status"])
    op.create_index("ix_proposals_proposal_type", "proposals", ["proposal_type"])

    # ------------------------------------------------------------------
    # votes
    # ------------------------------------------------------------------
    op.create_table(
        "votes",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "proposal_id",
            UUID(as_uuid=True),
            sa.ForeignKey("proposals.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "voter_id",
            UUID(as_uuid=True),
            sa.ForeignKey("company_agents.id"),
            nullable=False,
        ),
        sa.Column("vote", sa.String(10), nullable=False),
        sa.Column("reason", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_votes_proposal_id", "votes", ["proposal_id"])
    op.create_index("ix_votes_voter_id", "votes", ["voter_id"])
    # Unique constraint: one vote per voter per proposal
    op.create_unique_constraint("uq_votes_proposal_voter", "votes", ["proposal_id", "voter_id"])

    # ------------------------------------------------------------------
    # experiments
    # ------------------------------------------------------------------
    op.create_table(
        "experiments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "company_id",
            UUID(as_uuid=True),
            sa.ForeignKey("agent_companies.id"),
            nullable=True,
        ),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("hypothesis", sa.Text, nullable=True),
        sa.Column("methodology", JSONB, nullable=False, server_default="{}"),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("variables", JSONB, nullable=False, server_default="{}"),
        sa.Column("results", JSONB, nullable=False, server_default="{}"),
        sa.Column("analysis", sa.Text, nullable=True),
        sa.Column("conclusion", sa.Text, nullable=True),
        sa.Column("confidence", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("total_runs", sa.Integer, nullable=False, server_default="0"),
        sa.Column("total_cost_usd", sa.Numeric(10, 6), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_experiments_status", "experiments", ["status"])
    op.create_index("ix_experiments_company_id", "experiments", ["company_id"])
    op.create_index("ix_experiments_created_at", "experiments", ["created_at"])

    # ------------------------------------------------------------------
    # experiment_runs
    # ------------------------------------------------------------------
    op.create_table(
        "experiment_runs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "experiment_id",
            UUID(as_uuid=True),
            sa.ForeignKey("experiments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("run_number", sa.Integer, nullable=False),
        sa.Column("parameters", JSONB, nullable=False, server_default="{}"),
        sa.Column("results", JSONB, nullable=False, server_default="{}"),
        sa.Column("metrics", JSONB, nullable=False, server_default="{}"),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("duration_seconds", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("cost_usd", sa.Numeric(10, 6), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_experiment_runs_experiment_id", "experiment_runs", ["experiment_id"])
    op.create_index("ix_experiment_runs_status", "experiment_runs", ["status"])


def downgrade() -> None:
    op.drop_table("experiment_runs")
    op.drop_table("experiments")
    op.drop_unique_constraint("uq_votes_proposal_voter", "votes")
    op.drop_table("votes")
    op.drop_table("proposals")
    op.drop_table("company_agents")
    op.drop_table("agent_companies")
