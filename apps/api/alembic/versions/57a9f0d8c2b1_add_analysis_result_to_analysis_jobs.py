"""add analysis result to analysis_jobs

Revision ID: 57a9f0d8c2b1
Revises: bf6f1fb9b6e3
Create Date: 2026-04-24 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "57a9f0d8c2b1"
down_revision: Union[str, Sequence[str], None] = "bf6f1fb9b6e3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "analysis_jobs",
        sa.Column(
            "analysis_result",
            postgresql.JSONB(),
            nullable=True,
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("analysis_jobs", "analysis_result")
