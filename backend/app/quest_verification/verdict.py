from dataclasses import dataclass

from backend.app.auth.enums import TransactionType
from backend.app.auth.models import User, PointTransaction
from backend.app.badge.service import check_and_award_badges
from backend.app.growth.service import level_from_xp
from backend.app.map.enums import CompetitionStatus
from backend.app.map.models import Competition, CompetitionContribution
from backend.app.map.router import _ensure_participant
from backend.app.quest.models import Quest
from backend.app.quest_verification.challenge import (
    calculate_suspicion, needs_challenge, generate_challenge_code,
)
from backend.app.quest_verification.enums import SubmissionStatus
from backend.app.quest_verification.trust import (
    adjust_trust, TRUST_ON_COMPLETE, TRUST_ON_CHALLENGE, TRUST_ON_REJECT,
)
@dataclass
class Verdict:
    final_status: SubmissionStatus
    challenge_code: str | None
    suspicion: int
    stored_extras: list[str]
    challenge: bool

def decide(result: dict, phash_distance: int | None, extra_keys: list[str]) -> Verdict:
    related = result.get("related", [])
    stored_extras = [key for key, ok in zip(extra_keys, related) if ok]

    suspicion = calculate_suspicion(
        ai_generated=result.get("ai_generated", False),
        capture_time_known=result.get("capture_time_known", False),
        phash_distance=phash_distance,
    )
    # 【판단】 AI 생성·위조로 의심되면 바로 거절한다. 원래는 의심점수에만 더해서
    # 임계값을 넘어야 챌린지로 갔고, 점수가 모자라면 그대로 통과했다. 특히 봉사
    # 확인서는 pHash 검사를 건너뛰어 점수가 덜 쌓이므로 통과할 여지가 컸다.
    # 위조는 "조금 의심스러운 것"이 아니라 그 자체로 실패여야 한다.
    if result.get("ai_generated", False):
        return Verdict(
            final_status=SubmissionStatus.REJECTED,
            challenge_code=None,
            suspicion=suspicion,
            stored_extras=stored_extras,
            challenge=False,
        )

    challenge = bool(result.get("verified")) and needs_challenge(suspicion)

    if challenge:
        status = SubmissionStatus.PENDING
    elif result.get("verified"):
        status = SubmissionStatus.ACCEPTED
    else:
        status = SubmissionStatus.REJECTED

    return Verdict(
        final_status=status,
        challenge_code=generate_challenge_code() if challenge else None,
        suspicion=suspicion,
        stored_extras=stored_extras,
        challenge=challenge,
    )

def settle(repository, user: User, quest: Quest, submission, verdict: Verdict, result: dict) -> tuple:
    submission.final_status = verdict.final_status
    submission.challenge_code = verdict.challenge_code
    submission.extra_media_urls = verdict.stored_extras
    submission.ai_verdict = {**result, "suspicion_score": verdict.suspicion}
    submission.ai_generated_suspicion = result.get("ai_generated", False)

    if verdict.final_status is SubmissionStatus.PENDING:
        adjust_trust(user, TRUST_ON_CHALLENGE)
    elif verdict.final_status is SubmissionStatus.REJECTED:
        adjust_trust(user, TRUST_ON_REJECT)

    if verdict.final_status is not SubmissionStatus.ACCEPTED:
        repository.session.commit()
        return 0, 0, []

    return _grant_reward(repository, user, quest, submission)

def _grant_reward(repository, user: User, quest: Quest, submission) -> tuple[int, int, list[str]]:
    """통과한 제출에 보상을 지급한다.

    Returns:
        (획득 경험치, 획득 포인트, 이번에 새로 해금된 칭호(배지) 이름 목록)
    """
    xp_gained = quest.reward_exp or 0
    points_gained = quest.reward_point or 0

    user.current_xp += xp_gained
    # current_level은 절대 자동으로 안 올라갔음(growth 도메인의 level_from_xp 재사용)
    user.current_level = level_from_xp(user.current_xp)
    user.point_balance += points_gained
    adjust_trust(user, TRUST_ON_COMPLETE)

    if points_gained:
        repository.session.add(PointTransaction(
            user_id=user.user_id,
            submission_id=submission.submission_id,
            amount=points_gained,
            type=TransactionType.EARN,
            balance_after=user.point_balance,
        ))

    # ⭐ 추가: 대항전 기여 기록 - 지역 랭킹(personal_ranking)·시군구 랭킹·전국 랭킹이 전부
    # CompetitionContribution을 합산해서 만들어지는 구조인데, 여태 이 지점에서 만드는 코드가
    # 없어서 실제 퀘스트 완료가 랭킹에 전혀 반영이 안 됐다. 유저가 참여 지역을 정해뒀고
    # 지금 진행 중(IN_PROGRESS)인 대회가 있을 때만 기록한다 - 정산 중(SETTLING)엔 더 이상
    # 점수가 안 늘어나야 하므로 team-select 등 다른 쓰기 작업과 동일하게 IN_PROGRESS만 인정.
    if user.region_id is not None:
        competition = (
            repository.session.query(Competition)
            .filter(Competition.status == CompetitionStatus.IN_PROGRESS)
            .order_by(Competition.start_at.desc())
            .first()
        )
        if competition is not None:
            # 이 유저 지역이 아직 이번 대회 참여자로 등록 안 됐을 수 있으니(예: /map 화면을
            # 이번 주에 한 번도 안 들어옴) 먼저 보장해준다 - map 도메인의 헬퍼 재사용.
            _ensure_participant(repository.session, competition.competition_id, user.region_id)
            repository.session.add(CompetitionContribution(
                competition_id=competition.competition_id,
                user_id=user.user_id,
                submission_id=submission.submission_id,
                region_id=user.region_id,
                points=points_gained,
            ))

    repository.session.commit()

    # ⭐ 추가: 퀘스트 인증완료 화면에서 칭호(배지) 해금 토스트를 띄우기 위해
    # 새로 지급된 배지 이름을 함께 반환한다.
    unlocked_badge_names: list[str] = []
    try:
        unlocked_badges = check_and_award_badges(
            db=repository.session,
            user_id=user.user_id,
            category_code=quest.category.code,
        )
        unlocked_badge_names = [badge.name for badge in unlocked_badges]
    except Exception as error:
        repository.session.rollback()
        print(f"배지 지급 실패(인증은 정상 처리됨): user={user.user_id} "
              f"quest={quest.quest_id} {type(error).__name__}: {error}")

    return xp_gained, points_gained, unlocked_badge_names