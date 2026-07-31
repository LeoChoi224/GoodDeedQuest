"""
backend/app/mypage/router.py

MyPage 도메인 API 라우터 (읽기 전용 집계 레이어, 자체 테이블 없음).
"""
from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.app.common.database import get_db
from backend.app.common.auth import get_current_user
from backend.app.common.response import APIResponse
from backend.app.mypage.schemas import (
    MyQuestAchievementResponse,
    MyProfileResponse,
    ProfileImagePresignRequest,
    ProfileImagePresignResponse,
    ProfileImageConfirmRequest,
)
from backend.app.mypage.service import (
    get_my_quest_achievements,
    get_my_profile,
    presign_profile_image,
    confirm_profile_image,
)

router = APIRouter(prefix="/mypage", tags=["MyPage"])


@router.get(
    "/quests/achievements",
    response_model=APIResponse[List[MyQuestAchievementResponse]],
    status_code=status.HTTP_200_OK,
    summary="내가 달성한 퀘스트 타임라인 조회",
    description="현재 로그인한 사용자가 완료(ACCEPTED)한 퀘스트 목록을 완료 시간 역순으로 조회합니다.",
)
def get_my_quest_achievements_endpoint(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_id = current_user.get("id") or current_user.get("user_id")
    achievements = get_my_quest_achievements(db, user_id=user_id)
    return APIResponse.ok(data=achievements, message="달성 퀘스트 타임라인 조회 성공")


# ⭐ 수정: 마이페이지 프로필 헤더(이름/칭호/레벨/연속접속일/프로필이미지)
@router.get(
    "/profile",
    response_model=APIResponse[MyProfileResponse],
    status_code=status.HTTP_200_OK,
    summary="마이페이지 프로필 헤더 조회",
    description="닉네임, 현재 장착 칭호, 레벨, 연속접속일수, 프로필 이미지를 조회합니다.",
)
def get_my_profile_endpoint(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_id = current_user.get("id") or current_user.get("user_id")
    profile = get_my_profile(db, user_id=user_id)
    return APIResponse.ok(data=profile, message="프로필 조회 성공")


@router.post(
    "/profile/image/presign",
    response_model=ProfileImagePresignResponse,
    status_code=status.HTTP_200_OK,
    summary="프로필 이미지 업로드용 presigned URL 발급",
    description="클라이언트가 S3에 직접 업로드할 수 있는 presigned PUT URL과 S3 key를 발급합니다.",
)
def presign_profile_image_endpoint(
    req: ProfileImagePresignRequest,
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user.get("id") or current_user.get("user_id")
    return presign_profile_image(user_id=user_id, content_type=req.content_type)


@router.patch(
    "/profile/image",
    response_model=APIResponse[MyProfileResponse],
    status_code=status.HTTP_200_OK,
    summary="프로필 이미지 변경 확정",
    description="presign으로 S3에 업로드를 마친 뒤, 그 s3_key를 프로필 이미지로 저장합니다.",
)
def confirm_profile_image_endpoint(
    req: ProfileImageConfirmRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_id = current_user.get("id") or current_user.get("user_id")
    profile = confirm_profile_image(db, user_id=user_id, s3_key=req.s3_key)
    return APIResponse.ok(data=profile, message="프로필 이미지 변경 성공")
