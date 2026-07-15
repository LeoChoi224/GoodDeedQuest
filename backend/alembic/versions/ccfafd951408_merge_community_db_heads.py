"""merge community db heads

Revision ID: ccfafd951408
Revises: 3105b479d4a5, fc8eb270aee5
Create Date: 2026-07-15 09:41:33.136734

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ccfafd951408'
down_revision: Union[str, Sequence[str], None] = ('3105b479d4a5', 'fc8eb270aee5')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
