"""
랭킹 화면(MainMap/SiDoMap 전국·시군구 랭킹, RegionDetails 개인 랭킹, growth 리더보드)
테스트용 더미 데이터 시드 스크립트.

- User 1000명 생성. region_id는 80%가 서울/경기, 20%는 전국 랜덤 배정.
- current_xp/current_level도 다양하게 부여 (growth 리더보드 테스트 겸용).
- IN_PROGRESS 대회가 없으면 새로 하나 만듦.
- 전국 모든 Region에 CompetitionParticipant를 등록/갱신 - 서울/경기는 높은 점수대,
  그 외 지역은 낮은 점수대로 넣어서 national-ranking/city-ranking이 그럴듯하게 나오게 함.
- (추가) RegionDetails 상세페이지 "개인 랭킹" 테스트용으로, 더미 Quest 1개 + 유저별
  QuestSubmission(ACCEPTED 처리) + CompetitionContribution(랜덤 포인트)까지 생성.
  실제 인증 플로우를 거치지 않고 결과 상태만 흉내낸 것이므로 진짜 검증 로직 테스트는 아님.

재실행해도 안전: 유저는 매번 새로 추가되지만(이메일에 랜덤 접미사 없음, 재실행 시 유니크 제약
걸릴 수 있음 - 재실행하려면 아래 EMAIL_PREFIX를 바꾸거나 기존 테스트 유저를 먼저 지우세요),
CompetitionParticipant는 있으면 점수만 갱신하고 없으면 새로 만듭니다.

실행 (프로젝트 루트에서):
    python -m backend.app.map.seed.seed_ranking_test_users
"""
import random
from datetime import datetime, timedelta, timezone, date

import backend.app.models_registry  # noqa: F401 (User relationship 문자열 참조 등록용)
from backend.app.common.database import SessionLocal
from backend.app.common.auth import get_password_hash
from backend.app.auth.models import User
from backend.app.map.models import Region, City, Competition, CompetitionParticipant, CompetitionContribution
from backend.app.map.enums import CompetitionStatus
from backend.app.quest.models import Category, Quest
from backend.app.quest.enums import QuestType, QuestSource
from backend.app.common.enums import Difficulty
from backend.app.quest_verification.models import QuestSubmission
from backend.app.quest_verification.enums import SubmissionStatus

TOTAL_USERS = 1000
SEOUL_GYEONGGI_RATIO = 0.8  # 유저 중 서울/경기 비중
SEOUL_GYEONGGI_CITY_NAMES = ["서울특별시", "경기도"]
EMAIL_PREFIX = "rank_test"  # 재실행 시 겹치면 이 값을 바꾸세요 (예: rank_test2)
CONTRIBUTION_RATIO = 0.7  # 개인 랭킹용 더미 기여를 만들 유저 비중 (전부 다 할 필요는 없어서)

SURNAMES = ["김", "이", "박", "최", "정", "강", "조", "윤", "장", "임"]
GIVEN = [
    "민준", "서연", "도윤", "하은", "지호", "지우", "예준", "수아", "시우", "다은",
    "주원", "은우", "예은", "윤서", "현우", "채원", "우진", "소율", "지안", "서준",
]


def random_nickname(i: int) -> str:
    return f"{random.choice(SURNAMES)}{random.choice(GIVEN)}{i:04d}"


def random_birthday() -> date:
    start = date(1985, 1, 1)
    end = date(2008, 12, 31)
    delta_days = (end - start).days
    return start + timedelta(days=random.randint(0, delta_days))


def random_xp_level() -> tuple[int, int]:
    """레벨 1~30 랜덤 배정, growth 도메인 _next_level_xp 공식(1000 + 100*n*n)에 맞춰
    그 레벨 구간 안에 들어가는 XP 값을 부여."""
    level = random.randint(1, 30)
    floor_xp = 0 if level <= 1 else 1000 + (100 * (level - 1)) * (level - 1)
    ceil_xp = 1000 if level <= 1 else 1000 + (100 * level) * level
    xp = random.randint(floor_xp, max(floor_xp, ceil_xp - 1))
    return xp, level


def ensure_competition(db) -> Competition:
    competition = (
        db.query(Competition)
        .filter(Competition.status == CompetitionStatus.IN_PROGRESS)
        .order_by(Competition.start_at.desc())
        .first()
    )
    if competition:
        print(f"기존 진행중 대회 사용: competition_id={competition.competition_id}")
        return competition

    now = datetime.now(timezone.utc)
    competition = Competition(
        title="랭킹 테스트용 대항전",
        description="시드 스크립트로 생성된 테스트용 대항전 (월~토 진행 가정)",
        status=CompetitionStatus.IN_PROGRESS,
        start_at=now,
        end_at=now + timedelta(days=6),
    )
    db.add(competition)
    db.commit()
    db.refresh(competition)
    print(f"새 대회 생성: competition_id={competition.competition_id}")
    return competition


def ensure_dummy_quest(db, fallback_creator_id: int) -> Quest:
    """개인 기여 더미용 Quest 1개. 있는 카테고리를 재사용하고, 없으면 하나 만듦."""
    category = db.query(Category).first()
    if category is None:
        category = Category(name="테스트", code="test", icon_url="https://example.com/icon.png", is_active=True)
        db.add(category)
        db.commit()
        db.refresh(category)

    quest = db.query(Quest).filter(Quest.quest_title == "[시드] 랭킹 테스트용 더미 퀘스트").first()
    if quest:
        return quest

    quest = Quest(
        category_id=category.category_id,
        creator_id=fallback_creator_id,
        quest_title="[시드] 랭킹 테스트용 더미 퀘스트",
        quest_description="개인 랭킹(CompetitionContribution) 테스트를 위해 시드 스크립트가 생성한 더미 퀘스트입니다.",
        quest_type=QuestType.GOOD_DEED,
        quest_source=QuestSource.ADMIN,
        difficulty=Difficulty.EASY,
    )
    db.add(quest)
    db.commit()
    db.refresh(quest)
    print(f"더미 퀘스트 생성: quest_id={quest.quest_id}")
    return quest


def main():
    db = SessionLocal()
    try:
        competition = ensure_competition(db)

        boost_regions = (
            db.query(Region.region_id)
            .join(City, City.city_id == Region.city_id)
            .filter(City.city_name.in_(SEOUL_GYEONGGI_CITY_NAMES))
            .all()
        )
        boost_region_ids = [r.region_id for r in boost_regions]

        all_region_ids = [r.region_id for r in db.query(Region.region_id).all()]
        other_region_ids = [rid for rid in all_region_ids if rid not in boost_region_ids]

        if not boost_region_ids:
            raise RuntimeError(
                "서울/경기 Region이 하나도 없습니다. seed_city_region.py를 먼저 실행했는지 확인하세요."
            )

        print(f"서울/경기 지역 {len(boost_region_ids)}개, 그 외 지역 {len(other_region_ids)}개")

        shared_password_hash = get_password_hash("test1234!")  # 전부 동일 비번(테스트용), 해싱은 1번만

        created_users = []

        print(f"유저 {TOTAL_USERS}명 생성 시작...")
        for i in range(1, TOTAL_USERS + 1):
            use_boost = random.random() < SEOUL_GYEONGGI_RATIO
            region_id = (
                random.choice(boost_region_ids)
                if (use_boost or not other_region_ids)
                else random.choice(other_region_ids)
            )
            xp, level = random_xp_level()

            user = User(
                region_id=region_id,
                email=f"{EMAIL_PREFIX}_{i:04d}@gdq.test",
                password_hash=shared_password_hash,
                nickname=random_nickname(i),
                birthday=random_birthday(),
                current_xp=xp,
                current_level=level,
                daily_streak=random.randint(0, 30),
                is_active=True,
            )
            db.add(user)
            created_users.append(user)

            if i % 200 == 0:
                db.commit()
                print(f"  {i}/{TOTAL_USERS} 커밋 완료")

        db.commit()
        for u in created_users:
            db.refresh(u)  # user_id 확보
        print("유저 생성 완료.")

        print("CompetitionParticipant 등록/점수 부여 중...")
        for region_id in all_region_ids:
            participant = (
                db.query(CompetitionParticipant)
                .filter(
                    CompetitionParticipant.competition_id == competition.competition_id,
                    CompetitionParticipant.region_id == region_id,
                )
                .first()
            )
            is_boost_region = region_id in boost_region_ids
            score = random.randint(800, 5000) if is_boost_region else random.randint(0, 600)

            if participant:
                participant.score = score
            else:
                db.add(CompetitionParticipant(
                    competition_id=competition.competition_id,
                    region_id=region_id,
                    score=score,
                ))
        db.commit()
        print("CompetitionParticipant 완료.")

        # --- 개인 랭킹(RegionDetails) 테스트용: 더미 QuestSubmission + CompetitionContribution ---
        print("개인 기여(CompetitionContribution) 더미 생성 중...")
        dummy_quest = ensure_dummy_quest(db, fallback_creator_id=created_users[0].user_id)

        contributors = [u for u in created_users if random.random() < CONTRIBUTION_RATIO]
        for idx, user in enumerate(contributors, start=1):
            submission = QuestSubmission(
                user_id=user.user_id,
                quest_id=dummy_quest.quest_id,
                final_status=SubmissionStatus.ACCEPTED,
            )
            db.add(submission)
            db.flush()  # submission_id 확보 (commit 전에)

            db.add(CompetitionContribution(
                competition_id=competition.competition_id,
                user_id=user.user_id,
                submission_id=submission.submission_id,
                region_id=user.region_id,
                points=random.randint(10, 500),
            ))

            if idx % 200 == 0:
                db.commit()
                print(f"  {idx}/{len(contributors)} 기여 커밋 완료")

        db.commit()
        print(f"개인 기여 {len(contributors)}건 생성 완료.")

        print("전부 완료! national-ranking / city-ranking / region-ranking 개인 랭킹 / growth 리더보드 전부 테스트 가능합니다.")

    finally:
        db.close()


if __name__ == "__main__":
    main()