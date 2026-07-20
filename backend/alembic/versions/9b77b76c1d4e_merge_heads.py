"""merge heads

Revision ID: 9b77b76c1d4e
Revises: 020f241889c6, eac03d27aef5
Create Date: 2026-07-20 14:27:36.943081

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9b77b76c1d4e'
down_revision: Union[str, Sequence[str], None] = ('020f241889c6', 'eac03d27aef5')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
