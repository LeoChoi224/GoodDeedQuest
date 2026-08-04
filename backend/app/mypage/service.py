"""
backend/app/mypage/service.py

MyPage 도메인 서비스 레이어 (읽기 전용 집계).
Quest/QuestSubmission/User는 각각 다른 담당자 소유 모델이므로 조회 또는(프로필 이미지에
한해) 이미 존재하는 컬럼에 대한 단순 UPDATE만 수행하고, 테이블 구조는 건드리지 않는다.

컨벤션:
- DB 세션은 함수 인자로 직접 주입받는다 (badge/service.py 패턴과 동일).
"""
import uuid
from datetime import datetime, timedelta
from typing import List, Optional
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from backend.app.mypage.schemas import (
    MyQuestAchievementResponse,
    MyProfileResponse,
    ProfileImagePresignResponse,
    ProfileUpdateRequest,  # ⭐ 수정
)
from backend.app.quest.models import Quest
from backend.app.quest_verification.models import QuestSubmission
from backend.app.quest_verification.enums import SubmissionStatus
from backend.app.auth.models import User
from backend.app.auth.service import record_daily_user_activity  # ⭐ 수정: 마이페이지 진입도 "오늘 접속"으로 기록
from backend.app.community.models import UserActivityLog
from backend.app.badge.service import get_equipped_badge_name
from backend.app.shop.models import Purchase, Item  # ⭐ 수정: 장착 중인 프로필 테두리 조회용
from backend.app.shop.enums import PurchaseStatus
from backend.app.common.repository import DatabaseRepository  # ⭐ 수정
from backend.app.common.s3_client import generate_upload_presigned_url, generate_download_presigned_url

KST = ZoneInfo("Asia/Seoul")


def get_my_quest_achievements(db: Session, user_id: int) -> List[MyQuestAchievementResponse]:
    """
    유저가 완료(ACCEPTED)한 퀘스트 제출 내역을 Quest와 조인해서 완료 시간(submitted_at)
    역순으로 조회한다. growth/router.py::_get_weekly_xp_graph와 동일한 필터 조건을 사용한다.
    """
    rows = (
        db.query(QuestSubmission, Quest)
        .join(Quest, Quest.quest_id == QuestSubmission.quest_id)
        .options(joinedload(Quest.category))
        .filter(
            QuestSubmission.user_id == user_id,
            QuestSubmission.final_status == SubmissionStatus.ACCEPTED,
        )
        .order_by(QuestSubmission.submitted_at.desc())
        .all()
    )

    return [
        MyQuestAchievementResponse(
            submission_id=submission.submission_id,  # ⭐ 수정
            quest_id=quest.quest_id,
            title=quest.quest_title,
            description=quest.quest_description,
            category_code=quest.category.code,
            completed_at=submission.submitted_at,
            reward_point=quest.reward_point,
            reward_exp=quest.reward_exp,
        )
        for submission, quest in rows
    ]


# ⭐ 수정: 마이페이지 프로필 헤더(이름/칭호/레벨/연속접속일/프로필이미지)
def _compute_daily_streak(db: Session, user_id: int) -> int:
    """
    User.daily_streak 컬럼은 어떤 로그인/퀘스트 완료 흐름에서도 갱신되지 않는 죽은 값이라
    신뢰할 수 없다 - 실제 접속 기록인 user_activity_log.access_date를 최신순으로 훑어
    매 요청마다 연속 접속일수를 계산한다. 오늘 접속 기록이 아직 없어도(어제까지 연속이면)
    스트릭이 끊긴 것으로 보지 않는다.
    """
    rows = (
        db.query(UserActivityLog.access_date)
        .filter(UserActivityLog.user_id == user_id)
        .order_by(UserActivityLog.access_date.desc())
        .all()
    )
    if not rows:
        return 0

    dates = [row[0] for row in rows]
    today = datetime.now(KST).date()
    expected = today if dates[0] == today else today - timedelta(days=1)
    if dates[0] != expected:
        return 0

    streak = 0
    for d in dates:
        if d != expected:
            break
        streak += 1
        expected -= timedelta(days=1)
    return streak


# ⭐ 수정: 현재 장착 중인 프로필 테두리 아이템의 이미지 URL (없으면 None)
def _get_equipped_border_image_url(db: Session, user_id: int) -> Optional[str]:
    row = (
        db.query(Item.image_url)
        .join(Purchase, Purchase.item_id == Item.item_id)
        .filter(
            Purchase.user_id == user_id,
            Purchase.status == PurchaseStatus.COMPLETED,
            Purchase.is_equipped == True,
        )
        .first()
    )
    return row[0] if row else None


def get_my_profile(db: Session, user_id: int) -> MyProfileResponse:
    user = db.query(User).filter(User.user_id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="사용자를 찾을 수 없습니다.")

    # ⭐ 수정: 접속 기록은 그동안 로그인(POST /auth/login) 시에만 남았는데, 프론트가
    # 토큰을 최대 7일 보관하며 재로그인 없이 앱을 계속 쓰는 구조라 실제로는 로그인한
    # 첫날 이후로 daily_streak가 갱신되지 않는 문제가 있었다. 이 화면(마이페이지) 진입도
    # "오늘 접속"으로 잡아서, 로그인 여부와 무관하게 실제 사용일마다 기록이 쌓이게 한다.
    record_daily_user_activity(DatabaseRepository(User, db), user_id)
    db.commit()

    display_image_url = user.profile_image_url
    if display_image_url and not display_image_url.startswith("http"):
        # 이 도메인의 프로필 이미지 업로드 플로우로 저장된 값은 URL이 아니라 S3 key다
        # (외부 URL은 그대로, S3 key는 요청마다 presign) - short_form.get_eligible_media와
        # 동일한 판별 방식.
        display_image_url = generate_download_presigned_url(display_image_url)

    return MyProfileResponse(
        nickname=user.nickname,
        title=get_equipped_badge_name(db, user_id),
        current_level=user.current_level,
        daily_streak=_compute_daily_streak(db, user_id),
        equipped_border_image_url=_get_equipped_border_image_url(db, user_id),
        profile_image_url=display_image_url,
        category=user.category,  # ⭐ 수정
    )


# ⭐ 수정: 마이페이지 프로필 수정(닉네임/관심카테고리 부분 업데이트) - User 도메인 소유 컬럼이라
# 모델은 건드리지 않고 이미 존재하는 nickname/category 컬럼만 사용한다. 중복 닉네임 검사는
# 회원가입 플로우에도 아직 없는 기능이라 이 범위에서는 추가하지 않는다.
def update_my_profile(db: Session, user_id: int, req: ProfileUpdateRequest) -> MyProfileResponse:
    user = db.query(User).filter(User.user_id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="사용자를 찾을 수 없습니다.")

    if req.nickname is not None:
        user.nickname = req.nickname.strip()
    if req.category is not None:
        user.category = req.category

    db.commit()
    return get_my_profile(db, user_id)


def presign_profile_image(user_id: int, content_type: str) -> ProfileImagePresignResponse:
    ext = "png" if content_type == "image/png" else "jpg"
    s3_key = f"profile/{user_id}/{uuid.uuid4()}.{ext}"
    upload_url = generate_upload_presigned_url(s3_key, content_type)
    return ProfileImagePresignResponse(upload_url=upload_url, s3_key=s3_key)


def confirm_profile_image(db: Session, user_id: int, s3_key: str) -> MyProfileResponse:
    user = db.query(User).filter(User.user_id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="사용자를 찾을 수 없습니다.")

    user.profile_image_url = s3_key
    db.commit()
    return get_my_profile(db, user_id)
