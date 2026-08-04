import logging
from typing import Dict, Any, List, Final

import httpx
import openai
from pydantic import BaseModel, Field
from langchain_core.exceptions import OutputParserException
from langchain_core.prompts import ChatPromptTemplate

from ai.app.common.llm import get_openai_model, invoke_gemini_fallback
from ai.app.quest_recommend.state import RecommendState


logger: Final = logging.getLogger(__name__)

class QuestEvaluation(BaseModel):
    """비평가 LLM이 개별 퀘스트를 심사한 결과를 담는 채점표 스키마"""
    quest_title: str = Field(
        ...,
        # "평가 대상 퀘스트의 제목. 입력받은 문자열을 글자 그대로 복사할 것"
        description="Title of the evaluated quest. Copy the input string exactly, character for character."
    )
    is_valid: bool = Field(
        ...,
        # "퀘스트가 안전하고 현실적이며 사용자의 제약/상황에 부합하면 True, 그렇지 않으면 False"
        description="True if the quest is safe, realistic, and matches the user's constraints/situation; False otherwise."
    )
    reason: str = Field(
        ...,
        # "판단 사유 (영문 Planner 피드백용). 승인이면 짧은 구 하나, 반려면 상세히"
        description="Reason for the decision, in English, used as Planner feedback. If is_valid is true, write only a short phrase (e.g. 'Fits interests'). If is_valid is false, explain the specific problem in detail so the planner can correct it."
    )
    reason_ko: str = Field(
        ...,
        # "판단 사유 (한국어 터미널 로그용). 승인이면 짧은 구 하나, 반려면 상세히"
        description="Same as 'reason' but written in Korean for terminal logging. Keep it to a short phrase when is_valid is true, and detailed when is_valid is false."
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
    실제 봉사(retrieved_volunteers)와 AI가 생성한 일상 선행(ai_good_deeds)을 대상으로
    1차 기계적 필터링(중복/누락) 및 2차 LLM 비평가(Generator-Critic) 품질 검수를 수행하는 노드 함수입니다.
    반려된 퀘스트의 영문 사유(reason)는 rejection_reasons에 수집되어 Planner 피드백으로 전달되며,
    한글 사유(reason_ko)는 로그 용으로 기록됩니다.
    """
    retrieved_volunteers = state.get("retrieved_volunteers", [])
    ai_good_deeds = state.get("ai_good_deeds", [])
    recommendation_strategy = state.get("recommendation_strategy", {})
    user_profile = state.get("user_profile", {})
    situation_context = state.get("situation_context", {})
    request_context = state.get("request_context", {})
    accumulated = list(state.get("accumulated_candidates", []))
    rejection_reasons_en = list(state.get("rejection_reasons_en", []))
    rejection_reasons_ko = list(state.get("rejection_reasons_ko", []))

    # 이전 회차(전체 루프) 누적 상자의 퀘스트 제목들을 미리 정규화하여 중복 목록에 등록
    seen_titles = {
        (q.get("source_title") or q.get("quest_title") or "").strip().lower().replace(" ", "")
        for q in accumulated
        if q.get("source_title") or q.get("quest_title")
    }
    
    """1단계: 1차 기계적 필터링 (중복 제목 및 필수 필드 누락 제거)"""
    pre_filtered_quests= []

    # 1-1. 실제 봉사 데이터 매핑 (LLM 환각 0% 보존)
    for rank_index, vol in enumerate(retrieved_volunteers):
        source_title = vol.get("title") or "봉사활동"
        title = vol.get("quest_title") or source_title

        normalized_title = source_title.strip().lower().replace(" ", "")
        if normalized_title in seen_titles:
            continue
        seen_titles.add(normalized_title)

        quest_description = vol.get("quest_summary") or "지역 봉사활동 참여"
        vol_location = vol.get("location") or "장소 미지정"

        # 검색 상위일수록 높은 점수 (10, 9, 8 ... 최저 6점)
        volunteer_score = max(10 - rank_index, 6)

        pre_filtered_quests.append({
            "category_name": "VOLUNTEER",
            "quest_title": title,
            "quest_description": quest_description,
            "quest_target": "SOLO",
            "quest_type": "VOLUNTEER",
            "location": vol_location,
            "difficulty": "NORMAL",
            "intensity": 80,
            "estimated_duration": 180,
            "recommendation_reason": f"사용자 주변에 위치한 실제 봉사활동 기회입니다. ({vol_location})",
            "priority_score": volunteer_score,
            "center_id": vol.get("id"),
            "target": vol.get("target") or "지역 주민",
            "source_title": source_title,
        })

    # 1-2. AI 생성 일상 선행 데이터 1차 기계적 필터링
    for quest in ai_good_deeds:
        required_fields = ["quest_title", "quest_description", "quest_type", "category_name", "quest_target", "difficulty"]
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
        return {
            "candidate_quests": [],
            "accumulated_candidates": accumulated
        }

    """2단계: 2차 LLM 비평가(Critic) 심층 품질/윤리/제약조건 검수"""

    """
    ("system", "당신은 전문 AI 퀘스트 품질 검사관입니다.
        당신의 역할은 사용자에게 정말로 부적합한 퀘스트만 걸러내는 것이며, 가장 적합한 퀘스트를 선택하는 것이 아닙니다. 순위 결정은 별도의 점수 산정 단계에서 수행되므로, 단순히 "완벽하게 맞지는 않는" 퀘스트라면 통과시켜야 합니다. 명확하고 구체적인 문제가 있는 경우에만 Reject 하세요.
        각 퀘스트에는 'quest_type'이 있습니다.
        - 'GOOD_DEED'는 다른 AI 에이전트가 자유롭게 생성한 퀘스트이며 다시 생성할 수 있으므로, 제약 조건을 엄격하게 적용해도 됩니다.
        - 'VOLUNTEER'는 실제로 게시된 봉사활동 공고이며 일정, 대상, 장소가 이미 고정되어 있어 제약 조건에 맞게 수정할 수 없습니다.
        실제 봉사 공고에는 원본 게시물에서 그대로 가져온 'target' 필드가 있습니다(예: 청소년, 아동, 발달장애인, 입원 어르신).
        "이 활동이 누구를 돕는가"에 대한 확정된 답으로 신뢰하고, 설명문을 자의적으로 해석해 이를 뒤집지 마십시오.
        특히 봉사자의 모집 조건(연령, 자격 등)과 활동의 수혜 대상을 혼동하지 마십시오. 성인 봉사자를 모집하는 청소년 대상 활동은 청소년 관련 활동입니다.
        다음 경우에만 Reject(is_valid=False) 하세요.
        1. Safety: 퀘스트가 신체적으로 위험하거나, 명백히 비현실적이거나, 악용될 가능성이 있는 경우입니다.
        2. 최근 추천 중복: 'recently_recommended' 목록의 제목과 사실상 동일한 퀘스트인 경우입니다. 이 목록은 최근에 이 사용자에게 추천된 퀘스트 제목이며, 사용자가 싫어한다고 밝힌 주제가 아닙니다. 제목이 거의 같을 때만 반려하고, 주제·대상·카테고리가 겹친다는 이유로는 절대 반려하지 마십시오.
        조건 판단에 앞서, 사용자 관심사 코드 6종의 범위를 확인하세요.
        - volunteer: 봉사활동 전반
        - environment: 환경 정화, 재활용, 자원 절약, 기후 대응
        - sharing: 기부, 물품 나눔, 식사 나눔
        - animal: 유기동물 보호, 동물 돌봄
        - community: 이웃 돕기, 지역 행사, 그리고 노인·장애인·아동·저소득층·다문화 가정 등 지역 주민을 돕는 활동을 모두 포함합니다. 장애인 지원과 어르신 지원은 COMMUNITY입니다.
        - other: 위에 속하지 않는 선행
        3. Hard incompatibility with 'llm_constraints': 퀘스트가 llm_constraints와 명백하게 충돌하는 경우입니다. 표현이 아니라 실제 의미를 기준으로 판단하세요. 청소년 멘토를 모집하는 봉사활동은 청소년 관련 조건을 충족하는 것으로 봐야 하며, 장애인을 돕는 봉사활동도 지역사회 봉사 조건을 충족하는 것으로 봐야 합니다. 합리적인 사람이 보기에 해당 조건과 관련이 있다고 판단된다면 통과시켜야 합니다.
        4. 'VOLUNTEER'인 경우에만: 안전 문제, 최근 추천 목록과 제목이 거의 같은 경우, 또는 사용자가 실제로 언급한 일정 충돌이 있는 경우에만 Reject 하세요. 실제 봉사활동 공고는 주제가 완벽하게 일치하지 않는다는 이유, 여러 번 참여해야 한다는 이유, 경험자가 더 적합해 보인다는 이유, 특정 요일에 진행된다는 이유로 Reject 하면 안 됩니다.
        퀘스트가 "가장 적합한 후보가 아니다", 설명이 부족하다, 다른 후보들과 단순히 다르다는 이유로는 Reject 하면 안 됩니다.
        'VOLUNTEER'의 'quest_description'은 원본 공고를 요약한 한 문장입니다. 내용이 짧거나 세부 정보가 없다는 이유로 Reject 하지 마십시오. 원문 전체는 사용자에게 별도 화면으로 제공됩니다.
        분량 규칙: 승인(is_valid=true)한 경우 'reason'과 'reason_ko'에 짧은 구 하나만 쓰세요(예: 'Fits interests' / '관심사에 부합'). 승인 사유는 이후 단계에서 사용되지 않습니다. 반려(is_valid=false)한 경우에만 Planner가 교정할 수 있도록 구체적인 문제를 상세히 설명하세요.
        'quest_title'은 입력받은 문자열을 글자 그대로 복사하세요."),
    ("human", "### 입력 정보
        1. 사용자 프로필: {user_profile}
        2. 상황 컨텍스트: {situation_context}
        3. 사용자 커스텀 요청 컨텍스트: {request_context}
        4. 추천 전략 및 제약조건: {recommendation_strategy}
        ### 평가할 퀘스트 목록
        {pre_filtered_quests}")
    """
    validation_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a professional AI Quest Quality Inspector.
Your job is to filter out quests that are genuinely unsuitable — not to pick the single best match. Ranking is handled separately by a scoring step, so a quest that is merely "not a perfect fit" must still pass. Reject only when there is a clear, concrete problem you can point to.
Each quest has a 'quest_type':
- 'GOOD_DEED' was freely generated by another AI agent and can be regenerated, so you may hold it strictly to the constraints.
- 'VOLUNTEER' is a real, already-published listing with a fixed schedule, audience and venue. It cannot be rewritten to match constraints.
Real volunteer postings carry a 'target' field taken directly from the original listing (e.g. 청소년, 아동, 발달장애인, 입원 어르신). Trust it as the authoritative answer to "who does this activity help". Do not contradict it based on your own reading of the description.
In particular, never confuse the volunteer recruitment criteria (age, qualifications) with the beneficiaries of the activity. A posting that recruits adult volunteers to help teenagers IS a youth-related activity.
Reject (is_valid=False) only for these reasons:
1. Safety: the quest is physically dangerous, clearly unrealistic, or open to abuse.
2. Recently recommended duplicate: the quest title is effectively identical to an entry in 'recently_recommended'. That list is a history of titles already shown to this user — it is NOT a list of topics the user dislikes. Reject only on a near-identical title. Never reject because a quest shares a theme, an audience, or a category with an entry in that list.
Before judging constraints, note the scope of the six interest codes:
- volunteer: volunteer work in general
- environment: cleanups, recycling, resource saving, climate action
- sharing: donations, sharing goods, sharing meals
- animal: rescued animal care, animal welfare
- community: helping neighbours, local events, AND support for elderly people, people with disabilities, children, low-income households and multicultural families. Assisting people with disabilities IS COMMUNITY. Assisting elderly people IS COMMUNITY. Never reject those as unrelated to a COMMUNITY interest.
- other: good deeds that fit none of the above
3. Hard incompatibility with 'llm_constraints': the quest plainly contradicts a constraint. Judge by substance, not by wording — a listing recruiting adult mentors for teenagers DOES relate to youth, and a listing that assists disabled residents DOES count as community service. If a reasonable person would say the quest is related to what the constraint asks for, it passes.
4. For 'VOLUNTEER' only: reject solely on safety, on a near-identical title in 'recently_recommended', or on a scheduling conflict that the user actually stated. Do not reject a real listing for being an imperfect thematic match, for requiring multiple sessions, for suiting experienced participants, or for falling on a particular day of the week.
Do not reject a quest for being "not the most relevant option available", for lacking detail, or for merely being different from the other candidates.
The 'quest_description' of a 'VOLUNTEER' is a one-sentence summary of the original posting. Never reject it for being short or lacking detail — the full original text is shown to the user on a separate screen.
LENGTH RULES — follow these exactly, they control response latency:
- When is_valid is true, write only a short phrase in 'reason' and 'reason_ko' (e.g. 'Fits interests' / '관심사에 부합'). Approval reasons are never read by any later step, so anything longer is wasted.
- When is_valid is false, explain the specific problem in detail so the planner can correct it.
- Copy 'quest_title' from the input exactly, character for character."""),
        ("human", """### Inputs
1. User Profile: {user_profile}
2. Situation Context: {situation_context}
3. Custom Request Context: {request_context}
4. Recommendation Strategy & Constraints: {recommendation_strategy}
### Quests to Evaluate
{pre_filtered_quests}""")
    ])

    input_data = {
        "user_profile": user_profile,
        "situation_context": situation_context,
        "request_context": request_context,
        "recommendation_strategy": recommendation_strategy,
        "pre_filtered_quests": pre_filtered_quests
    }

    response = None
    try:
        # 1. 정상 연산: OpenAI 모델 호출
        llm = get_openai_model(model_name="gpt-4o-mini", temperature=0.0)  # 일관성 있는 분석을 위해 온도=0.0
        structured_llm = llm.with_structured_output(ValidationReportOutput)

        validation_chain = validation_prompt | structured_llm
        response = validation_chain.invoke(input_data)

    except (openai.OpenAIError, OutputParserException, httpx.HTTPError) as e:
        # 2. OpenAI 장애 발생 시 Gemini 백업 함수 호출
        logger.warning(f"OpenAI 품질 검수 중 예외 발생 ({e}). Gemini 백업 모델을 가동합니다.")
        response = invoke_gemini_fallback(
            prompt=validation_prompt,
            input_data=input_data,
            structured_schema=ValidationReportOutput,
            temperature=0.0
        )
    except Exception as e:
        logger.warning(f"비평가 LLM 호출 실패: {e}. 1차 필터링 목록으로 임시 대체합니다.")

    # 3. 정상 반환 (OpenAI 또는 Gemini 성공 시)
    if response and response.evaluations:
        title_to_evaluation = {eval_item.quest_title: eval_item for eval_item in response.evaluations}

        final_quests = []
        for q in pre_filtered_quests:
            eval_report = title_to_evaluation.get(q["quest_title"])

            if not (eval_report and eval_report.is_valid):
                reason_en = eval_report.reason if eval_report and eval_report.reason else "Rejected by Critic."
                reason_ko = eval_report.reason_ko if eval_report and eval_report.reason_ko else "Critic 검수 보고서 미수신."

                rejection_reasons_en.append(f"'{q.get('quest_title')}': {reason_en}")
                rejection_reasons_ko.append(f"'{q.get('quest_title')}': {reason_ko}")
                logger.warning(f"2차 검수 탈락: 퀘스트 '{q['quest_title']}' 반려 사유: {reason_ko}")
                continue

            final_quests.append(q)
            accumulated.append(q)

        logger.info(f"품질 검수 완료. 최종 합격: {len(final_quests)}개 / 누적 합격: {len(accumulated)}개")
        
        return {
            "candidate_quests": final_quests,
            "accumulated_candidates": accumulated,
            "rejection_reasons_en": rejection_reasons_en,
            "rejection_reasons_ko": rejection_reasons_ko
        }

    # 4. 양대 LLM 모두 실패 시 빈 리스트 반환
    return {
        "candidate_quests": pre_filtered_quests,
        "accumulated_candidates": accumulated
        }

def route_validation(state: RecommendState) -> str:
    """
    검증 결과(candidate_quests / accumulated_candidates)와 재시도 횟수(retry_count)를 분석하여
    다음으로 이동할 랭그래프 노드(response / planner / volunteer)를 결정하는 라우터 함수입니다.
    """
    candidate_quests = state.get("candidate_quests", [])
    accumulated_candidates = state.get("accumulated_candidates", [])
    retrieved_volunteers = state.get("retrieved_volunteers", [])
    retry_count = state.get("retry_count", 0)
    skip_volunteer_agent = state.get("skip_volunteer_agent", False)

    total_candidates_count = len(accumulated_candidates) or len(candidate_quests)

    # 1. 합격 통과 (Pass) - 최종 추천 후보 5개 이상 확보 완료
    if total_candidates_count >= 5:
        logger.info(f"검증 통과: 최종 추천 후보 {total_candidates_count}개 확보 완료. 응답 생성 노드로 이동합니다.")
        return "response"
    
    # 2. 재시도 횟수 초과 (Max Retries Reached) - 무한 루프 방지를 위한 강제 폴백 종료
    if retry_count >= 2:
        logger.warning(f"재시도 횟수 초과 (현재 {retry_count}회): 후보 {total_candidates_count}개로 최종 응답을 구성합니다.")
        return "response"
    
    # 3. 봉사 데이터가 비었고 아직 '없음'이 확정되지 않은 경우에만 봉사 수색 노드로 회귀
    if not retrieved_volunteers and not skip_volunteer_agent:
        logger.info("검색된 봉사활동 데이터 부족: 추가 수집을 위해 volunteer 수색 노드로 회귀합니다.")
        return "volunteer"

    # 4. 추천 품질 낮음 - 검색 데이터는 존재하나 비평가(Critic) 심사에서 반려되어 후보가 부족해진 경우
    logger.warning(f"비평가 검수 탈락으로 인한 후보 부족 (현재 {total_candidates_count}개): 추천 전략 재수립을 위해 플래너로 회귀합니다.")
    return "planner"



