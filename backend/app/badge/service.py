"""
backend/app/badge/service.py

Badge 도메인 서비스 레이어.
라우터(엔드포인트)와 models/schemas 사이에서 실제 "비즈니스 로직"을 담당하는 계층.

포함 기능:
- 전체 배지 도감 조회 (미보유 포함, is_owned 계산)
- 내가 보유한 배지 목록 조회
- 배지 장착 / 해제 (유저당 최대 1개 장착 정책)
- 카테고리 기반 배지 자동 지급 (check_and_award_badges)

컨벤션:
- DB 세션은 함수 인자로 직접 주입받는다 (shop/service.py 패턴과 동일).
- 존재하지 않는 리소스에 대한 예외는 shop/service.py와 동일하게 서비스 레이어에서
  바로 HTTPException(404)을 raise한다 (라우터에서 별도 변환 불필요).
"""

from typing import List

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from backend.app.badge.models import Badge, UserBadge
from backend.app.badge.schemas import BadgeResponse, MyBadgeResponse
from backend.app.quest.models import Quest, Category
from backend.app.quest_verification.models import QuestSubmission
from backend.app.quest_verification.enums import SubmissionStatus

# ⭐ 수정: 모든 유저가 처음부터 장착하고 시작하는 기본 칭호.
# condition_category를 실제 Category.code와 절대 겹치지 않는 값으로 둬서
# check_and_award_badges()의 카테고리 기반 자동 지급 대상에 섞이지 않게 한다.
DEFAULT_BADGE_NAME = "선행 초보자"
DEFAULT_BADGE_CONDITION_CATEGORY = "__default__"


# ---------------------------------------------------------------------------
# 마이페이지 프로필 헤더용 - 기본 칭호 보장 + 현재 장착 칭호 조회
# ---------------------------------------------------------------------------

def _get_or_create_default_badge(db: Session) -> Badge:
    badge = db.query(Badge).filter(Badge.name == DEFAULT_BADGE_NAME).first()
    if badge:
        return badge

    badge = Badge(
        name=DEFAULT_BADGE_NAME,
        description="선행퀘스트에 첫발을 내딛은 모든 사람에게 주어지는 기본 칭호입니다.",
        icon_url="https://cdn-icons-png.flaticon.com/512/2917/2917995.png",
        badge_category="기본",
        condition_category=DEFAULT_BADGE_CONDITION_CATEGORY,
        condition_count=0,
    )
    db.add(badge)
    db.commit()
    db.refresh(badge)
    return badge


def ensure_default_badge_equipped(db: Session, user_id: int) -> None:
    """
    유저가 장착 중인 뱃지(칭호)가 하나도 없으면 기본 칭호("선행 초보자")를 보유/장착
    시켜준다. 신규 가입 시점이 아니라 프로필 조회 시점에 지연 실행되므로 auth 도메인
    (회원가입 흐름)을 건드리지 않고도 "처음부터 무조건 장착된 상태"를 보장한다.
    """
    already_equipped = (
        db.query(UserBadge.user_badge_id)
        .filter(UserBadge.user_id == user_id, UserBadge.is_equipped == True)
        .first()
    )
    if already_equipped:
        return

    default_badge = _get_or_create_default_badge(db)
    owned = (
        db.query(UserBadge)
        .filter(UserBadge.user_id == user_id, UserBadge.badge_id == default_badge.badge_id)
        .first()
    )
    if owned:
        owned.is_equipped = True
    else:
        db.add(UserBadge(user_id=user_id, badge_id=default_badge.badge_id, is_equipped=True))
    db.commit()


def get_equipped_badge_name(db: Session, user_id: int) -> str:
    """마이페이지 프로필 헤더에 표시할, 현재 장착 중인 칭호(Badge.name)를 조회한다."""
    ensure_default_badge_equipped(db, user_id)
    equipped = (
        db.query(Badge.name)
        .join(UserBadge, UserBadge.badge_id == Badge.badge_id)
        .filter(UserBadge.user_id == user_id, UserBadge.is_equipped == True)
        .first()
    )
    return equipped[0] if equipped else DEFAULT_BADGE_NAME


# ---------------------------------------------------------------------------
# 배지 도감 조회
# ---------------------------------------------------------------------------

def get_all_badges(db: Session, user_id: int) -> List[BadgeResponse]:
    """
    전체 Badge 목록을 조회하고, 각 배지에 대해 현재 유저의 보유 여부(is_owned)를
    계산해서 채워 넣는다. is_owned는 DB 컬럼이 아니라 이 함수에서 계산되는 값이다.
    """
    badges = db.query(Badge).all()

    # 유저가 보유한 badge_id만 별도로 조회해서 set으로 만들어 둠 (매 배지마다 쿼리 날리지 않기 위함)
    owned_badge_ids = {
        row.badge_id
        for row in db.query(UserBadge.badge_id).filter(UserBadge.user_id == user_id).all()
    }

    return [
        BadgeResponse(
            badge_id=badge.badge_id,
            name=badge.name,
            description=badge.description,
            icon_url=badge.icon_url,
            badge_category=badge.badge_category,
            is_owned=badge.badge_id in owned_badge_ids,
        )
        for badge in badges
    ]


def get_my_badges(db: Session, user_id: int) -> List[MyBadgeResponse]:
    """
    현재 유저가 보유한 UserBadge 목록을 Badge와 조인해서 조회한다.
    joinedload로 badge 정보를 함께 로드해서 N+1 쿼리를 방지한다.
    """
    user_badges = (
        db.query(UserBadge)
        .options(joinedload(UserBadge.badge))
        .filter(UserBadge.user_id == user_id)
        .all()
    )

    return [
        MyBadgeResponse(
            badge_id=user_badge.badge.badge_id,
            name=user_badge.badge.name,
            description=user_badge.badge.description,
            icon_url=user_badge.badge.icon_url,
            badge_category=user_badge.badge.badge_category,
            is_equipped=user_badge.is_equipped,
            awarded_at=user_badge.awarded_at,
        )
        for user_badge in user_badges
    ]


# ---------------------------------------------------------------------------
# 배지 장착 / 해제 (유저당 최대 1개 장착 정책)
# ---------------------------------------------------------------------------

def equip_badge(db: Session, user_id: int, badge_id: int) -> UserBadge:
    """
    유저가 보유한 배지를 장착한다. 유저당 장착 가능한 배지는 최대 1개이므로,
    기존에 장착되어 있던 배지가 있으면 먼저 전부 해제한 뒤 대상 배지를 장착한다.
    """
    target = (
        db.query(UserBadge)
        .filter(UserBadge.user_id == user_id, UserBadge.badge_id == badge_id)
        .first()
    )
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"보유하지 않은 배지입니다. (badge_id={badge_id})",
        )

    # 유저당 최대 1개 장착 정책 - 기존에 장착 중이던 배지를 전부 해제
    # synchronize_session=False: target은 아래에서 명시적으로 다시 세팅하므로 세션 동기화 불필요
    db.query(UserBadge).filter(
        UserBadge.user_id == user_id,
        UserBadge.is_equipped == True,
    ).update({"is_equipped": False}, synchronize_session=False)

    target.is_equipped = True
    db.commit()
    db.refresh(target)
    return target


def unequip_badge(db: Session, user_id: int, badge_id: int) -> UserBadge:
    """
    장착 중인 배지를 해제한다. 대상이 애초에 장착 상태가 아니면 404를 반환한다.
    """
    target = (
        db.query(UserBadge)
        .filter(
            UserBadge.user_id == user_id,
            UserBadge.badge_id == badge_id,
            UserBadge.is_equipped == True,
        )
        .first()
    )
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"장착된 배지가 아닙니다. (badge_id={badge_id})",
        )

    target.is_equipped = False
    db.commit()
    db.refresh(target)
    return target


# ---------------------------------------------------------------------------
# 카테고리 기반 배지 자동 지급 (award)
# ---------------------------------------------------------------------------

def check_and_award_badges(db: Session, user_id: int, category_code: str) -> List[Badge]:
    """
    유저가 특정 카테고리 퀘스트를 완료(ACCEPTED)했을 때 호출.
    해당 카테고리 완료 횟수를 계산해 조건을 만족하는 미보유 배지를 지급한다.
    """
    completed_count = (
        db.query(func.count(QuestSubmission.submission_id))
        .join(Quest, QuestSubmission.quest_id == Quest.quest_id)
        .join(Category, Quest.category_id == Category.category_id)
        .filter(
            QuestSubmission.user_id == user_id,
            Category.code == category_code,
            QuestSubmission.final_status == SubmissionStatus.ACCEPTED,
        )
        .scalar()
    )

    owned_badge_ids = {
        row.badge_id
        for row in db.query(UserBadge.badge_id).filter(UserBadge.user_id == user_id).all()
    }

    eligible_badges = (
        db.query(Badge)
        .filter(
            Badge.condition_category == category_code,
            Badge.condition_count <= completed_count,
            Badge.badge_id.notin_(owned_badge_ids),
        )
        .all()
    )

    if not eligible_badges:
        return []

    for badge in eligible_badges:
        db.add(UserBadge(user_id=user_id, badge_id=badge.badge_id, is_equipped=False))

    db.commit()
    return eligible_badges
