"""make video metadata nullable

Revision ID: bf6f1fb9b6e3
Revises: a5cc31e9b4f6
Create Date: 2026-04-21 02:05:00.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "bf6f1fb9b6e3"
down_revision: Union[str, Sequence[str], None] = "a5cc31e9b4f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        "analysis_jobs",
        "video_duration_seconds",
        nullable=True,
    )
    op.alter_column(
        "analysis_jobs",
        "video_width",
        nullable=True,
    )
    op.alter_column(
        "analysis_jobs",
        "video_height",
        nullable=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
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
        "video_height",
        nullable=False,
    )
    op.alter_column(
        "analysis_jobs",
        "video_width",
        nullable=False,
    )
    op.alter_column(
        "analysis_jobs",
        "video_duration_seconds",
        nullable=False,
    )
