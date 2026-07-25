from typing import Dict, Any, List
import logging

from ai.app.quest_recommend.state import RecommendState

logger = logging.getLogger(__name__)

def select_top_quests_by_type(target_pool: List[Dict[str, Any]], quest_type: str, count: int) -> List[Dict[str, Any]]:
    """
    후보군(target_pool)에서 특정 quest_type만 추출하여 
    priority_score 내림차순 정렬 후 요청된 count 개수만큼 슬라이싱하여 반환하는 헬퍼 함수입니다.
    """
    filtered = [q for q in target_pool if q.get("quest_type") == quest_type]
    sorted_quests = sorted(filtered, key=lambda x: x.get("priority_score", 0), reverse=True)
    return sorted_quests[:count]

def format_response(state: RecommendState) -> Dict[str, Any]:
    """
     최종 검증을 마친 후보군(accumulated_candidates / candidate_quests)을 대상으로
    추천도 점수(priority_score) 순으로 실제 봉사 1~2개 + 일상 선행 3~4개를 조합하여
    최종 5개만을 슬라이싱하여 최종 응답 형태로 반환하는 프로그래밍 기반 노드 함수입니다.
    """
    candidate_quests = state.get("candidate_quests", [])
    accumulated_candidates = state.get("accumulated_candidates", [])

    target_pool = accumulated_candidates or candidate_quests

    logger.info(f"최종 응답 포맷팅 시작: 검토 대상 후보 {len(target_pool)}개")

    # 1. 실제 봉사(VOLUNTEER) 점수 상위 최대 2개 선별
    selected_volunteers = select_top_quests_by_type(target_pool, quest_type="VOLUNTEER", count=2)

    # 2. 모자란 개수(3~4개)만큼 일상 선행(GOOD_DEED) 점수 상위 선별
    needed_good_deeds = 5 - len(selected_volunteers)
    selected_good_deeds = select_top_quests_by_type(target_pool, quest_type="GOOD_DEED", count=needed_good_deeds)

    final_recommended = selected_volunteers + selected_good_deeds

    # 3. 봉사 데이터 부족 등으로 만약 5개가 채워지지 않은 경우 남은 전체 후보군에서 점수 순으로 차출
    if len(final_recommended) < 5:
        remaining = [q for q in target_pool if q not in final_recommended]
        remaining_sorted = sorted(remaining, key=lambda x: x.get("priority_score", 0), reverse=True)
        final_recommended.extend(remaining_sorted[:5 - len(final_recommended)])
        
    logger.info(f"최종 황금비율 추천 퀘스트 {len(final_recommended)}개 선별 완료 (실제 봉사: {len(selected_volunteers)}개, AI 일상 선행: {len(selected_good_deeds)}개)")
    
    return {"recommended_quests": final_recommended}