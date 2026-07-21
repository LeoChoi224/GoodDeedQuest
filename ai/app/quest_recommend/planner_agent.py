from pydantic import BaseModel, Field
import logging
from typing import Dict, Any, List

from ai.app.quest_recommend.state import RecommendState
from ai.app.common.llm import get_openai_model

logger = logging.getLogger(__name__)

class PlannerOutput(BaseModel):
    strategy: str = Field(
        ...,
        # "추천 방향을 설명하는 간략한 전략 요약 (예: '비 오는 평일이므로 실내 환경 관련 활동을 강조')."
        description="A brief strategy summary explaining the recommendation direction (e.g. 'Emphasize indoor environmental tasks on rainy weekdays')."
    )
    search_query: str = Field(
        ...,
        # "벡터 데이터베이스에서 관련 봉사 활동을 찾기 위해 최적화된 검색 쿼리 키워드 (예: '실내 환경 교육')."
        description="An optimized search query keyword to find relevant volunteer tasks from the vector database (e.g., 'indoor environmental education')."
    )
    llm_constraints: List[str] = Field(
        ...,
        # "최종 퀘스트 추천 에이전트가 준수해야 할 2~4개의 엄격한 규칙/제약조건 리스트 (예: '반드시 실내여야 함', '소요 시간 1시간 미만')."
        description="A list of 2 to 4 strict rules/constraints for the final quest recommendation agent to follow (e.g., 'must be indoor', 'duration under 1 hour')."
    )

def analyze_strategy(state: RecommendState) -> Dict[str, Any]:
    """
    사용자 프로필(user_profile), 주변 상황(situation_context), 유저 요구사항(request_context)을 통합 분석하여
    추천 전략 및 벡터 DB 검색용 쿼리를 수립하는 LangGraph 노드 함수입니다.
    """
    user_profile = state.get("user_profile", {})
    situation_context = state.get("situation_context", {})
    request_context = state.get("request_context", {})
        
    try:
        llm = get_openai_model(model_name="gpt-4o-mini", temperature=0.2)  # 전략적 추론을 위해 온도=0.2
        structured_llm = llm.with_structured_output(PlannerOutput)

        """
        "당신은 전문적인 퀘스트 추천 기획자입니다. 사용자의 정보를 분석하고 추천 전략을 수립하십시오.\n\n"
        "### 입력 정보\n"
        "1. 사용자 프로필: {user_profile}\n"
        "2. 상황 컨텍스트 (날짜, 평일/주말, 날씨, 야외 활동 가능 여부): {situation_context}\n"
        "3. 사용자 커스텀 요청 컨텍스트: {request_context}\n\n"
        "위의 입력값을 바탕으로, 다음 내용을 명시하는 상세한 PlannerOutput을 구성하십시오: \n"
        "- 'strategy': 전반적인 방향성. 상황 컨텍스트의 'is_outdoor_feasible' 여부를 반드시 준수해야 하며(예: False인 경우 실내 활동으로 제한), 사용자의 커스텀 요청사항을 존중해야 합니다.\n"
        "- 'search_query': 데이터베이스에서 가장 연관성 높은 봉사활동 기회를 가져오기 위한 핵심 검색 쿼리.\n"
        "- 'llm_constraints': 퀘스트 추천 생성 에이전트가 반드시 준수해야 하는 2~4개의 실행 가능한 규칙 제약조건."
        """
        prompt = (
            f"You are a professional Quest Recommendation Planner. Analyze the user's information and plan a recommendation strategy.\n\n"
            f"### Input Information\n"
            f"1. User Profile: {user_profile}\n"
            f"2. Situation Context (Date, Weekday/Weekend, Weather, Outdoor Feasibility): {situation_context}\n"
            f"3. Custom User Request Context: {request_context}\n\n"
            f"Based on the inputs above, construct a detailed PlannerOutput specifying: \n"
            f"- 'strategy': The overall direction. Ensure it respects 'is_outdoor_feasible' from the situation context (e.g. if False, restrict to indoors) and the user's custom requests.\n"
            f"- 'search_query': A key search query to fetch the most relevant volunteer opportunities from the database.\n"
            f"- 'llm_constraints': 2 to 4 actionable rules that the quest recommendation generator must follow."
        )

        response = structured_llm.invoke(prompt)
        strategy_dict = response.model_dump()

        return {"recommendation_strategy": strategy_dict}
    
    except Exception as e:
        logger.warning(f"Failed to plan recommendation strategy using OpenAI: {e}. Fallback to default strategy.")
        
        # API 호출 및 외부 장애 발생 시 안정적인 흐름 진행을 위한 Fallback 딕셔너리 생성
        interests = user_profile.get("interests", [])
        fallback_query = ", ".join(interests) if interests else "volunteer"
        
        fallback_dict = {
            "strategy": "Recommend standard quests based on user interests.",
            "search_query": fallback_query,
            "llm_constraints": []
        }
        
        return {"recommendation_strategy": fallback_dict}

