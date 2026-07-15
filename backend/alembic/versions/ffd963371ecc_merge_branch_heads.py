"""merge branch heads

Revision ID: ffd963371ecc
Revises: 844c3cbe4c9e, aa1368a37820
Create Date: 2026-07-14 17:52:45.796638

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ffd963371ecc'
down_revision: Union[str, Sequence[str], None] = ('844c3cbe4c9e', 'aa1368a37820')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
