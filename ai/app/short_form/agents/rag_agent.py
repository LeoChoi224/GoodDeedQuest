"""
RAG Agent (BGM 매칭)

입력: state["vision_results"] (씬 분위기/태그)
출력: state["bgm_match"] (매칭된 bgm_id)

mood_tags는 고정 vocab 12개 안에서만 나오므로, pgvector 유사도 검색 대신
BackgroundMusic.mood_tag에 대한 exact match(WHERE mood_tag IN (...))로 매칭한다.
ShortForm.bgm_id는 NOT NULL 이므로 이 단계에서 반드시 값이 채워져야 함.

이번 이슈(#87) 스코프: mood_tag IN (...) 쿼리 작성/실행 + raw 결과 로그 확인까지만.
결과 파싱, 우선순위/fallback 전략, 예외 상황별 세부 처리는 후속 이슈(#88)에서 작업.
"""
import logging

from sqlalchemy import select

from ..models import BackgroundMusic
from ...common.database import SessionLocal
from ..state import ShortFormState, BgmMatchResult

logger = logging.getLogger(__name__)


def rag_agent(state: ShortFormState) -> ShortFormState:
    mood_tags = [tag for r in state["vision_results"] for tag in r["mood_tags"]]
    logger.info(f"[RagAgent] mood_tags={mood_tags}")

    try:
        with SessionLocal() as session:
            candidates = session.scalars(
                select(BackgroundMusic).where(BackgroundMusic.mood_tag.in_(mood_tags))
            ).all()
            print(f"[RagAgent] raw candidates={candidates}")
    except Exception:
        # TODO(#88): DB 쿼리 실패 시 구체적인 처리 전략(재시도/fallback 등) 정의
        logger.exception("[RagAgent] BackgroundMusic 쿼리 실패")

    # TODO(#88): BgmMatchResult 파싱 및 fallback 전략은 후속 이슈에서 처리
    # (매칭 0개일 때 랜덤 fallback, 테이블이 비어있을 때의 RuntimeError 처리 등 포함)
    dummy_match: BgmMatchResult = {
        "bgm_id": 1,
        "bgm_title": "더미 BGM",
        "match_score": 0.0,
        "match_reason": "더미 매칭 결과 (RAG 파싱 미구현, #88에서 작업)",
    }

    state["bgm_match"] = dummy_match
    return state
