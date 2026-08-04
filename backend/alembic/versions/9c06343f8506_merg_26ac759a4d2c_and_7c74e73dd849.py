"""Merg 26ac759a4d2c and 7c74e73dd849

Revision ID: 9c06343f8506
Revises: 26ac759a4d2c, 7c74e73dd849
Create Date: 2026-07-28 20:33:23.359821

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9c06343f8506'
down_revision: Union[str, Sequence[str], None] = ('26ac759a4d2c', '7c74e73dd849')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
