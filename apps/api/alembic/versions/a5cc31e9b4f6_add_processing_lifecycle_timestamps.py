"""add processing lifecycle timestamps

Revision ID: a5cc31e9b4f6
Revises: 9d277522507d
Create Date: 2026-04-20 20:56:41.994804

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a5cc31e9b4f6"
down_revision: Union[str, Sequence[str], None] = "9d277522507d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "analysis_jobs",
        sa.Column("processing_started_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )
    op.add_column(
        "analysis_jobs",
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )
    op.add_column(
        "analysis_jobs",
        sa.Column("failed_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("analysis_jobs", "failed_at")
    op.drop_column("analysis_jobs", "completed_at")
    op.drop_column("analysis_jobs", "processing_started_at")
