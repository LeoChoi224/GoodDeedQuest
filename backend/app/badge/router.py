"""
backend/app/badge/router.py

Badge 도메인 API 라우터.
service.py 함수들을 실제 엔드포인트로 노출한다.
"""

from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.app.common.database import get_db
from backend.app.common.auth import get_current_user
from backend.app.common.response import APIResponse
from backend.app.badge.models import UserBadge
from backend.app.badge.schemas import BadgeResponse, MyBadgeResponse
from backend.app.badge.service import (
    get_all_badges,
    get_my_badges,
    equip_badge,
    unequip_badge,
)

router = APIRouter(prefix="/badges", tags=["Badge"])


def _to_my_badge_response(user_badge: UserBadge) -> MyBadgeResponse:
    """equip/unequip이 반환하는 UserBadge ORM 객체를 MyBadgeResponse로 변환한다."""
    return MyBadgeResponse(
        badge_id=user_badge.badge.badge_id,
        name=user_badge.badge.name,
        description=user_badge.badge.description,
        icon_url=user_badge.badge.icon_url,
        badge_category=user_badge.badge.badge_category,
        is_equipped=user_badge.is_equipped,
        awarded_at=user_badge.awarded_at,
    )


@router.get(
    "",
    response_model=APIResponse[List[BadgeResponse]],
    status_code=status.HTTP_200_OK,
    summary="전체 배지 도감 조회",
    description="미보유 배지를 포함한 전체 배지 목록을 조회합니다. 각 배지의 보유 여부(is_owned)가 함께 내려갑니다.",
)
def get_badges(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_id = current_user.get("id") or current_user.get("user_id")
    badges = get_all_badges(db, user_id=user_id)
    return APIResponse.ok(data=badges, message="전체 배지 도감 조회 성공")


@router.get(
    "/my",
    response_model=APIResponse[List[MyBadgeResponse]],
    status_code=status.HTTP_200_OK,
    summary="내가 보유한 배지 목록 조회",
    description="현재 로그인한 사용자가 보유한 배지 목록을 조회합니다.",
)
def get_my_badges_endpoint(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_id = current_user.get("id") or current_user.get("user_id")
    my_badges = get_my_badges(db, user_id=user_id)
    return APIResponse.ok(data=my_badges, message="내 배지 목록 조회 성공")


@router.patch(
    "/{badge_id}/equip",
    response_model=APIResponse[MyBadgeResponse],
    status_code=status.HTTP_200_OK,
    summary="배지 장착",
    description="보유한 배지를 장착합니다. 유저당 최대 1개만 장착 가능하며, 기존에 장착 중이던 배지는 자동으로 해제됩니다.",
)
def equip_badge_endpoint(
    badge_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_id = current_user.get("id") or current_user.get("user_id")
    user_badge = equip_badge(db, user_id=user_id, badge_id=badge_id)
    return APIResponse.ok(data=_to_my_badge_response(user_badge), message="배지 장착 성공")


@router.patch(
    "/{badge_id}/unequip",
    response_model=APIResponse[MyBadgeResponse],
    status_code=status.HTTP_200_OK,
    summary="배지 장착 해제",
    description="장착 중인 배지를 해제합니다.",
)
def unequip_badge_endpoint(
    badge_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_id = current_user.get("id") or current_user.get("user_id")
    user_badge = unequip_badge(db, user_id=user_id, badge_id=badge_id)
    return APIResponse.ok(data=_to_my_badge_response(user_badge), message="배지 장착 해제 성공")
