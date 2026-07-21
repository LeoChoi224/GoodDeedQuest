from pydantic import BaseModel, Field
import logging
from typing import Dict, Any, Optional, List

from ai.app.quest_recommend.state import RecommendState
from ai.app.common.llm import get_openai_model

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
        당신은 전문적인 AI 퀘스트 추천 생성기입니다.\n
        검색된 실제 봉사 활동 데이터와 AI가 창작한 일상 선행 활동을 조합하여 정확히 6~7개의 퀘스트 후보를 생성하십시오.\n\n
        ### 입력 정보\n
        1. 사용자 프로필 (관심사, 목표 난이도, 완료/제외 내역): {user_profile}\n
        2. 상황 컨텍스트 (평일/주말, 날씨, 야외 가능 여부): {situation_context}\n
        3. 사용자 커스텀 요청 컨텍스트: {request_context}\n
        4. 추천 전략 및 제약조건: {recommendation_strategy}\n
        5. 검색된 실제 봉사 데이터: {retrieved_volunteers}\n\n
        ### 생성 규칙\n
        - 추천 전략 내의 'llm_constraints' 제약 조건을 엄격히 준수하십시오. (예: 만약 'must be indoor'가 지정되어 있다면, 모든 퀘스트의 location은 None이어야 하며 실내 친화적인 활동이어야 합니다.)\n
        - 사용자의 완료 목록(completed_history)이나 제외 목록(exclusions)에 포함된 제목과 중복되는 퀘스트는 절대 추천하지 마십시오.\n
        - '검색된 실제 봉사 데이터'에서 실제 봉사 활동을 추출해 변환하고(quest_type='VOLUNTEER'로 설정하고 제목/내용/장소를 유지할 것), 여기에 유저 상황에 알맞은 기발한 일상 선행 활동을 창작하여 융합하십시오 (quest_type='GOOD_DEED'로 설정하고 location=None으로 지정하며, 재미있고 실행 가능하도록 설계할 것).\n
        - 모든 퀘스트의 예상 소요 시간('estimated_duration')을 분 단위 정수형으로 지정하십시오.\n
        - 'quests' 필드 아래에 정확히 6~7개의 후보를 출력하십시오.
        """
        prompt = (
            f"You are a professional AI Quest Recommendation Generator.\n"
            f"Generate exactly 6 to 7 quest candidates combining retrieved real volunteer works and AI-created daily good deeds.\n\n"
            f"### Inputs\n"
            f"1. User Profile (interests, target difficulty, completed/exclusion history): {user_profile}\n"
            f"2. Situation Context (weekday/weekend, weather, is_outdoor_feasible): {situation_context}\n"
            f"3. Custom Request Context: {request_context}\n"
            f"4. Planning Strategy & Constraints: {recommendation_strategy}\n"
            f"5. Retrieved Real Volunteer Tasks: {retrieved_volunteers}\n\n"
            f"### Rules\n"
            f"- Strictly follow the 'llm_constraints' in the Strategy (e.g. if 'must be indoor', location must be None and all tasks must be indoor friendly).\n"
            f"- Do not recommend any quest titles that match the user's completed history or exclusions.\n"
            f"- Mix actual volunteer tasks from 'Retrieved Real Volunteer Tasks' (set quest_type='VOLUNTEER', preserve their titles/content/location) with creative daily good deeds (set quest_type='GOOD_DEED', location=None, design them to be fun and actionable).\n"
            f"- Set 'estimated_duration' for all quests in minutes as an integer.\n"
            f"- Output exactly 6 to 7 candidates under 'quests'."
        )

        response = structured_llm.invoke(prompt)
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