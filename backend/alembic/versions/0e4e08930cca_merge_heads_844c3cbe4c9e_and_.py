"""Merge heads 844c3cbe4c9e and aa1368a37820

Revision ID: 0e4e08930cca
Revises: 844c3cbe4c9e, aa1368a37820
Create Date: 2026-07-14 21:42:44.903375

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0e4e08930cca'
down_revision: Union[str, Sequence[str], None] = ('844c3cbe4c9e', 'aa1368a37820')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
