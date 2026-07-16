"""add user fk to shortform

Revision ID: 4f3c48026a4c
Revises: f828ee80f9bb
Create Date: 2026-07-16 16:04:53.716199

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '4f3c48026a4c'
down_revision: Union[str, Sequence[str], None] = 'f828ee80f9bb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("DROP TYPE IF EXISTS short_form_status_enum")
    op.rename_table('shortform', 'short_form')
    op.execute("ALTER TYPE shortform_status_enum RENAME TO short_form_status_enum")
    op.create_foreign_key(None, 'short_form', 'user', ['user_id'], ['user_id'])
    op.create_index(op.f('ix_short_form_user_id'), 'short_form', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_short_form_user_id'), table_name='short_form')
    op.drop_constraint(None, 'short_form', type_='foreignkey')
    op.execute("ALTER TYPE short_form_status_enum RENAME TO shortform_status_enum")
    op.rename_table('short_form', 'shortform')