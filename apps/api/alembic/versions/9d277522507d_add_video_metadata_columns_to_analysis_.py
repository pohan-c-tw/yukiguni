"""add video metadata columns to analysis_jobs

Revision ID: 9d277522507d
Revises: ce0d37adca9e
Create Date: 2026-04-20 20:33:05.996502

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9d277522507d"
down_revision: Union[str, Sequence[str], None] = "ce0d37adca9e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "analysis_jobs",
        sa.Column("video_duration_seconds", sa.Float(), nullable=True),
    )
    op.add_column(
        "analysis_jobs",
        sa.Column("video_width", sa.Integer(), nullable=True),
    )
    op.add_column(
        "analysis_jobs",
        sa.Column("video_height", sa.Integer(), nullable=True),
    )

    op.execute(
        """
        UPDATE analysis_jobs
        SET
            video_duration_seconds = 0,
            video_width = 0,
            video_height = 0
        WHERE
            video_duration_seconds IS NULL
            OR video_width IS NULL
            OR video_height IS NULL
        """
    )

    op.alter_column(
        "analysis_jobs",
        "video_duration_seconds",
        nullable=False,
    )
    op.alter_column(
        "analysis_jobs",
        "video_width",
        nullable=False,
    )
    op.alter_column(
        "analysis_jobs",
        "video_height",
        nullable=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("analysis_jobs", "video_height")
    op.drop_column("analysis_jobs", "video_width")
    op.drop_column("analysis_jobs", "video_duration_seconds")
