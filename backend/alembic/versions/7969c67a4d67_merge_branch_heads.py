"""merge branch heads

Revision ID: 7969c67a4d67
Revises: 24105004dbbf, 6b233f24a890
Create Date: 2026-07-28 16:13:26.894686

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7969c67a4d67'
down_revision: Union[str, Sequence[str], None] = ('24105004dbbf', '6b233f24a890')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
