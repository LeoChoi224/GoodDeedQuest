from typing import TypedDict, List
from langgraph.graph import StateGraph, END

# 에이전트 상태 정의
class RecommendState(TypedDict):
    user_id: int
    interests: List[str]
    location: str
    history_quests: List[str]
    candidate_quests: List[dict]
    recommended_quests: List[dict]

# 1. 후보군 매칭 노드
def retrieve_candidates(state: RecommendState) -> dict:
    """사용자의 관심사와 위치 기반으로 후보 퀘스트들을 Vector DB나 리스트에서 필터링해 가져옵니다."""
    interests = state.get("interests", [])
    location = state.get("location", "")
    
    # 뼈대용 가상 후보 리스트
    all_candidates = [
        {"id": 201, "title": "마포 한강공원 환경정화", "category": "환경", "location": "서울시 마포구"},
        {"id": 202, "title": "사랑의 반찬 배달 봉사", "category": "봉사", "location": "서울시 마포구"},
        {"id": 203, "title": "도서관 도서 정리 정돈", "category": "교육", "location": "서울시 마포구"},
        {"id": 204, "title": "일회용 플라스틱 없는 하루", "category": "환경", "location": "전국"}
    ]
    
    # 관심사 혹은 위치와 일부 매칭되는 후보 필터링
    filtered = [
        c for c in all_candidates
        if c["category"] in interests or location in c["location"] or c["location"] == "전국"
    ]
    
    return {"candidate_quests": filtered}

# 2. LLM 개인화 랭킹 노드
def rank_and_personalize(state: RecommendState) -> dict:
    """LLM을 사용하여 후보 퀘스트들을 사용자의 성향과 매칭률에 따라 랭킹을 매기고 추천 사유를 작성합니다."""
    candidates = state.get("candidate_quests", [])
    interests = state.get("interests", [])
    
    recommendations = []
    # Mock LLM 랭킹 처리 로직
    for idx, c in enumerate(candidates):
        reason = f"사용자님이 '{c['category']}' 영역에 관심이 많으시며, 활동 지역({state['location']})에 적합하여 추천합니다."
        recommendations.append({
            "id": c["id"],
            "title": c["title"],
            "description": f"{c['title']} 활동을 통해 이웃에게 작은 따뜻함을 나누어 주세요.",
            "reason": reason
        })
        
    return {"recommended_quests": recommendations[:2]} # Top 2 추천

# LangGraph 그래프 구성
workflow = StateGraph(RecommendState)

# 노드 등록
workflow.add_node("retrieve_candidates", retrieve_candidates)
workflow.add_node("rank_and_personalize", rank_and_personalize)

# 진입점 설정
workflow.set_entry_point("retrieve_candidates")

# 엣지 연결
workflow.add_edge("retrieve_candidates", "rank_and_personalize")
workflow.add_edge("rank_and_personalize", END)

# 컴파일
recommend_agent = workflow.compile()

async def run_recommendation_flow(user_id: int, interests: List[str], location: str) -> List[dict]:
    """외부에서 추천 에이전트를 호출하기 위한 인터페이스입니다."""
    initial_state = {
        "user_id": user_id,
        "interests": interests,
        "location": location,
        "history_quests": [],
        "candidate_quests": [],
        "recommended_quests": []
    }
    
    # 동기식 혹은 비동기 그래프 실행
    result = await recommend_agent.ainvoke(initial_state)
    return result.get("recommended_quests", [])
