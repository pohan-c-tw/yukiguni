"""add video metadata columns to analysis_jobs

Revision ID: 9d277522507d
Revises: ce0d37adca9e
Create Date: 2026-04-20 20:33:05.996502

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9d277522507d'
down_revision: Union[str, Sequence[str], None] = 'ce0d37adca9e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
