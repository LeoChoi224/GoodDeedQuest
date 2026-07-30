"""
CompetitionContribution(개인 기여) 데이터만 채우는 백필 스크립트.
seed_ranking_test_users.py로 만든 1000명(rank_test_* 유저)이 이미 있는데
개인 기여 데이터만 비어있을 때 사용 - 유저/CompetitionParticipant는 건드리지 않음.

실행 (프로젝트 루트에서):
    python -m backend.app.map.seed.seed_personal_contributions
"""
import random

import backend.app.models_registry  # noqa: F401
from backend.app.common.database import SessionLocal
from backend.app.auth.models import User
from backend.app.map.models import Competition, CompetitionContribution
from backend.app.map.enums import CompetitionStatus
from backend.app.quest.models import Category, Quest
from backend.app.quest.enums import QuestType, QuestSource
from backend.app.common.enums import Difficulty
from backend.app.quest_verification.models import QuestSubmission
from backend.app.quest_verification.enums import SubmissionStatus

EMAIL_PREFIX = "rank_test"
CONTRIBUTION_RATIO = 0.7


def get_current_competition(db) -> Competition:
    competition = (
        db.query(Competition)
        .filter(Competition.status.in_([CompetitionStatus.IN_PROGRESS, CompetitionStatus.SETTLING]))
        .order_by(Competition.start_at.desc())
        .first()
    )
    if competition is None:
        raise RuntimeError("진행중이거나 정산중인 대회가 없습니다. seed_ranking_test_users.py를 먼저 실행하세요.")
    return competition


def ensure_dummy_quest(db, fallback_creator_id: int) -> Quest:
    category = db.query(Category).first()
    if category is None:
        category = Category(name="테스트", code="test", icon_url="https://example.com/icon.png", is_active=True)
        db.add(category)
        db.commit()
        db.refresh(category)

    quest = db.query(Quest).filter(Quest.quest_title == "[시드] 랭킹 테스트용 더미 퀘스트").first()
    if quest:
        print(f"기존 더미 퀘스트 재사용: quest_id={quest.quest_id}")
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
        competition = get_current_competition(db)
        print(f"사용할 대회: competition_id={competition.competition_id}, status={competition.status}")

        users = db.query(User).filter(User.email.like(f"{EMAIL_PREFIX}_%")).all()
        if not users:
            raise RuntimeError(f"'{EMAIL_PREFIX}_%' 이메일의 유저가 없습니다. seed_ranking_test_users.py를 먼저 실행하세요.")
        print(f"대상 유저 {len(users)}명 조회됨.")

        # 이미 이 대회에 기여 기록이 있는 유저는 건너뛰어서 재실행해도 안전하게
        already = {
            row[0]
            for row in db.query(CompetitionContribution.user_id)
            .filter(CompetitionContribution.competition_id == competition.competition_id)
            .all()
        }
        candidates = [u for u in users if u.user_id not in already]
        print(f"이미 기여 있는 유저 {len(already)}명 제외, 남은 대상 {len(candidates)}명.")

        dummy_quest = ensure_dummy_quest(db, fallback_creator_id=users[0].user_id)

        contributors = [u for u in candidates if random.random() < CONTRIBUTION_RATIO]
        print(f"개인 기여 생성 대상: {len(contributors)}명")

        for idx, user in enumerate(contributors, start=1):
            if user.region_id is None:
                continue  # 팀(지역) 미설정 유저는 기여 지역이 없어 스킵

            submission = QuestSubmission(
                user_id=user.user_id,
                quest_id=dummy_quest.quest_id,
                final_status=SubmissionStatus.ACCEPTED,
            )
            db.add(submission)
            db.flush()

            db.add(CompetitionContribution(
                competition_id=competition.competition_id,
                user_id=user.user_id,
                submission_id=submission.submission_id,
                region_id=user.region_id,
                points=random.randint(10, 500),
            ))

            if idx % 200 == 0:
                db.commit()
                print(f"  {idx}/{len(contributors)} 커밋 완료")

        db.commit()
        print("개인 기여 데이터 생성 완료.")

    finally:
        db.close()


if __name__ == "__main__":
    main()