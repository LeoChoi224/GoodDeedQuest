"""merge heads

Revision ID: d9e371890710
Revises: 4a6252b8334f, 70aadfa6efeb
Create Date: 2026-07-31 17:42:01.788631

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd9e371890710'
down_revision: Union[str, Sequence[str], None] = ('4a6252b8334f', '70aadfa6efeb')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
