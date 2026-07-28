"""seed remaining categories

Revision ID: 7c74e73dd849
Revises: 24105004dbbf
Create Date: 2026-07-26 22:57:08.015904

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7c74e73dd849'
down_revision: Union[str, Sequence[str], None] = '24105004dbbf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# 프론트 CATEGORY_DEFS 6종 중 DB에 없던 것들. code는 아이콘 매칭용 키다.
CATEGORIES = [
    ("봉사", "volunteer"),
    ("나눔", "sharing"),
    ("동물", "animal"),
    ("지역사회", "community"),
    ("기타", "other"),
]


def upgrade() -> None:
    """없는 카테고리만 추가한다 (이미 있으면 건너뜀)."""
    for name, code in CATEGORIES:
        op.execute(
            sa.text(
                "INSERT INTO category (name, code, icon_url, is_active) "
                "SELECT :name, :code, :icon, true "
                "WHERE NOT EXISTS (SELECT 1 FROM category WHERE code = :code)"
            ).bindparams(
                name=name,
                code=code,
                icon=f"https://example.com/icons/{code}.png",
            )
        )


def downgrade() -> None:
    """추가했던 카테고리를 제거한다. 사용 중인 퀘스트가 있으면 FK가 막는다."""
    for _, code in CATEGORIES:
        op.execute(
            sa.text("DELETE FROM category WHERE code = :code").bindparams(code=code)
        )
