import logging
from typing import Dict, Any

from langgraph.graph import StateGraph, END
from ai.app.quest_recommend.state import RecommendState

# 8개 노드 및 각 모듈별 응집된 라우터 함수 임포트
from ai.app.quest_recommend.nodes.user_profile_agent import analyze_user_profile
from ai.app.quest_recommend.nodes.situation_agent import analyze_situation
from ai.app.quest_recommend.nodes.request_agent import analyze_request
from ai.app.quest_recommend.nodes.planner_agent import analyze_strategy
from ai.app.quest_recommend.nodes.retrieval_tool import retrieve_volunteers
from ai.app.quest_recommend.nodes.good_deed_agent import create_good_deeds
from ai.app.quest_recommend.nodes.validation_agent import validate_candidates, route_validation
from ai.app.quest_recommend.nodes.response_agent import format_response

logger = logging.getLogger(__name__)

def create_recommendation_graph():
    """
    맞춤형 퀘스트 추천 랭그래프(StateGraph) 워크플로우를 조립하고 컴파일하는 함수입니다.
    """
    workflow = StateGraph(RecommendState)

    # 1. 8개 에이전트 노드 등록
    workflow.add_node("user_profile", analyze_user_profile)
    workflow.add_node("situation", analyze_situation)
    workflow.add_node("request", analyze_request)
    workflow.add_node("planner", analyze_strategy)
    workflow.add_node("retrieval", retrieve_volunteers)
    workflow.add_node("recommendation", create_good_deeds)
    workflow.add_node("validation", validate_candidates)
    workflow.add_node("response", format_response)

    # 2. 그래프 진입점(Entry Point) 설정
    workflow.set_entry_point("user_profile")

    # 3. 순차 에지(Sequential Edges) 연결
    workflow.add_edge("user_profile", "situation")
    workflow.add_edge("situation", "request")
    workflow.add_edge("request", "planner")
    workflow.add_edge("planner", "retrieval")
    workflow.add_edge("retrieval", "recommendation")
    workflow.add_edge("recommendation", "validation")
    workflow.add_edge("response", END)  # 최종 응답 후종착점(END) 연결
    
    # 4. 검증 에이전트: 조건부 분기 (추천 품질 낮음: planner / 검색 결과 부족 : retrieval / 통과, 재시도 횟수 초과: response)
    workflow.add_conditional_edges(
        "validation",
        route_validation,
        {
            "planner": "planner",
            "retrieval": "retrieval",
            "response": "response"
        }
    )

    # 5. 워크플로우 컴파일
    return workflow.compile()

# 글로벌 컴파일 객체 생성 (싱글톤 활용)
recommend_graph = create_recommendation_graph()

def run_recommendation_flow(initial_state: RecommendState) -> Dict[str, Any]:
    """
    외부 API 라우터나 백엔드 컨트롤러에서 단 한 번의 호출로 
    전체 퀘스트 추천 워크플로우를 실행하는 최상위 엔트리포인트 함수입니다.
    """
    logger.info(f"퀘스트 추천 랭그래프 워크플로우 가동 시작. User ID: {initial_state.get('user_id')}")
    
    final_state = recommend_graph.invoke(initial_state)
    
    logger.info(f"퀘스트 추천 랭그래프 워크플로우 완료. 최종 퀘스트 {len(final_state.get('recommended_quests', []))}개 배출.")
    
    return final_state