"""merge branch heads

Revision ID: 8595ff5e793f
Revises: c54f214612ce, c8282ca2a6f3
Create Date: 2026-07-20 17:32:02.730015

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8595ff5e793f'
down_revision: Union[str, Sequence[str], None] = ('c54f214612ce', 'c8282ca2a6f3')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
