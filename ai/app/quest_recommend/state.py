from typing import TypedDict, List, Dict, Any, Optional

class RecommendState(TypedDict):
    """
    LangGraph 기반 맞춤형 퀘스트 추천 워크플로우에서
    여러 에이전트 노드 간 데이터 공유 및 전달을 담당하는 State 정의 클래스입니다.
    """
    user_id: int
    interests: str
    location: str
    level: int
    history_quests: List[str]
    recent_recommendations: List[str]
    preferred_difficulty: str
    request_message: Optional[str]

    user_profile: Dict[str, Any]
    context: Dict[str, Any]
    request_context: Dict[str, Any]

    recommendation_strategy: Dict[str, Any]
    retrieved_volunteers: List[Dict]
    candidate_quests: List[Dict]

    retry_count: int
    recommended_quests: List[Dict]
