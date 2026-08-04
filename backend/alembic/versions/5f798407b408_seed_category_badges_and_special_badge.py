"""seed category badges and special badge

Revision ID: 5f798407b408
Revises: 5891ef139e70
Create Date: 2026-07-31 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5f798407b408'
down_revision: Union[str, Sequence[str], None] = '5891ef139e70'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# 카테고리별 5단계 칭호. condition_category는 category.code와 매칭되는 값이다.
# condition_count는 해당 카테고리 퀘스트 완료(ACCEPTED) 누적 개수 기준.
CATEGORY_BADGES = [
    # (condition_category, badge_category, [(condition_count, name, description), ...])
    ("volunteer", "봉사", [
        (1, "봉사 새싹", "봉사 퀘스트를 1회 완료하면 획득하는 칭호입니다."),
        (5, "봉사 실천가", "봉사 퀘스트를 5회 완료하면 획득하는 칭호입니다."),
        (15, "봉사 열정가", "봉사 퀘스트를 15회 완료하면 획득하는 칭호입니다."),
        (30, "봉사 마스터", "봉사 퀘스트를 30회 완료하면 획득하는 칭호입니다."),
        (50, "봉사의 전설", "봉사 퀘스트를 50회 완료한 당신에게 주어지는 칭호입니다."),
    ]),
    ("environment", "환경", [
        (1, "환경 새싹", "환경 퀘스트를 1회 완료하면 획득하는 칭호입니다."),
        (5, "그린 실천가", "환경 퀘스트를 5회 완료하면 획득하는 칭호입니다."),
        (15, "에코 지킴이", "환경 퀘스트를 15회 완료하면 획득하는 칭호입니다."),
        (30, "환경 마스터", "환경 퀘스트를 30회 완료하면 획득하는 칭호입니다."),
        (50, "지구 수호자", "환경 퀘스트를 50회 완료한 당신에게 주어지는 칭호입니다."),
    ]),
    ("sharing", "나눔", [
        (1, "나눔 새싹", "나눔 퀘스트를 1회 완료하면 획득하는 칭호입니다."),
        (5, "나눔 실천가", "나눔 퀘스트를 5회 완료하면 획득하는 칭호입니다."),
        (15, "나눔 전도사", "나눔 퀘스트를 15회 완료하면 획득하는 칭호입니다."),
        (30, "나눔 마스터", "나눔 퀘스트를 30회 완료하면 획득하는 칭호입니다."),
        (50, "나눔의 전설", "나눔 퀘스트를 50회 완료한 당신에게 주어지는 칭호입니다."),
    ]),
    ("animal", "동물", [
        (1, "동물 새싹", "동물 퀘스트를 1회 완료하면 획득하는 칭호입니다."),
        (5, "동물 친구", "동물 퀘스트를 5회 완료하면 획득하는 칭호입니다."),
        (15, "동물 지킴이", "동물 퀘스트를 15회 완료하면 획득하는 칭호입니다."),
        (30, "동물 마스터", "동물 퀘스트를 30회 완료하면 획득하는 칭호입니다."),
        (50, "동물 수호자", "동물 퀘스트를 50회 완료한 당신에게 주어지는 칭호입니다."),
    ]),
    ("community", "지역사회", [
        (1, "이웃 새싹", "지역사회 퀘스트를 1회 완료하면 획득하는 칭호입니다."),
        (5, "이웃 실천가", "지역사회 퀘스트를 5회 완료하면 획득하는 칭호입니다."),
        (15, "지역 지킴이", "지역사회 퀘스트를 15회 완료하면 획득하는 칭호입니다."),
        (30, "지역사회 마스터", "지역사회 퀘스트를 30회 완료하면 획득하는 칭호입니다."),
        (50, "우리동네 영웅", "지역사회 퀘스트를 50회 완료한 당신에게 주어지는 칭호입니다."),
    ]),
    ("other", "기타", [
        (1, "선행 새싹", "기타 퀘스트를 1회 완료하면 획득하는 칭호입니다."),
        (5, "선행 실천가", "기타 퀘스트를 5회 완료하면 획득하는 칭호입니다."),
        (15, "선행 열정가", "기타 퀘스트를 15회 완료하면 획득하는 칭호입니다."),
        (30, "선행 마스터", "기타 퀘스트를 30회 완료하면 획득하는 칭호입니다."),
        (50, "선행의 전설", "기타 퀘스트를 50회 완료한 당신에게 주어지는 칭호입니다."),
    ]),
]

# 특별 칭호 - 서로 다른 카테고리 2개 이상에서 최종 단계(condition_count=50)를 달성하면 자동 지급.
# condition_category는 category.code와 겹치지 않는 센티널 값, condition_count는
# "마스터해야 하는 카테고리 개수" 임계값으로 재해석해서 재사용한다 (badge/service.py에서 이 값을 읽어 판정).
SPECIAL_BADGE_CONDITION_CATEGORY = "__special__"
SPECIAL_BADGE = (
    2,
    "나는 정운",
    "서로 다른 카테고리 2개 이상에서 최고 단계를 달성한 당신에게 주어지는 특별한 칭호입니다.",
)


def upgrade() -> None:
    """이미 있는 (condition_category, condition_count) 조합은 건너뛰고 없는 것만 추가한다."""
    for condition_category, badge_category, tiers in CATEGORY_BADGES:
        for condition_count, name, description in tiers:
            op.execute(
                sa.text(
                    "INSERT INTO badge "
                    "(name, description, icon_url, badge_category, condition_category, condition_count) "
                    "SELECT :name, :description, :icon_url, :badge_category, :condition_category, :condition_count "
                    "WHERE NOT EXISTS ("
                    "  SELECT 1 FROM badge "
                    "  WHERE condition_category = :condition_category AND condition_count = :condition_count"
                    ")"
                ).bindparams(
                    name=name,
                    description=description,
                    icon_url=f"https://example.com/icons/badge_{condition_category}_{condition_count}.png",
                    badge_category=badge_category,
                    condition_category=condition_category,
                    condition_count=condition_count,
                )
            )

    special_count, special_name, special_description = SPECIAL_BADGE
    op.execute(
        sa.text(
            "INSERT INTO badge "
            "(name, description, icon_url, badge_category, condition_category, condition_count) "
            "SELECT :name, :description, :icon_url, :badge_category, :condition_category, :condition_count "
            "WHERE NOT EXISTS ("
            "  SELECT 1 FROM badge WHERE condition_category = :condition_category"
            ")"
        ).bindparams(
            name=special_name,
            description=special_description,
            icon_url="https://example.com/icons/badge_special_najeongwoon.png",
            badge_category="특별",
            condition_category=SPECIAL_BADGE_CONDITION_CATEGORY,
            condition_count=special_count,
        )
    )


def downgrade() -> None:
    """시드한 카테고리 배지 + 특별 배지를 제거한다. 이미 유저가 보유 중이면 FK가 막는다."""
    for condition_category, _badge_category, tiers in CATEGORY_BADGES:
        for condition_count, _name, _description in tiers:
            op.execute(
                sa.text(
                    "DELETE FROM badge WHERE condition_category = :condition_category AND condition_count = :condition_count"
                ).bindparams(condition_category=condition_category, condition_count=condition_count)
            )
    op.execute(
        sa.text("DELETE FROM badge WHERE condition_category = :condition_category").bindparams(
            condition_category=SPECIAL_BADGE_CONDITION_CATEGORY
        )
    )
