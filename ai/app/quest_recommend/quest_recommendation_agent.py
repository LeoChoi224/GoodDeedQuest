from pydantic import BaseModel, Field
import logging
from typing import Dict, Any, Optional, List

from ai.app.quest_recommend.state import RecommendState
from ai.app.common.llm import get_openai_model

from langchain_core.prompts import ChatPromptTemplate

logger = logging.getLogger(__name__)

class QuestCandidate(BaseModel):
    """최종 퀘스트 테이블 규격과 정합성이 완료된 개별 퀘스트 후보 스키마"""
    category_name: str = Field(
        ...,
        # "유저의 관심사와 매치되는 퀘스트 카테고리 이름 (예: '환경', '동물', '지역사회', '기타')."
        description="Category name matching user interests (e.g., '환경', '동물', '지역사회')."
        )
    quest_title: str = Field(
        ...,
        # "퀘스트의 제목 (예: '한강 쓰레기 줍기 플로깅', '텀블러 사용하기')."
        description="The title of the quest."
        )
    quest_description: str = Field(
        ...,
        # "퀘스트에 대한 상세한 설명 및 실천 가이드."
        description="Detailed description and execution guide of the quest."
        )
    quest_target: str = Field(
        ...,
        # "대상 참여 방식 모드: 'SOLO'(개인) 또는 'TEAM'(협동)."
        description="Target participation mode: 'SOLO' or 'TEAM'."
        )
    quest_type: str = Field(
        ...,
        # "퀘스트 종류: 실제 봉사활동의 경우 'VOLUNTEER', AI가 창작한 일상 선행의 경우 'GOOD_DEED'."
        description="Type of the quest: 'VOLUNTEER' for real volunteer works, 'GOOD_DEED' for AI-created daily good deeds."
        )
    location: Optional[str] = Field(
        None,
        # "실제 봉사(VOLUNTEER) 퀘스트의 구체적인 활동 장소 주소. 일상 선행(GOOD_DEED) 퀘스트의 경우 반드시 null/None이어야 함."
        description="Specific location address for VOLUNTEER quests. Must be null/None for GOOD_DEED."
        )
    difficulty: str = Field(
        ...,
        # "퀘스트 난이도: 'VERY_EASY'(매우 쉬움), 'EASY'(쉬움), 'NORMAL'(보통), 'HARD'(어려움), 'VERY_HARD'(매우 어려움) 중 하나."
        description="Quest difficulty: 'VERY_EASY', 'EASY', 'NORMAL', 'HARD', 'VERY_HARD'."
        )
    estimated_duration: Optional[int] = Field(
        None,
        # "분 단위로 환산한 예상 소요 시간 (예: 10, 30, 240)."
        description="Estimated duration in minutes (e.g., 10, 30, 180)."
        )

class QuestCandidatesOutput(BaseModel):
    """LLM이 최종 반환할 구조화된 후보군 목록 스키마"""
    quests: List[QuestCandidate] = Field(
        default_factory=list,
        # "실제 봉사활동과 AI가 생성한 일상 선행이 혼합되어 생성된 정확히 6~7개의 퀘스트 후보 리스트."
        description="A list of 6 to 7 generated quest candidates."
        )
    
def recommend_quests(state: RecommendState) -> Dict[str, Any]:
    """
    검색된 봉사 데이터와 추천 전략을 기반으로
    실제 봉사 및 AI 생성 일상 선행이 조합된 퀘스트 후보군(candidate_quests)을 생성하는 노드 함수입니다.
    """
    user_profile = state.get("user_profile", {})
    situation_context = state.get("situation_context", {})
    request_context = state.get("request_context", {})
    recommendation_strategy = state.get("recommendation_strategy", {})
    retrieved_volunteers = state.get("retrieved_volunteers", [])

    try:
        llm = get_openai_model(model_name="gpt-4o-mini", temperature=0.7)  # 다양하고 참신한 선행 창작을 위해 온도=0.7
        structured_llm = llm.with_structured_output(QuestCandidatesOutput)

        """
        ("system", "당신은 전문적인 AI 퀘스트 추천 생성기입니다.
            검색된 실제 봉사 활동 데이터와 AI가 창작한 일상 선행 활동을 조합하여 정확히 6~7개의 퀘스트 후보를 생성하십시오.
            ### 생성 규칙
            - 추천 전략 내의 'llm_constraints' 제약 조건을 엄격히 준수하십시오. (예: 만약 'must be indoor'가 지정되어 있다면, 모든 퀘스트의 location은 None이어야 하며 실내 친화적인 활동이어야 합니다.)
            - 사용자의 제외 목록(exclusions)에 포함된 제목과 중복되는 퀘스트는 절대 추천하지 마십시오. 완료 목록(completed_history)은 사용자의 취향과 선호를 파악하기 위한 참고 자료로만 활용하며, 완료 이력이 많은 활동은 관심사와 선호를 추론하는 근거로 사용하십시오. 동일하거나 거의 동일한 퀘스트만을 반복 추천하지 말고(최대 1개까지만 허용), 사용자가 좋아할 가능성이 높은 새로운 활동이나 기존 선호를 난이도·방식·상황 측면에서 확장한 활동, 또는 같은 가치(환경, 봉사, 건강 등)를 다른 방식으로 실천할 수 있는 창의적이고 맞춤형 퀘스트를 우선 추천하십시오.
            - '검색된 실제 봉사 데이터'에서 실제 봉사 활동을 추출해 변환하고(quest_type='VOLUNTEER'로 설정하고 제목/내용/장소를 유지할 것), 여기에 유저 상황에 알맞은 기발한 일상 선행 활동을 창작하여 융합하십시오 (quest_type='GOOD_DEED'로 설정하고 location=None으로 지정하며, 재미있고 실행 가능하도록 설계할 것).
            - 모든 퀘스트의 예상 소요 시간('estimated_duration')을 분 단위 정수형으로 지정하십시오.
            - 'quests' 필드 아래에 정확히 6~7개의 후보를 출력하십시오."),
        ("human", "### 입력 정보
            1. 사용자 프로필 (관심사, 목표 난이도, 완료/제외 내역): {user_profile}
            2. 상황 컨텍스트 (평일/주말, 날씨, 야외 가능 여부): {situation_context}
            3. 사용자 커스텀 요청 컨텍스트: {request_context}
            4. 추천 전략 및 제약조건: {recommendation_strategy}
            5. 검색된 실제 봉사 데이터: {retrieved_volunteers}")
        """
        recommendation_prompt = ChatPromptTemplate.from_messages([
           ("system", """You are a professional AI Quest Recommendation Generator.
Combine the retrieved real volunteer work data and AI-created daily good deeds to generate exactly 6 to 7 quest candidates.
### Rules for Generation
- Strictly comply with the 'llm_constraints' in the recommendation strategy. (e.g., if 'must be indoor' is specified, the location must be None and all tasks must be indoor-friendly.)
- Never recommend quests whose titles duplicate or match the user's exclusion list (exclusions). The completed history (completed_history) should only be used as a reference to understand the user's tastes and preferences; use frequently completed activities as a basis to infer interests and preferences. Do not repeatedly recommend the same or nearly identical quests (maximum 1 repetition allowed). Instead, prioritize recommending new activities the user is likely to enjoy, activities that expand their existing preferences in terms of difficulty, method, or situation, or creative and customized quests that practice the same value (environment, volunteering, health, etc.) in a different way.
- Extract and convert actual volunteer tasks from the 'Retrieved Real Volunteer Tasks' (set quest_type='VOLUNTEER', and preserve their titles, content, and location), and blend them with creative daily good deeds tailored to the user's situation (set quest_type='GOOD_DEED', location=None, and design them to be fun and actionable).
- Set the 'estimated_duration' for all quests in minutes as an integer.
- Output exactly 6 to 7 candidates under the 'quests' field."""),
            ("human", """### Inputs
1. User Profile (interests, target difficulty, completed/exclusion history): {user_profile}
2. Situation Context (weekday/weekend, weather, is_outdoor_feasible): {situation_context}
3. Custom Request Context: {request_context}
4. Planning Strategy & Constraints: {recommendation_strategy}
5. Retrieved Real Volunteer Tasks: {retrieved_volunteers}""")
        ])

        recommendation_chain = recommendation_prompt | structured_llm

        response = recommendation_chain.invoke({
            "user_profile": user_profile,
            "situation_context": situation_context,
            "request_context": request_context,
            "recommendation_strategy": recommendation_strategy,
            "retrieved_volunteers": retrieved_volunteers
            })
        candidates_list = [q.model_dump() for q in response.quests]

        return {"candidate_quests": candidates_list}

    except Exception as e:
        logger.warning(f"Failed to generate quest candidates using OpenAI: {e}. Fallback to basic good deeds.")

        # API 오류 발생 시 시스템 중단을 방지하기 위해 2개의 기본 일상 선행을 Fallback 결과로 구성
        interests = user_profile.get("interests", []) if user_profile else []
        primary_category = interests[0] if interests else "환경"

        fallback_quests = [
            {
                "category_name": primary_category,
                "quest_title": "텀블러 사용하기",
                "quest_description": "일회용 컵 대신 개인 텀블러를 사용하여 온실가스 배출을 줄입니다.",
                "quest_target": "SOLO",
                "quest_type": "GOOD_DEED",
                "location": None,
                "difficulty": "VERY_EASY",
                "estimated_duration": 5
            },
            {
                "category_name": primary_category,
                "quest_title": "분리배출 꼼꼼히 하기",
                "quest_description": "재활용품의 이물질을 세척하고 올바른 분류함에 배출합니다.",
                "quest_target": "SOLO",
                "quest_type": "GOOD_DEED",
                "location": None,
                "difficulty": "EASY",
                "estimated_duration": 10
            }
        ]
        
        return {"candidate_quests": fallback_quests}