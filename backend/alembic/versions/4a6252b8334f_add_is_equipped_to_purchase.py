"""add is_equipped to purchase

Revision ID: 4a6252b8334f
Revises: 5f798407b408
Create Date: 2026-07-31 08:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4a6252b8334f'
down_revision: Union[str, Sequence[str], None] = '5f798407b408'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('purchase', sa.Column('is_equipped', sa.Boolean(), server_default='false', nullable=False, comment='유저의 현재 장착 여부'))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('purchase', 'is_equipped')
