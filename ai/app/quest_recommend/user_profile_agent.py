from typing import Dict, Any

from ai.app.quest_recommend.state import RecommendState

def analyze_user_profile(state: RecommendState) -> Dict[str, Any]:
    """
    사용자의 기본 입력값과 활동 이력을 읽어와 
    규격화된 프로필 정보(user_profile)로 정제하여 반환하는 프로그래밍 기반의 LangGraph 노드 함수입니다.
    """
    # State로부터 필요한 정보들을 안전하게 꺼내옵니다.
    interests = state.get("interests", [])
    region_id = state.get("region_id")
    latitude = state.get("latitude")
    longitude = state.get("longitude")
    level = state.get("level", 1)
    history_quests = state.get("history_quests", [])
    recent_recommendations = state.get("recent_recommendations", [])
    preferred_difficulty = state.get("preferred_difficulty")

    # 난이도 정보 처리 (비어있거나 빈 문자열인 경우 "ANY"로 Fallback)
    target_difficulty = preferred_difficulty if preferred_difficulty else "ANY"

    # 최근 추천 내역(exclusions)과 기존 완료 이력(completed_history) 분리 정의
    exclusions = recent_recommendations
    completed_history = history_quests

    # LangGraph 규격에 맞춰 user_profile 업데이트 딕셔너리 반환
    return {"user_profile": {
        "interests": interests,
        "region_id": region_id,
        "latitude": latitude,
        "longitude": longitude,
        "level": level,
        "target_difficulty": target_difficulty,
        "exclusions": exclusions,
        "completed_history": completed_history
    }}