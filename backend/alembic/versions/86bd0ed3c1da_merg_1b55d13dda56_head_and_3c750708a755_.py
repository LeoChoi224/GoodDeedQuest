"""Merg 1b55d13dda56 (head) and 3c750708a755 (head)

Revision ID: 86bd0ed3c1da
Revises: 1b55d13dda56, 3c750708a755
Create Date: 2026-08-04 04:57:43.592754

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '86bd0ed3c1da'
down_revision: Union[str, Sequence[str], None] = ('1b55d13dda56', '3c750708a755')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
