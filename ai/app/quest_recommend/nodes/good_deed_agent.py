import logging
from typing import Dict, Any, Optional, List, Final

import httpx
import openai
from pydantic import BaseModel, Field
from langchain_core.exceptions import OutputParserException
from langchain_core.prompts import ChatPromptTemplate

from ai.app.common.llm import get_openai_model, invoke_gemini_fallback
from ai.app.quest_recommend.state import RecommendState


logger: Final = logging.getLogger(__name__)

class GoodDeedCandidate(BaseModel):
    """유저 맞춤형 일상 선행(GOOD_DEED) 퀘스트의 세부 항목 스키마"""
    category_name: str = Field(
        ...,
        # "유저 관심사 기반 카테고리 ('ENVIRONMENT', 'SHARING', 'ANIMAL', 'COMMUNITY', 'OTHER')"
        description="Category name matching user interests (e.g., 'ENVIRONMENT', 'SHARING', 'ANIMAL', 'COMMUNITY', 'OTHER')."
    )
    quest_title: str = Field(
        ...,
        # "AI가 기발하게 창작한 일상 선행 퀘스트 제목 (반드시 한국어)"
        description="The title of the daily good deed quest. MUST be written in Korean, because it is shown directly to Korean end users."
    )
    quest_description: str = Field(
        ...,
        # "퀘스트의 명확한 실천 지침 및 재미있는 상세 설명 (반드시 한국어)"
        description="Detailed description and execution guide of the quest. MUST be written in Korean, because it is shown directly to Korean end users."
    )
    quest_target: str = Field(
        ...,
        # "퀘스트 참여 모드 ('SOLO': 개인 / 'TEAM': 협동)"
        description="Target participation mode: 'SOLO' or 'TEAM'."
    )
    quest_type: str = Field(
        "GOOD_DEED",
        # "퀘스트 유형 (AI 창작 일상 선행은 고정값 'GOOD_DEED')"
        description="Type of the quest: Always 'GOOD_DEED' for AI created tasks."
    )
    location: Optional[str] = Field(
        None,
        # "일상 선행 퀘스트는 장소 제약이 없으므로 항상 None"
        description="Must be null/None for GOOD_DEED daily quests."
    )
    difficulty: str = Field(
        ...,
        # "체감 난이도 ('VERY_EASY', 'EASY', 'NORMAL', 'HARD', 'VERY_HARD')"
        description="Quest difficulty: 'VERY_EASY', 'EASY', 'NORMAL', 'HARD', 'VERY_HARD'."
    )
    estimated_duration: Optional[int] = Field(
        15,
        # "부담 없이 실천할 수 있는 분 단위 예상 소요 시간"
        description="Estimated duration in minutes (e.g., 10, 15, 30)."
    )
    recommendation_reason: str = Field(
        ...,
        # "유저의 현재 상황, 날씨, 요청에 딱 맞춘 공감형 추천 사유 (한글)"
        description="Why this quest is recommended for the user based on their situation. Write the recommendation reason in Korean."
    )
    priority_score: int = Field(
        ...,
        # "상황 맞춤 적합도 점수 (1~10점, 10점이 최고 점수)"
        description="Priority score from 1 to 10 indicating suitability (10 is highest)."
    )
class GoodDeedCandidatesOutput(BaseModel):
    """LLM이 최종 출력할 센스 있는 AI 일상 선행 6개 묶음 스키마"""
    quests: List[GoodDeedCandidate] = Field(
        default_factory=list,
        # "유저 맞춤형 AI 일상 선행 퀘스트 후보 6개 리스트"
        description="A list of exactly 6 AI-created daily good deeds."
    )

def create_good_deeds(state: RecommendState) -> Dict[str, Any]:
    """
    추천 전략을 기반으로 유저 상황에 맞춘 순수 AI 일상 선행(GOOD_DEED)
    6개를 독립 창작하여 병합 후보군(candidate_quests)을 구성하는 노드 함수입니다.
    Critic 비평가의 반려 사유(rejection_reasons_en)가 존재할 경우 프롬프트에 주입해 재창작 품질을 보정합니다.
    """
    user_profile = state.get("user_profile", {})
    situation_context = state.get("situation_context", {})
    request_context = state.get("request_context", {})
    recommendation_strategy = state.get("recommendation_strategy", {})
    retry_count = state.get("retry_count", 0)
    rejection_reasons = state.get("rejection_reasons_en", [])
    
    model_name = "gpt-4o" if rejection_reasons else "gpt-4o-mini"


    rejection_feedback = ""
    if rejection_reasons:
        logger.info(f"Critic 반려 피드백 수용 재창작 가동 (반려 건수: {len(rejection_reasons)}건)")
        # \n- 치명적 반려 피드백: 이전 회차에 다음 퀘스트 후보들이 품질 검수원에게 반려되었습니다: {rejection_reasons}. 같은 실수를 반복하지 말고, 지적된 사항을 명확히 충족하는 퀘스트를 생성하십시오!
        rejection_feedback = f"\n- CRITICAL REJECTION FEEDBACK: In the previous round, these quest candidates were rejected by the quality inspector: {rejection_reasons}. Do not repeat the same mistakes — generate quests that clearly satisfy the points raised there!"
    logger.info(f"AI 일상 선행 퀘스트 6개 독립 창작 가동 (시도 차수: {retry_count}, 선택 모델: {model_name})")

    """
    ("system", "당신은 전문적인 AI 퀘스트 추천 생성기입니다.
        사용자의 상황, 날씨 및 제약조건에 맞춰 기발하고 실천 가능한 일상 선행(GOOD_DEED) 퀘스트를 정확히 6개 생성하십시오.
        ### 생성 규칙
        - 추천 전략 안의 'llm_constraints' 제약조건을 엄격히 준수하십시오 (예: '실내 필수'인 경우 실내 친화적인 활동만 생성하십시오).
        - 사용자의 제외 목록(exclusions)에 일치하는 퀘스트 제목은 절대 생성하지 마십시오.
        - 생성되는 6개 퀘스트 후보 세트 내부에서 중복된 퀘스트 제목을 생성하지 마십시오 (각 후보는 고유한 제목을 가져야 합니다).
        - 완료 목록(completed_history)은 사용자가 선호하는 활동을 나타냅니다. 사용자의 습관을 강화하기 위해 완료 이력에 있는 유사하거나 동일한 퀘스트를 적극적으로 추천해야 합니다. 단, 다양성을 유지하기 위해 동일한 후보 세트 내에서 완료 이력의 정확한 동일 재추천은 최대 1개까지만 허용하십시오.
        - 'category_name'은 퀘스트 카테고리에 맞는 다음 영문 대문자 문자열 중 하나로 엄격하게 설정되어야 합니다:
            - 'ENVIRONMENT' (환경 관련 활동)
            - 'SHARING' (기부/나눔 관련 활동)
            - 'ANIMAL' (동물 케어/보호 관련 활동)
            - 'COMMUNITY' (지역사회 돕기 관련 활동)
            - 'OTHER' (기타 다양한 선행 활동)
        - 'quest_type'='GOOD_DEED' 및 'location'=null 로 설정하십시오.
        - 각 퀘스트 후보에 대해 사용자의 프로필, 날씨, 평일/주말 상황, 수립된 전략, 그리고 사용자가 메시지로 보낸 커스텀 요청에 어떻게 부합하는지 설명하는 상세한 맞춤형 'recommendation_reason'(추천 사유)을 한국어로 제공하십시오.
        - 적합성을 나타내는 'priority_score'(1부터 10까지의 정수, 10이 가장 높음)를 부여하십시오.
        - 모든 퀘스트의 예상 소요 시간('estimated_duration')을 분 단위 정수로 설정하십시오.
        - 'quests' 필드 아래에 정확히 6개의 후보를 출력하십시오.
        {rejection_feedback}"),
    ("human", "### 입력 정보
        1. 사용자 프로필 (관심사, 목표 난이도, 완료/제외 내역): {user_profile}
        2. 상황 컨텍스트 (평일/주말, 날씨, 야외 가능 여부): {situation_context}
        3. 커스텀 요청 컨텍스트: {request_context}
        4. 기획 전략 및 제약조건: {recommendation_strategy}")
    """
    recommendation_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a professional AI Quest Recommendation Generator.
Generate exactly 6 creative and actionable daily good deed (GOOD_DEED) quests tailored to the user's situation, weather, and constraints.
### Rules for Generation
- Strictly comply with 'llm_constraints' in the recommendation strategy (e.g. if 'must be indoor', generate only indoor-friendly tasks).
- Never generate quest titles matching the user's exclusion list (exclusions).
- Do not generate duplicate quest titles within the same generated set of 6 quest candidates (each candidate must have a unique title).
- The completed history (completed_history) represents the user's preferred activities. You should actively recommend similar or identical quests from their history to reinforce their habits. However, to maintain variety, allow at most 1 exact repetition from the completed history within the same candidate set.
- The 'category_name' must be strictly set to one of the following uppercase strings matching the quest category:
  - 'ENVIRONMENT' (for environmental tasks)
  - 'SHARING' (for donation or sharing tasks)
  - 'ANIMAL' (for animal care/protection tasks)
  - 'COMMUNITY' (for local community helper tasks)
  - 'OTHER' (for other miscellaneous tasks)
- Set 'quest_type'='GOOD_DEED' and 'location'=null.
- Provide a detailed customized 'recommendation_reason' in Korean for each quest candidate explaining how it fits the user's profile, weather, weekday/weekend context, planned strategy, and custom request messaged by the user.
- Assign a 'priority_score' (integer from 1 to 10, where 10 is the highest) representing suitability.
- Set the 'estimated_duration' for all quests in minutes as an integer.
- Output exactly 6 candidates under the 'quests' field.{rejection_feedback}"""),
        ("human", """### Inputs
1. User Profile (interests, target difficulty, completed/exclusion history): {user_profile}
2. Situation Context (weekday/weekend, weather, outdoor feasibility): {situation_context}
3. Custom Request Context: {request_context}
4. Planning Strategy & Constraints: {recommendation_strategy}""")
    ])

    input_data = {
        "user_profile": user_profile,
        "situation_context": situation_context,
        "request_context": request_context,
        "recommendation_strategy": recommendation_strategy,
        "rejection_feedback": rejection_feedback,
    }

    response = None
    try:
        # 1. 정상 연산: OpenAI 모델 호출
        llm = get_openai_model(model_name=model_name, temperature=0.7)  # 다양하고 참신한 선행 창작을 위해 온도=0.7
        structured_llm = llm.with_structured_output(GoodDeedCandidatesOutput)

        recommendation_chain = recommendation_prompt | structured_llm
        response = recommendation_chain.invoke(input_data)

    except (openai.OpenAIError, OutputParserException, httpx.HTTPError) as e:
        # 2. OpenAI 장애 발생 시 Gemini 백업 함수 호출
        logger.warning(f"OpenAI 일상 선행 창작 중 예외 발생 ({e}). Gemini 백업 모델을 가동합니다.")
        response = invoke_gemini_fallback(
            prompt=recommendation_prompt,
            input_data=input_data,
            structured_schema=GoodDeedCandidatesOutput,
            temperature=0.7
        )
    except Exception as e:
        logger.error(f"일상 선행 창작 중 비정상 예외 발생: {e}")

    # 3. 정상 반환 (OpenAI 또는 Gemini 성공 시)
    if response and response.quests:
        ai_good_deeds = [q.model_dump() for q in response.quests]
        logger.info(f"AI 일상 선행 퀘스트 6개 창작 완료.")
        return {"ai_good_deeds": ai_good_deeds}

    # 4. 양대 LLM 모두 실패 시 빈 리스트 반환
    logger.warning("양대 LLM 모두 통신 실패. 더미 데이터 대신 빈 결과를 안전 반환합니다.")
    return {"ai_good_deeds": []}


