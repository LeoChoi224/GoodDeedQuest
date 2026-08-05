"""
전국 지역랭킹 / 개인기여도 / 커뮤니티 피드용 배경 더미 데이터.

배경:
    발표용 로그인 계정(어느 지역에 만들어질지 아직 정해지지 않음, DB에 직접 생성 예정)이
    어느 지역에서 로그인하든 지역 랭킹·개인 기여도(Competition/CompetitionParticipant/
    CompetitionContribution)와 커뮤니티 피드가 비어있지 않도록, 전국 모든 지역에
    배경용 더미 유저를 채워둔다. 특정 지역에 종속되지 않으므로 로그인 데모 계정을
    나중에 어느 지역으로 만들든 상관없다.

    포인트/배지/상점 구매 내역은 넣지 않는다 - 데모 로그인 계정에 직접 포인트를 넣어두고
    뱃지 획득·아이템 구매는 발표 중 라이브로 시연하는 용도이기 때문.

    커뮤니티 캡션/댓글은 화면에 그대로 노출되는 텍스트라 "[SEED]" 같은 표식을 넣지 않는다
    (다른 랭킹 테스트 스크립트와 달리 이건 발표용 데모라 티가 나면 안 됨).

만드는 데이터:
    - User: seed_city_region.py로 이미 채워진 전국 모든 Region에 배경 유저 배정.
      서울/경기 지역은 지역당 20~30명, 그 외 지역은 지역당 8~12명(총 수천 명대).
      로그인 데모용이 아니라 랭킹/피드를 채우기 위한 배경 유저라 비밀번호는 공유값.
    - 레벨 1~100 사이 다양하게 분포(growth 공식에 맞는 XP 부여).
    - Competition 1개(진행중/정산중인 게 있으면 재사용) + 전국 모든 Region의
      CompetitionParticipant(지역 점수, 서울/경기는 높은 점수대) - 전국/시도 랭킹 화면용.
    - 유저의 70%에게 더미 QuestSubmission(ACCEPTED) + CompetitionContribution -
      지역 상세 개인 랭킹 화면용.
    - 그중 30%에게만 커뮤니티 피드 게시글 1~2개 - 전부 다 올리면 부자연스러워서 일부만.
    - 게시글마다 배경 유저 중 일부가 좋아요(0~10개)와 댓글(0~3개)을 남김 - 피드가
      빈 반응 없이 그럴듯하게 보이도록.

전제조건:
    seed_city_region.py로 City/Region이 먼저 채워져 있어야 한다(전국 259개 지역).

재실행 주의:
    User는 매번 새로 추가된다(이메일에 순번만 붙어서 재실행하면 유니크 제약에
    걸릴 수 있음). 다시 만들려면 EMAIL_PREFIX를 바꾸거나, 먼저
    email LIKE 'demo_region_%' 인 유저를 정리하세요.

실행 (프로젝트 루트에서):
    python -m backend.app.map.seed.dummy_demo_region_ranking
"""
import random
from datetime import date, datetime, timedelta, timezone

import backend.app.models_registry  # noqa: F401  (User 등 relationship 문자열 참조 등록용)
from backend.app.common.auth import get_password_hash
from backend.app.common.database import SessionLocal
from backend.app.common.enums import Difficulty
from backend.app.auth.models import User
from backend.app.community.models import Comment, CommunityPost, PostLike
from backend.app.map.enums import CompetitionStatus
from backend.app.map.models import City, Competition, CompetitionContribution, CompetitionParticipant, Region
from backend.app.quest.enums import QuestSource, QuestType
from backend.app.quest.models import Category, Quest
from backend.app.quest_verification.enums import SubmissionStatus
from backend.app.quest_verification.models import QuestSubmission

BOOST_CITY_NAMES = ["서울특별시", "경기도"]  # 이 시/도에 속한 지역은 인원/점수를 더 크게
BOOST_USERS_PER_REGION_RANGE = (20, 30)
OTHER_USERS_PER_REGION_RANGE = (8, 12)

EMAIL_PREFIX = "demo_region"  # 재실행 시 겹치면 이 값을 바꾸세요 (예: demo_region2)
SHARED_PASSWORD = "test1234!"

CONTRIBUTION_RATIO = 0.7  # 개인 기여(CompetitionContribution)를 만들 유저 비중
POST_RATIO_AMONG_CONTRIBUTORS = 0.3  # 기여 유저 중 피드 게시글까지 올릴 비중
POST_COUNT_RANGE = (1, 2)
LIKE_COUNT_RANGE = (0, 10)  # 게시글 하나당 좋아요 수
COMMENT_COUNT_RANGE = (0, 3)  # 게시글 하나당 댓글 수

DUMMY_QUEST_TITLE = "[시드] 랭킹 테스트용 더미 퀘스트"  # 다른 랭킹 시드 스크립트와 동일 타이틀 재사용
COMMIT_BATCH_SIZE = 200

SURNAMES = ["김", "이", "박", "최", "정", "강", "조", "윤", "장", "임"]
GIVEN = [
    "민준", "서연", "도윤", "하은", "지호", "지우", "예준", "수아", "시우", "다은",
    "주원", "은우", "예은", "윤서", "현우", "채원", "우진", "소율", "지안", "서준",
]

POST_IMAGE_URLS = [
    "https://images.unsplash.com/photo-1532996122724-e3c354a0b15b?w=1200",
    "https://images.unsplash.com/photo-1542601906990-b4d3fb778b09?w=1200",
    "https://images.unsplash.com/photo-1559027615-cd4628902d4a?w=1200",
    "https://images.unsplash.com/photo-1593113598332-cd288d649433?w=1200",
    "https://images.unsplash.com/photo-1542810634-71277d95dcbb?w=1200",
    "https://images.unsplash.com/photo-1618477461853-cf6ed80faba5?w=1200",
]

POST_CAPTIONS = [
    "오늘도 동네 한 바퀴 돌면서 쓰레기 주웠어요.",
    "처음으로 봉사활동 나갔는데 생각보다 뿌듯하네요.",
    "주말엔 역시 선행 퀘스트가 최고!",
    "텀블러 챙겨서 일회용품 줄이기 성공.",
    "동네 이웃분들이랑 같이해서 더 즐거웠어요.",
    "오늘 목표 달성! 다음 퀘스트도 도전해야지.",
    "작은 실천이지만 꾸준히 하니 뿌듯합니다.",
    "날씨 좋아서 야외 봉사하기 딱 좋았어요.",
]

COMMENT_TEXTS = [
    "멋져요! 저도 이번 주에 도전해볼게요.",
    "우와 대단하시네요 ㅎㅎ",
    "저도 오늘 비슷한 거 했는데 반가워요!",
    "화이팅입니다, 응원할게요!",
    "사진 보니까 저도 나가고 싶어지네요.",
    "꾸준히 하시는 모습 멋있어요.",
    "좋은 정보 감사해요!",
    "저희 동네도 같이 해요 ㅎㅎ",
    "진짜 부지런하시다...",
    "저도 다음 퀘스트로 정했어요!",
]


def random_nickname(i: int) -> str:
    return f"{random.choice(SURNAMES)}{random.choice(GIVEN)}Q{i:04d}"


def random_birthday() -> date:
    start = date(1985, 1, 1)
    end = date(2008, 12, 31)
    delta_days = (end - start).days
    return start + timedelta(days=random.randint(0, delta_days))


def random_xp_level() -> tuple[int, int]:
    """레벨 1~100 랜덤 배정, growth 도메인 next_level_xp 공식(1000 + 100*n*n)에 맞춰
    그 레벨 구간 안에 들어가는 XP 값을 부여."""
    level = random.randint(1, 100)
    floor_xp = 0 if level <= 1 else 1000 + (100 * (level - 1)) * (level - 1)
    ceil_xp = 1000 if level <= 1 else 1000 + (100 * level) * level
    xp = random.randint(floor_xp, max(floor_xp, ceil_xp - 1))
    return xp, level


def ensure_competition(db) -> Competition:
    competition = (
        db.query(Competition)
        .filter(Competition.status.in_([CompetitionStatus.IN_PROGRESS, CompetitionStatus.SETTLING]))
        .order_by(Competition.start_at.desc())
        .first()
    )
    if competition:
        print(f"기존 진행중/정산중 대회 재사용: competition_id={competition.competition_id}")
        return competition

    now = datetime.now(timezone.utc)
    competition = Competition(
        title="지역랭킹 데모용 대항전",
        description="발표 데모용 지역랭킹/개인기여도 화면을 채우기 위한 더미 대항전",
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
    category = db.query(Category).first()
    if category is None:
        category = Category(name="테스트", code="test", icon_url="https://example.com/icon.png", is_active=True)
        db.add(category)
        db.commit()
        db.refresh(category)

    quest = db.query(Quest).filter(Quest.quest_title == DUMMY_QUEST_TITLE).first()
    if quest:
        return quest

    quest = Quest(
        category_id=category.category_id,
        creator_id=fallback_creator_id,
        quest_title=DUMMY_QUEST_TITLE,
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
        shared_password_hash = get_password_hash(SHARED_PASSWORD)

        # 전국 Region + 소속 City명 조회 (seed_city_region.py가 이미 채워놨다고 가정)
        region_rows = (
            db.query(Region.region_id, Region.region_name, City.city_name)
            .join(City, City.city_id == Region.city_id)
            .all()
        )
        if not region_rows:
            raise RuntimeError(
                "Region 데이터가 없습니다. backend.app.map.seed.seed_city_region 을 먼저 실행하세요."
            )

        boost_region_ids = {r.region_id for r in region_rows if r.city_name in BOOST_CITY_NAMES}
        all_region_ids = [r.region_id for r in region_rows]
        print(
            f"전국 지역 {len(all_region_ids)}개 로드 완료 "
            f"(서울/경기 {len(boost_region_ids)}개, 그 외 {len(all_region_ids) - len(boost_region_ids)}개)"
        )

        # 1. 지역별 배경 유저 생성 (서울/경기 20~30명, 그 외 8~12명, 레벨 1~100 다양하게)
        print("배경 유저 생성 시작...")
        created_users: list[User] = []
        seq = 1
        pending = 0
        for region in region_rows:
            is_boost = region.region_id in boost_region_ids
            user_count = random.randint(*BOOST_USERS_PER_REGION_RANGE) if is_boost else random.randint(*OTHER_USERS_PER_REGION_RANGE)

            for _ in range(user_count):
                xp, level = random_xp_level()
                user = User(
                    region_id=region.region_id,
                    email=f"{EMAIL_PREFIX}_{seq:05d}@gdq.test",
                    password_hash=shared_password_hash,
                    nickname=random_nickname(seq),
                    birthday=random_birthday(),
                    current_xp=xp,
                    current_level=level,
                    daily_streak=random.randint(0, 30),
                    is_active=True,
                )
                db.add(user)
                created_users.append(user)
                seq += 1
                pending += 1

            if pending >= COMMIT_BATCH_SIZE:
                db.commit()
                pending = 0
                print(f"  {seq - 1}명 커밋 완료...")

        db.commit()
        for u in created_users:
            db.refresh(u)
        print(f"배경 유저 {len(created_users)}명 생성 완료.")

        # 2. CompetitionParticipant (지역 점수) - 전국 모든 지역
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
            is_boost = region_id in boost_region_ids
            score = random.randint(800, 5000) if is_boost else random.randint(0, 600)
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

        # 3. 개인 기여(CompetitionContribution) - 유저의 70%
        print("개인 기여(CompetitionContribution) 더미 생성 중...")
        dummy_quest = ensure_dummy_quest(db, fallback_creator_id=created_users[0].user_id)

        contributors = [u for u in created_users if random.random() < CONTRIBUTION_RATIO]
        contributor_submissions: dict[int, int] = {}  # user_id -> submission_id (피드용으로 재사용)
        for idx, user in enumerate(contributors, start=1):
            submission = QuestSubmission(
                user_id=user.user_id,
                quest_id=dummy_quest.quest_id,
                final_status=SubmissionStatus.ACCEPTED,
            )
            db.add(submission)
            db.flush()
            contributor_submissions[user.user_id] = submission.submission_id

            db.add(CompetitionContribution(
                competition_id=competition.competition_id,
                user_id=user.user_id,
                submission_id=submission.submission_id,
                region_id=user.region_id,
                points=random.randint(10, 500),
            ))

            if idx % COMMIT_BATCH_SIZE == 0:
                db.commit()
                print(f"  {idx}/{len(contributors)} 기여 커밋 완료")

        db.commit()
        print(f"개인 기여 {len(contributors)}건 생성 완료.")

        # 4. 커뮤니티 피드 - 기여 유저 중 30%만, 1~2개씩
        print("커뮤니티 피드 게시글 더미 생성 중...")
        post_authors = [u for u in contributors if random.random() < POST_RATIO_AMONG_CONTRIBUTORS]
        now = datetime.now(timezone.utc)
        created_posts: list[tuple[CommunityPost, int]] = []  # (post, author_user_id)
        pending = 0
        for author in post_authors:
            num_posts = random.randint(*POST_COUNT_RANGE)
            for i in range(num_posts):
                created_at = now - timedelta(days=random.randint(0, 20), hours=random.randint(0, 23))
                post = CommunityPost(
                    user_id=author.user_id,
                    submission_id=contributor_submissions.get(author.user_id) if i == 0 else None,
                    media_url=random.choice(POST_IMAGE_URLS),
                    caption=random.choice(POST_CAPTIONS),
                    is_active=True,
                    created_at=created_at,
                    updated_at=created_at,
                )
                db.add(post)
                created_posts.append((post, author.user_id))
                pending += 1

            if pending >= COMMIT_BATCH_SIZE:
                db.commit()
                pending = 0
        db.commit()
        for post, _author_id in created_posts:
            db.refresh(post)
        print(f"커뮤니티 피드 게시글 {len(created_posts)}건 생성 완료 (작성자 {len(post_authors)}명).")

        # 5. 게시글별 좋아요/댓글 - 배경 유저 중 일부가 반응 남김
        print("좋아요/댓글 더미 생성 중...")
        like_count_total = 0
        comment_count_total = 0
        pending = 0
        for post, author_user_id in created_posts:
            like_pool = [u for u in created_users if u.user_id != author_user_id]

            like_n = random.randint(*LIKE_COUNT_RANGE)
            likers = random.sample(like_pool, k=min(like_n, len(like_pool)))
            for liker in likers:
                db.add(PostLike(
                    post_id=post.post_id,
                    user_id=liker.user_id,
                    created_at=post.created_at + timedelta(hours=random.randint(0, 48)),
                ))
                like_count_total += 1
                pending += 1

            comment_n = random.randint(*COMMENT_COUNT_RANGE)
            commenters = random.sample(like_pool, k=min(comment_n, len(like_pool)))
            for commenter in commenters:
                comment_at = post.created_at + timedelta(hours=random.randint(0, 48))
                db.add(Comment(
                    post_id=post.post_id,
                    user_id=commenter.user_id,
                    content=random.choice(COMMENT_TEXTS),
                    created_at=comment_at,
                    updated_at=comment_at,
                ))
                comment_count_total += 1
                pending += 1

            if pending >= COMMIT_BATCH_SIZE:
                db.commit()
                pending = 0

        db.commit()
        print(f"좋아요 {like_count_total}건, 댓글 {comment_count_total}건 생성 완료.")

        print(
            "전부 완료! 전국 어느 지역에 데모 로그인 계정을 만들든 지역 랭킹, 지역 상세 "
            "개인 랭킹, growth 리더보드, 커뮤니티 피드(좋아요/댓글 포함)가 비어있지 않습니다."
        )

    finally:
        db.close()


if __name__ == "__main__":
    main()