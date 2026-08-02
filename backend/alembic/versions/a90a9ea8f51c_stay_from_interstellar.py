"""Stay! from interstellar

Revision ID: a90a9ea8f51c
Revises: d9e371890710
Create Date: 2026-08-02 15:23:31.945945

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a90a9ea8f51c'
down_revision: Union[str, Sequence[str], None] = 'd9e371890710'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """submissionstatus 열거형에 ON_HOLD 를 추가한다."""
    # 【판단】 PostgreSQL 은 열거형에 값을 추가하는 작업을 다른 작업과 같은
    #        트랜잭션에 담지 못한다. alembic 은 기본적으로 트랜잭션으로 감싸므로
    #        먼저 끊어줘야 한다. 이 COMMIT 이 없으면 마이그레이션이 실패한다.
    op.execute("COMMIT")
    op.execute("ALTER TYPE submissionstatus ADD VALUE IF NOT EXISTS 'ON_HOLD'")


def downgrade() -> None:
    """되돌리지 않는다.

    PostgreSQL 에는 열거형에서 값을 빼는 기능이 없다. 되돌리려면 타입을 새로
    만들고 컬럼을 옮긴 뒤 옛 타입을 지워야 하는데, 그 사이 ON_HOLD 인 행이
    있으면 데이터가 깨진다. 값이 하나 더 있어도 해롭지 않으므로 그대로 둔다.
    """
    pass