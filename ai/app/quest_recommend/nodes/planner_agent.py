from pydantic import BaseModel, Field
import logging
import httpx
import openai
from typing import Dict, Any, List

from ai.app.quest_recommend.state import RecommendState
from ai.app.common.llm import get_openai_model, invoke_gemini_fallback

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.exceptions import OutputParserException

logger = logging.getLogger(__name__)

class PlannerOutput(BaseModel):
    """유저 프로필과 실시간 기상/요일 상황을 융합 분석하여 도출한 추천 전략 및 쿼리 정보를 담는 Pydantic 스키마"""
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
    Critic 비평가의 반려 사유(rejection_reasons) 피드백이 존재할 경우 전략과 쿼리를 스마트하게 보정합니다.
    """
    user_profile = state.get("user_profile", {})
    situation_context = state.get("situation_context", {})
    request_context = state.get("request_context", {})
    retry_count = state.get("retry_count", 0)
    rejection_reasons = state.get("rejection_reasons", [])

    model_name = "gpt-4o" if rejection_reasons else "gpt-4o-mini"

    # Critic 반려 사유 피드백 지침 구성
    rejection_feedback = ""
    if rejection_reasons:
        logger.info(f"Critic 반려 피드백 수용 전략 보정 가동 (반려 건수: {len(rejection_reasons)}건)")
        # \n- 치명적 반려 피드백: 이전 퀘스트 후보들이 다음 이유로 반려되었습니다: {rejection_reasons}. 이 반려 사유들을 극복할 수 있도록 search_query와 llm_constraints를 엄격하게 보정하십시오!
        rejection_feedback = f"\n- CRITICAL REJECTION FEEDBACK: Previous quest candidates were rejected due to: {rejection_reasons}. Adjust search_query and llm_constraints strictly to overcome these rejections!"

    """
    ("system", ("당신은 전문적인 퀘스트 추천 기획자입니다. 사용자의 정보를 분석하고 추천 전략을 수립하십시오.
        입력값을 바탕으로 다음 내용을 명시하는 상세한 PlannerOutput을 구성하십시오:
        - 'strategy': 전반적인 방향성. 상황 컨텍스트의 'is_outdoor_feasible' 여부를 반드시 준수해야 하며(예: False인 경우 실내 활동으로 제한), 사용자의 커스텀 요청 컨텍스트를 존중해야 합니다.
        - 'search_query': 벡터 데이터베이스에서 가장 연관성 높은 봉사활동을 찾기 위한 최적화된 검색 쿼리 키워드.
        - 'llm_constraints': 퀘스트 추천 생성 에이전트가 반드시 준수해야 하는 2~4개의 실행 가능한 규칙 제약조건.
        {rejection_feedback}")),
    ("human", ("### 입력 정보
        1. 사용자 프로필: {user_profile}
        2. 상황 컨텍스트 (날짜, 평일/주말, 날씨, 야외 활동 가능 여부): {situation_context}
        3. 사용자 커스텀 요청 컨텍스트: {request_context}"))
    """
    planner_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a professional Quest Recommendation Planner. Analyze the user's information and plan a recommendation strategy.
Based on the inputs, construct a detailed PlannerOutput specifying:
- 'strategy': The overall direction. Ensure it strictly respects 'is_outdoor_feasible' from the situation context (e.g., if False, restrict to indoors) and respects the user's custom request context.
- 'search_query': An optimized search query keyword to find the most relevant volunteer tasks from the vector database.
- 'llm_constraints': 2 to 4 actionable rules that the quest recommendation generator must follow.{rejection_feedback}"""),
        ("human", """### Input Information
1. User Profile: {user_profile}
2. Situation Context (Date, Weekday/Weekend, Weather, Outdoor Feasibility): {situation_context}
3. Custom User Request Context: {request_context}""")
    ])

    input_data = {
        "user_profile": user_profile,
        "situation_context": situation_context,
        "request_context": request_context,
        "rejection_feedback": rejection_feedback
    }

    response = None
    try:
        # 1. 정상 연산: OpenAI 모델 호출
        llm = get_openai_model(model_name=model_name, temperature=0.2)  # 전략적 추론을 위해 온도=0.2
        structured_llm = llm.with_structured_output(PlannerOutput)

        planner_chain = planner_prompt | structured_llm
        response = planner_chain.invoke(input_data)

    except (openai.OpenAIError, OutputParserException, httpx.HTTPError) as e:
        # 2. OpenAI 장애 발생 시 Gemini 백업 함수 호출
        logger.warning(f"OpenAI 전략 수립 중 예외 발생 ({e}). Gemini 백업 모델을 가동합니다.")
        response = invoke_gemini_fallback(
            prompt=planner_prompt,
            input_data=input_data,
            structured_schema=PlannerOutput,
            temperature=0.2
        )
    except Exception as e:
        logger.error(f"전략 수립 중 비정상 예외 발생: {e}")

    # 3. 정상 반환 (OpenAI 또는 Gemini 성공 시)
    if response:
        strategy_dict = response.model_dump()
        new_retry = retry_count + 1 if state.get("recommendation_strategy") else retry_count
        return {
            "recommendation_strategy": strategy_dict,
            "retry_count": new_retry
        }
    
    # 4. 양대 LLM 모두 실패 시 안전 기본 전략 반환 (Defensive Fallback)
    logger.warning("양대 LLM 모두 실패. 사용자 관심 기반 안전 기본 전략으로 방어합니다.")
    interests = user_profile.get("interests", [])
    fallback_query = ", ".join(interests) if interests else "volunteer"
    
    return {
        "recommendation_strategy": {
            "strategy": "Recommend standard quests based on user interests.",
            "search_query": fallback_query,
            "llm_constraints": []
        }
    }