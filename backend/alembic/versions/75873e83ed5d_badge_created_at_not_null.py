"""badge_created_at_not_null

Revision ID: 75873e83ed5d
Revises: 4416cb806eb1
Create Date: 2026-07-21 09:57:50.056214

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '75873e83ed5d'
down_revision: Union[str, Sequence[str], None] = '4416cb806eb1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("UPDATE badge SET created_at = now() WHERE created_at IS NULL")  # ⭐ 추가
    op.alter_column('badge', 'created_at', nullable=False)  # ⭐ 추가


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('badge', 'created_at', nullable=True)  # ⭐ 추가