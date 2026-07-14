"""merge branch heads

Revision ID: ced371da50ea
Revises: 72dd988b3ae2, 91735051701b
Create Date: 2026-07-14 12:18:18.860446

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ced371da50ea'
down_revision: Union[str, Sequence[str], None] = ('72dd988b3ae2', '91735051701b')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
