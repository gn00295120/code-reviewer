"""Add platform field to code_reviews

Revision ID: 007
Revises: 006
Create Date: 2026-03-21
"""

from typing import Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic
revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    op.add_column(
        "code_reviews",
        sa.Column("platform", sa.String(20), nullable=False, server_default="github"),
    )
    op.create_index("ix_code_reviews_platform", "code_reviews", ["platform"])


def downgrade() -> None:
    op.drop_index("ix_code_reviews_platform", table_name="code_reviews")
    op.drop_column("code_reviews", "platform")
