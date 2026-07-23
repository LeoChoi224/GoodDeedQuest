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
        # "유저의 관심사와 매치되는 퀘스트 카테고리 이름 (예: '환경', '나눔', '동물', '지역사회', '취약계층', '기타')."
        description="Category name matching user interests (e.g., 'ENVIRONMENT', 'SHARING', 'ANIMAL', 'COMMUNITY', 'VULNERABLE_GROUP', 'OTHER')."
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
    recommendation_reason: str = Field(
        ...,
        # 사용자의 상황에 따라 이 퀘스트가 추천되는 이유.
        description="Why this quest is recommended for the user based on their situation."
    )
    priority_score: int = Field(
        ...,
        # 적합성을 나타내는 1부터 10까지의 우선순위 점수 (10이 가장 높음).
        description="Priority score from 1 to 10 indicating suitability (10 is highest)."
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
            - 추천 전략 내의 'llm_constraints' 제약 조건을 엄격히 준수하십시오. (예: 만약 '실내 활동 필수'가 지정되어 있다면, 모든 퀘스트는 실내 친화적인 활동이어야 합니다. 일상 선행(GOOD_DEED)은 location이 None이 되며, 실제 봉사(VOLUNTEER)는 주소지는 존재하되 실내 시설 내부에서 진행되는 활동이어야 합니다.)
            - 사용자의 제외 목록(exclusions)에 포함된 제목의 퀘스트는 절대 추천하지 마십시오.
            - 동일한 추천 세트(6~7개 후보군) 내부에서 제목이 서로 중복되는 퀘스트를 생성하지 마십시오 (각 후보의 제목은 고유해야 합니다).
            - 완료 목록(completed_history)은 사용자의 취향과 선호를 나타내므로, 완료 이력이 있는 활동이나 유사한 활동은 적극적으로 재추천하십시오. 단, 다양성을 위해 한 번의 추천 세트 내에서 동일한 완료 퀘스트가 중복 등장하는 것은 최대 1개까지만 허용하십시오.
            - 카테고리명('category_name')은 반드시 다음 영문 대문자 문자열 중 하나로만 지정하십시오:
            - 'ENVIRONMENT' (환경 관련 활동)
            - 'SHARING' (기부 또는 나눔 관련 활동)
            - 'ANIMAL' (동물 케어 및 보호 관련 활동)
            - 'COMMUNITY' (지역사회 돕기 관련 활동)
            - 'VULNERABLE_GROUP' (취약계층 지원 또는 봉사 관련 활동)
            - 'OTHER' (기타 다양한 선행 활동)
            - '검색된 실제 봉사 데이터'에서 실제 봉사 활동을 추출해 변환하고(quest_type='VOLUNTEER'로 설정하고 제목/내용/장소를 유지할 것), 여기에 유저 상황에 알맞은 기발한 일상 선행 활동을 창작하여 융합하십시오 (quest_type='GOOD_DEED'로 설정하고 location=None으로 지정하며, 재미있고 실행 가능하도록 설계할 것).
            - 각 퀘스트 후보에 대해 사용자의 관심사 및 레벨(난이도), 실시간 날씨 및 야외 가능 여부, 평일/주말 상황, 수립된 기획 전략, 그리고 사용자가 직접 메시지로 요구한 특별한 요청사항(예: 건강 상태, 소요 시간, 시간대 선호 등)에 어떻게 정교하게 부합하는지 설명하는 맞춤형 'recommendation_reason'(추천 사유)을 한국어로 자세히 작성하십시오.
            - 각 퀘스트가 사용자에게 얼마나 적합한지 나타내는 'priority_score'(1부터 10까지의 정수, 10이 가장 높음)를 부여하십시오.
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
- Strictly comply with the 'llm_constraints' in the recommendation strategy. (e.g., if 'must be indoor' is specified, all recommended quests must be indoor-friendly activities. Note that GOOD_DEED tasks will have location as None, but VOLUNTEER tasks will have their valid locations but must take place indoors.)
- Never recommend quests whose titles match the user's exclusion list (exclusions).
- Do not recommend duplicate quest titles within the same generated set of 6 to 7 quest candidates (each candidate must have a unique title).
- The completed history (completed_history) represents the user's preferred activities. You should actively recommend similar or identical quests from their history to reinforce their habits. However, to maintain variety, allow at most 1 exact repetition from the completed history within the same candidate set.
- The 'category_name' must be strictly set to one of the following uppercase strings matching the quest category:
  - 'ENVIRONMENT' (for environmental tasks)
  - 'SHARING' (for donation or sharing tasks)
  - 'ANIMAL' (for animal care/protection tasks)
  - 'COMMUNITY' (for local community helper tasks)
  - 'VULNERABLE_GROUP' (for volunteering or supporting vulnerable groups)
  - 'OTHER' (for other miscellaneous tasks)
- Extract and convert actual volunteer tasks from the 'Retrieved Real Volunteer Tasks' (set quest_type='VOLUNTEER', and preserve their titles, content, and location), and blend them with creative daily good deeds tailored to the user's situation (set quest_type='GOOD_DEED', location=None, and design them to be fun and actionable).
- For each quest candidate, provide a customized 'recommendation_reason' in Korean explaining in detail how this task aligns with the user's interests and level, real-time weather and outdoor feasibility, weekday/weekend availability, the planned strategy, and any specific custom request (e.g., physical condition, preferred duration, or time constraints) they messaged.
- Assign a 'priority_score' (integer from 1 to 10, where 10 is the highest) representing how suitable the quest is for the user.
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
        logger.warning(f"OpenAI를 통한 퀘스트 후보 생성 실패: {e}. 기본 일상 선행으로 폴백합니다.")

        # API 오류 발생 시 시스템 중단을 방지하기 위해 2개의 기본 일상 선행을 Fallback 결과로 구성
        interests = user_profile.get("interests", []) if user_profile else []
        primary_category = interests[0] if interests else "ENVIRONMENT"

        fallback_quests = [
            {
                "category_name": primary_category,
                "quest_title": "텀블러 사용하기",
                "quest_description": "일회용 컵 대신 개인 텀블러를 사용하여 온실가스 배출을 줄입니다.",
                "quest_target": "SOLO",
                "quest_type": "GOOD_DEED",
                "location": None,
                "difficulty": "VERY_EASY",
                "estimated_duration": 5,
                "recommendation_reason": "일회용품을 줄이고 환경을 보호할 수 있는 가장 대표적인 일상 선행 활동입니다.",
                "priority_score": 9,
            },
            {
                "category_name": primary_category,
                "quest_title": "분리배출 꼼꼼히 하기",
                "quest_description": "재활용품의 이물질을 세척하고 올바른 분류함에 배출합니다.",
                "quest_target": "SOLO",
                "quest_type": "GOOD_DEED",
                "location": None,
                "difficulty": "EASY",
                "estimated_duration": 10,
                "recommendation_reason": "올바른 분리배출을 통해 재활용률을 높이고 환경을 정화하는 데 기여합니다.",
                "priority_score": 8,
            }
        ]
        
        return {"candidate_quests": fallback_quests}