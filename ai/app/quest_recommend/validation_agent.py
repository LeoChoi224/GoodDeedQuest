from typing import Dict, Any, List
import logging
from pydantic import BaseModel, Field

from ai.app.quest_recommend.state import RecommendState
from ai.app.common.llm import get_openai_model

from langchain_core.prompts import ChatPromptTemplate

logger = logging.getLogger(__name__)

class QuestEvaluation(BaseModel):
    """비평가 LLM이 개별 퀘스트를 심사한 결과를 담는 채점표 스키마"""
    quest_title: str=Field(
        ...,
        # "평가 대상 퀘스트의 제목"
        description="Title of the evaluated quest."
    )
    is_valid: bool=Field(
        ...,
        # "퀘스트가 안전하고 현실적이며 사용자의 제약/상황에 부합하면 True, 그렇지 않으면 False"
        description="True if the quest is safe, realistic, and matches the user's constraints/situation; False otherwise."
    )
    reason: str=Field(
        ...,
        # "승인 또는 반려에 대한 상세 사유"
        description="Detailed reason for approval or rejection."
    )

class ValidationReportOutput(BaseModel):
    """비평가 LLM이 제출할 전체 후보군 심사 보고서 스키마"""
    evaluations: List[QuestEvaluation]=Field(
        default_factory=list,
        # "모든 후보 퀘스트에 대한 평가 결과 보고서"
        description="Evaluation reports for all candidate quests."
    )

def validate_candidates(state: RecommendState) -> Dict[str, Any]:
    """
    생성된 추천 퀘스트 후보군(candidate_quests)을 대상으로
    1차 기계적 필터링(중복/누락) 및 2차 LLM 비평가(Generator-Critic) 품질 검수를 수행하는 노드 함수입니다.
    """
    candidate_quests = state.get("candidate_quests", [])
    recommendation_strategy = state.get("recommendation_strategy", {})
    user_profile = state.get("user_profile", {})
    situation_context = state.get("situation_context", {})
    request_context = state.get("request_context", {})
    retry_count = state.get("retry_count", 0)
    accumulated = list(state.get("accumulated_candidates", []))

    # 이전 회차(전체 루프) 누적 상자의 퀘스트 제목들을 미리 정규화하여 중복 목록에 등록
    seen_titles = {
        q["quest_title"].strip().lower().replace(" ", "") 
        for q in accumulated 
        if q.get("quest_title")
    }
    
    """1단계: 1차 기계적 필터링 (중복 제목 및 필수 필드 누락 제거)"""
    pre_filtered_quests= []

    for quest in candidate_quests:
        # 필수 필드 체크
        required_fields = [
        "quest_title",
        "quest_description",
        "quest_type",
        "category_name",
        "quest_target",
        "difficulty",
        ]
        if not all(quest.get(field) for field in required_fields):
            logger.warning(f"1차 검수 탈락: 필수 필드 누락. 데이터: {quest}")
            continue

        # 이전 루프 포함 전체 중복 검사 (공백/소문자 통일)
        normalized_title = quest["quest_title"].strip().lower().replace(" ", "")
        if normalized_title in seen_titles:
            logger.warning(f"1차 검수 탈락: 전 루프 포함 중복 제목 감지 ('{quest['quest_title']}').")
            continue

        seen_titles.add(normalized_title)
        pre_filtered_quests.append(quest)

    if not pre_filtered_quests:
        logger.warning("1차 검수 결과 유효한 후보 퀘스트가 없습니다.")
        return {"candidate_quests": []}

    """2단계: 2차 LLM 비평가(Critic) 심층 품질/윤리/제약조건 검수"""
    try:
        llm = get_openai_model(model_name="gpt-4o-mini", temperature=0.0)  # 일관성 있는 분석을 위해 온도=0.0
        structured_llm = llm.with_structured_output(ValidationReportOutput)

        """
        ("system", "당신은 전문적인 AI 퀘스트 품질 검수원입니다.
            사용자 프로필, 상황 컨텍스트, 요청 컨텍스트, 기획 제약조건과 대조하여 모든 후보 퀘스트들을 평가하십시오.
            엄격한 검수 지침:
            1. 안전성 및 실현 가능성 검사: 신체적으로 위험하거나, 극도로 비현실적이거나, 악용될 소지가 있는 퀘스트는 모두 반려하십시오 (is_valid=False로 설정).
            2. 제약조건 검사: 추천 전략 안의 'llm_constraints' 제약 조건을 확인하십시오. 퀘스트가 이 특정 제약 조건을 위반하는 경우 (예: '실내 활동 필수'인데 실외 활동이거나 주소지가 실외인 경우) is_valid=False로 설정하십시오.
            3. 상황 적합성 검사: 사용자의 상황에 맞지 않는 퀘스트는 반려하십시오 (예: 사용자가 감기에 걸린 경우, 강도 높은 신체 활동은 반려하십시오).
            4. 비평 사유: 퀘스트를 승인하거나 반려한 구체적이고 명확한 이유를 제공하십시오."),
        ("human", "### 입력 정보
            1. 사용자 프로필: {user_profile}
            2. 상황 컨텍스트: {situation_context}
            3. 사용자 커스텀 요청 컨텍스트: {request_context}
            4. 추천 전략 및 제약조건: {recommendation_strategy}
            ### 평가할 퀘스트 목록
            {quests_to_evaluate}")
        """
        validation_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a professional AI Quest Quality Inspector.
Evaluate all the candidate quests against the user profile, situation context, request context, and planning constraints.
Strict Inspection Guidelines:
1. Safety & Reality Check: Reject any quest that is physically dangerous, highly unrealistic, or could be abused (set is_valid=False).
2. Constraint Check: Check the 'llm_constraints' inside the Recommendation Strategy. If a quest violates any of those specific constraints (e.g. if 'must be indoor', location must be None and all tasks must be indoor friendly), set is_valid=False.
3. Context Alignment Check: Reject tasks that do not fit the user's situation (e.g. if the user has a cold, reject high-effort physical tasks).
4. Reason: Provide a detailed, clear explanation for why the quest was approved or rejected."""),
        ("human", """### Inputs
1. User Profile: {user_profile}
2. Situation Context: {situation_context}
3. Custom Request Context: {request_context}
4. Recommendation Strategy & Constraints: {recommendation_strategy}
### Quests to Evaluate
{quests_to_evaluate}""")
        ])

        validation_chain = validation_prompt | structured_llm

        response = validation_chain.invoke({
            "user_profile": user_profile,
            "situation_context": situation_context,
            "request_context": request_context,
            "recommendation_strategy": recommendation_strategy,
            "quests_to_evaluate": pre_filtered_quests
        })
        title_to_evaluation = {eval_item.quest_title: eval_item for eval_item in response.evaluations}

        # 합격품만 선별
        final_quests = []
        for q in pre_filtered_quests:
            eval_report = title_to_evaluation.get(q["quest_title"])

            if not (eval_report and eval_report.is_valid):
                reason = eval_report.reason if eval_report else "No evaluation report received from Critic."
                logger.warning(f"2차 검수 탈락: 퀘스트 '{q['quest_title']}' 반려 사유: {reason}")
                continue

            final_quests.append(q)
            accumulated.append(q)

        logger.info(f"품질 검수 완료. 최종 합격: {len(final_quests)}개 / 원본 후보: {len(candidate_quests)}개")

        return {
            "candidate_quests": final_quests,
            "accumulated_candidates": accumulated
        }

    except Exception as e:
        logger.warning(f"비평가 LLM 호출 실패: {e}. 1차 필터링 목록으로 임시 대체합니다.")
        return {"candidate_quests": pre_filtered_quests}

def route_validation(state: RecommendState) -> str:
    """
    검증 결과(candidate_quests)와 재시도 횟수(retry_count)를 분석하여
    다음으로 이동할 랭그래프 노드(response / planner / retrieval)를 결정하는 라우터 함수입니다.
    """
    candidate_quests = state.get("candidate_quests", [])
    retrieved_volunteers = state.get("retrieved_volunteers", [])
    retry_count = state.get("retry_count", 0)

    candidate_count = len(candidate_quests)
    # 1. 합격 통과 (Pass) - 최종 추천 후보 5개 이상 확보 완료
    if candidate_count >= 5:
        logger.info(f"검증 통과: 최종 추천 후보 {candidate_count}개 확보 완료. 응답 생성 노드로 이동합니다.")
        return "response"

    # 2. 재시도 횟수 초과 (Max Retries Reached) - 무한 루프 방지를 위한 강제 폴백 종료
    if retry_count >= 3:
        logger.warning(f"재시도 횟수 초과 (현재 {retry_count}회): 후보 {candidate_count}개로 최종 응답을 구성합니다.")
        return "response"

    # 3. 검색 결과 부족 - 검색된 원본 봉사 데이터가 아예 없어 재생성이 필요한 경우
    if not retrieved_volunteers:
        logger.info("검색된 봉사활동 데이터 부족: 추가 수집을 위해 검색 툴로 회귀합니다.")
        return "retrieval"

    # 4. 추천 품질 낮음 - 검색 데이터는 존재하나 비평가(Critic) 심사에서 반려되어 후보가 부족해진 경우
    logger.warning(f"비평가 검수 탈락으로 인한 후보 부족 (현재 {candidate_count}개): 추천 전략 재수립을 위해 플래너로 회귀합니다.")
    return "planner"
