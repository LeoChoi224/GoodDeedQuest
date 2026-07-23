from typing import Dict, Any
import logging

from ai.app.quest_recommend.state import RecommendState

logger = logging.getLogger(__name__)

def format_response(state: RecommendState) -> Dict[str, Any]:
    """
    최종 검증을 마친 후보군(candidate_quests)을 추천도 점수(priority_score) 순으로
    정렬하고, 상위 최대 5개만을 슬라이싱하여 최종 응답 형태로 반환하는 프로그래밍 기반 노드 함수입니다.
    """
    candidate_quests = state.get("candidate_quests", [])
    accumulated_candidates = state.get("accumulated_candidates", [])

    target_pool = accumulated_candidates or candidate_quests

    logger.info(f"최종 응답 포맷팅 시작: 당회 합격 {len(candidate_quests)}개 + 누적 AI 합격 {len(accumulated_candidates)}개 검토 중.")

    # 1. 추천 점수(priority_score)가 높은 퀘스트 순으로 내림차순 정렬 (기본값 0)
    sorted_quests = sorted(
        target_pool,
        key=lambda x: x.get("priority_score", 0),
        reverse=True
    )
    
    # 2. 정량 조건 충족을 위해 상위 최대 5개 추출
    final_recommended = sorted_quests[:5]
    
    logger.info(f"최종 응답 포맷팅 완료: 최적의 추천 퀘스트 {len(final_recommended)}개 선별 완료.")
    
    return {"recommended_quests": final_recommended}