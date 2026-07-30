"""I'm trust

Revision ID: 2fc927449bab
Revises: 9c06343f8506
Create Date: 2026-07-30 14:14:47.217763

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2fc927449bab'
down_revision: Union[str, Sequence[str], None] = '9c06343f8506'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
