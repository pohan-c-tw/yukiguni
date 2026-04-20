"""add processing lifecycle timestamps

Revision ID: a5cc31e9b4f6
Revises: 9d277522507d
Create Date: 2026-04-20 20:56:41.994804

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a5cc31e9b4f6'
down_revision: Union[str, Sequence[str], None] = '9d277522507d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
