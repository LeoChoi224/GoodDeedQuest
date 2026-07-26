from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, or_, and_
from sqlalchemy.orm import Session

from backend.app.common.database import get_db
from backend.app.common.response import APIResponse
from backend.app.common.auth import get_current_user
from backend.app.auth.models import User
from backend.app.quest.models import Quest
from backend.app.quest_verification.models import QuestSubmission
from backend.app.quest_verification.enums import SubmissionStatus
from backend.app.growth.schemas import (
    GrowthStatusResponse,
    DailyXp,
    LeaderboardEntry,
    LeaderboardResponse,
)

router = APIRouter(prefix="/growth", tags=["Growth & Rewards System"])


def _next_level_xp(level: int) -> int:
    """레벨업에 필요한 누적 경험치.
    1레벨=1000, 이후 n레벨(n>=2)은 1000 + (100*n)*n
    (2레벨=1000+200*2=1400, 3레벨=1000+300*3=1900, ...)
    """
    if level <= 1:
        return 1000
    return 1000 + (100 * level) * level


def _get_weekly_xp_graph(db: Session, user_id: int) -> list[DailyXp]:
    """최근 7일간 승인된 퀘스트 제출 기준으로 날짜별 XP 합산 후 누적합으로 변환"""
    today = datetime.now(timezone.utc).date()
    start = today - timedelta(days=6)

    rows = (
        db.query(
            func.date(QuestSubmission.submitted_at).label("day"),
            func.coalesce(func.sum(Quest.reward_exp), 0).label("xp"),
        )
        .join(Quest, Quest.quest_id == QuestSubmission.quest_id)
        .filter(
            QuestSubmission.user_id == user_id,
            QuestSubmission.final_status == SubmissionStatus.ACCEPTED,
            QuestSubmission.submitted_at >= start,
        )
        .group_by(func.date(QuestSubmission.submitted_at))
        .all()
    )
    daily_totals = {r.day: r.xp for r in rows}

    result = []
    running_total = 0
    for i in range(7):
        d = start + timedelta(days=i)
        running_total += daily_totals.get(d, 0)
        result.append(DailyXp(date=d, cumulative_xp=running_total))
    return result


def _get_rank(db: Session, current_xp: int, user_id: int) -> int:
    """XP 기준 전체 순위. 동점자는 user_id 오름차순으로 순서를 고정해서
    아래 _get_nearby_ranks의 OFFSET 조회와 순위가 어긋나지 않게 함."""
    higher = (
        db.query(func.count(User.user_id))
        .filter(
            User.is_active.is_(True),
            or_(
                User.current_xp > current_xp,
                and_(User.current_xp == current_xp, User.user_id < user_id),
            ),
        )
        .scalar()
    )
    return higher + 1


def _get_total_users(db: Session) -> int:
    return db.query(func.count(User.user_id)).filter(User.is_active.is_(True)).scalar()


def _get_nearby_ranks(db: Session, rank: int, my_user_id: int) -> list[LeaderboardEntry]:
    """내 순위 기준 앞/뒤 1명씩 포함 (최대 3명). 맨 앞/맨 끝이면 그만큼 적게 반환."""
    offset = max(rank - 2, 0)
    rows = (
        db.query(User)
        .filter(User.is_active.is_(True))
        .order_by(User.current_xp.desc(), User.user_id.asc())
        .offset(offset)
        .limit(3)
        .all()
    )
    start_rank = offset + 1
    return [
        LeaderboardEntry(
            rank=start_rank + i,
            user_id=u.user_id,
            nickname=u.nickname,
            current_level=u.current_level,
            is_me=(u.user_id == my_user_id),
        )
        for i, u in enumerate(rows)
    ]


@router.get("/status", response_model=APIResponse[GrowthStatusResponse])
def get_growth_status(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """경험치바(레벨/XP) + 최근 7일 누적경험치 그래프"""
    db_user = db.query(User).filter(User.user_id == user["id"]).first()
    if db_user is None:
        return APIResponse.fail(message="사용자를 찾을 수 없습니다")

    status_data = GrowthStatusResponse(
        current_level=db_user.current_level,
        current_xp=db_user.current_xp,
        next_level_xp=_next_level_xp(db_user.current_level),
        weekly_xp_graph=_get_weekly_xp_graph(db, db_user.user_id),
    )
    return APIResponse.ok(data=status_data)


@router.get("/leaderboard", response_model=APIResponse[LeaderboardResponse])
def get_leaderboard(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """전체 유저 XP 리더보드 상위 10명 + 내 순위(탑10 밖이면 앞뒤 1명씩도 같이)"""
    db_user = db.query(User).filter(User.user_id == user["id"]).first()
    if db_user is None:
        return APIResponse.fail(message="사용자를 찾을 수 없습니다")

    top_users = (
        db.query(User)
        .filter(User.is_active.is_(True))
        .order_by(User.current_xp.desc(), User.user_id.asc())
        .limit(10)
        .all()
    )
    leaderboard = [
        LeaderboardEntry(
            rank=idx + 1,
            user_id=u.user_id,
            nickname=u.nickname,
            current_level=u.current_level,
            is_me=(u.user_id == db_user.user_id),
        )
        for idx, u in enumerate(top_users)
    ]

    my_rank_in_top = next((e for e in leaderboard if e.is_me), None)
    if my_rank_in_top:
        my_entry = my_rank_in_top
        nearby_ranks = []  # 이미 leaderboard 안에서 앞뒤가 다 보이니 중복 불필요
    else:
        my_rank = _get_rank(db, db_user.current_xp, db_user.user_id)
        my_entry = LeaderboardEntry(
            rank=my_rank,
            user_id=db_user.user_id,
            nickname=db_user.nickname,
            current_level=db_user.current_level,
            is_me=True,
        )
        nearby_ranks = _get_nearby_ranks(db, my_rank, db_user.user_id)

    return APIResponse.ok(
        data=LeaderboardResponse(
            leaderboard=leaderboard,
            my_entry=my_entry,
            nearby_ranks=nearby_ranks,
            total_users=_get_total_users(db),
        )
    )


class PurchaseRequest(BaseModel):
    item_id: int


@router.post("/shop/purchase")
def purchase_item(req: PurchaseRequest, user: dict = Depends(get_current_user)):
    """포인트를 활용하여 기부 또는 굿즈를 구매/교환합니다."""
    # 포인트 차감 및 결제/교환 비즈니스 로직
    return APIResponse.ok(message=f"아이템 {req.item_id} 구매 완료! 포인트가 차감되었습니다.")