"""merge duplicate heads

Revision ID: c8282ca2a6f3
Revises: 7e2cdbc0897c, 9b77b76c1d4e
Create Date: 2026-07-20 16:51:56.103395

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c8282ca2a6f3'
down_revision: Union[str, Sequence[str], None] = ('7e2cdbc0897c', '9b77b76c1d4e')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
