from sqlalchemy.orm import Session

from backend.app.quest.models import QuestStart
from backend.app.quest_verification.models import QuestSubmission
from backend.app.quest_verification.enums import SubmissionStatus


def completed_quest_ids(db: Session, user_id: int) -> set[int]:
    """인증이 통과(ACCEPTED)된 퀘스트 집합. 목록에서 감추고 완료로 표시하는 기준이다."""
    rows = (
        db.query(QuestSubmission.quest_id)
        .filter(
            QuestSubmission.user_id == user_id,
            QuestSubmission.final_status == SubmissionStatus.ACCEPTED,
        )
        .all()
    )
    return {row[0] for row in rows}


def started_quest_ids(db: Session, user_id: int) -> set[int]:
    """내가 손을 댄 퀘스트 집합. 인증을 냈거나 시작 버튼을 누른 것을 합친다.

    인증은 상태를 가리지 않는다. 거절·보류도 "손을 댄" 것이므로 진행중으로 본다.
    통과한 것은 호출부에서 done_ids 로 이미 목록에서 빠진다.
    """
    submitted = (
        db.query(QuestSubmission.quest_id)
        .filter(QuestSubmission.user_id == user_id)
        .all()
    )
    started = (
        db.query(QuestStart.quest_id)
        .filter(QuestStart.user_id == user_id)
        .all()
    )
    return {row[0] for row in submitted} | {row[0] for row in started}


