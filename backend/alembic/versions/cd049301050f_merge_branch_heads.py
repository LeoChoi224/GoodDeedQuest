"""merge branch heads

Revision ID: cd049301050f
Revises: 4f3c48026a4c, bc95f2a0c3b6
Create Date: 2026-07-17 20:00:06.681941

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cd049301050f'
down_revision: Union[str, Sequence[str], None] = ('4f3c48026a4c', 'bc95f2a0c3b6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
