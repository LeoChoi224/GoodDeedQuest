"""merge heads

Revision ID: 05eb01e7b2b2
Revises: 815da3e7c6aa, a90a9ea8f51c
Create Date: 2026-08-02 13:03:10.476856

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '05eb01e7b2b2'
down_revision: Union[str, Sequence[str], None] = ('815da3e7c6aa', 'a90a9ea8f51c')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
