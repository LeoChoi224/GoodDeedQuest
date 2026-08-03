from dataclasses import dataclass

from backend.app.auth.enums import TransactionType
from backend.app.auth.models import User, PointTransaction
from backend.app.badge.service import check_and_award_badges
from backend.app.growth.service import level_from_xp
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
        return 0, 0
    
    return _grant_reward(repository, user, quest, submission)

def _grant_reward(repository, user: User, quest: Quest, submission) -> tuple[int, int]:
    """통과한 제출에 보상을 지급한다.

    Returns:
        (획득 경험치, 획득 포인트)
    """
    xp_gained = quest.reward_exp or 0
    points_gained = quest.reward_point or 0

    user.current_xp += xp_gained
    # ⭐ 수정: XP가 바뀔 때마다 레벨도 같이 재계산해서 저장 - 이전엔 XP만 쌓이고
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

    repository.session.commit()

    try:
        check_and_award_badges(
            db=repository.session,
            user_id=user.user_id,
            category_code=quest.category.code,
        )
    except Exception as error:
        repository.session.rollback()
        print(f"배지 지급 실패(인증은 정상 처리됨): user={user.user_id} "
              f"quest={quest.quest_id} {type(error).__name__}: {error}")

    return xp_gained, points_gained