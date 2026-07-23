from typing import TypedDict, List, Dict, Any, Optional

class RecommendState(TypedDict):
    """
    LangGraph 기반 맞춤형 퀘스트 추천 워크플로우에서
    여러 에이전트 노드 간 데이터 공유 및 전달을 담당하는 State 정의 클래스입니다.
    """
    user_id: int
    interests: List[str]
    region_id: Optional[int]
    latitude: Optional[float]
    longitude: Optional[float]
    level: int
    history_quests: List[str]
    recent_recommendations: List[str]
    preferred_difficulty: str
    request_message: Optional[str]

    user_profile: Dict[str, Any]
    situation_context: Dict[str, Any]
    request_context: Dict[str, Any]

    recommendation_strategy: Dict[str, Any]
    retrieved_volunteers: List[Dict[str, Any]]
    candidate_quests: List[Dict[str, Any]]

    retry_count: int
    accumulated_candidates: List[Dict[str, Any]]
    recommended_quests: List[Dict[str, Any]]
