import unittest
from unittest.mock import patch

from langchain_core.runnables import RunnableLambda

from ai.app.quest_recommend.state import RecommendState
from ai.app.quest_recommend.nodes.validation_agent import validate_candidates, route_validation

MODULE = "ai.app.quest_recommend.nodes.validation_agent"


class DummyEvaluation:
    """비평가 LLM의 개별 평가 결과를 흉내 내는 테스트용 객체"""
    def __init__(self, title, is_valid, reason, reason_ko):
        self.quest_title = title
        self.is_valid = is_valid
        self.reason = reason
        self.reason_ko = reason_ko


class DummyReport:
    """비평가 LLM의 전체 심사 보고서를 흉내 내는 테스트용 객체"""
    def __init__(self, evaluations):
        self.evaluations = evaluations


def build_state(**overrides) -> RecommendState:
    """검증 노드 테스트용 기본 State를 구성하고 필요한 값만 덮어쓰는 헬퍼"""
    base = {
        "user_profile": {"interests": ["COMMUNITY"]},
        "situation_context": {"today_weather": "sunny", "is_outdoor_feasible": True},
        "request_context": {},
        "recommendation_strategy": {"strategy": "test", "llm_constraints": []},
        "retrieved_volunteers": [],
        "ai_good_deeds": [],
        "candidate_quests": [],
        "accumulated_candidates": [],
        "rejection_reasons_en": [],
        "rejection_reasons_ko": [],
        "retry_count": 0,
        "skip_volunteer_agent": False,
        "searched_volunteer_ids": [],
        "recommended_quests": []
    }
    base.update(overrides)
    return base


def patch_critic(report):
    """비평가 LLM 호출 체인을 지정한 보고서로 대체하는 컨텍스트 매니저 헬퍼"""
    patcher = patch(f"{MODULE}.get_openai_model")
    mock_get_openai = patcher.start()

    # 프로덕션은 `validation_prompt | structured_llm` 으로 체인을 조립한 뒤
    # 그 체인을 invoke 한다(validation_agent.py:214).
    # 따라서 with_structured_output 의 반환값은 LangChain Runnable 이어야 한다.
    # MagicMock 을 넣으면 `|` 가 만들어낸 새 체인이 mock.invoke 를 타지 않아
    # 보고서가 전달되지 않고 후보가 전부 사라진다.
    mock_get_openai.return_value.with_structured_output.return_value = RunnableLambda(
        lambda _: report
    )
    return patcher


class TestValidateCandidates(unittest.TestCase):

    def test_volunteer_and_good_deed_both_pass(self):
        """실제 봉사와 AI 선행이 모두 1차 매핑 및 2차 LLM 검수를 통과해야 함"""
        state = build_state(
            retrieved_volunteers=[
                {
                    "id": 1001,
                    "title": "한강 플로깅 쓰레기 수거",
                    "content": "한강 플로깅 쓰레기 수거\n한강 수변 환경 정화 활동",
                    "category": "환경",
                    "location": "서울시 마포구",
                    "url": "https://www.vms.or.kr",
                    "is_volunteer": True
                }
            ],
            ai_good_deeds=[
                {
                    "category_name": "ENVIRONMENT",
                    "quest_title": "텀블러 실천하기",
                    "quest_description": "개인 텀블러 사용",
                    "quest_target": "SOLO",
                    "quest_type": "GOOD_DEED",
                    "location": None,
                    "difficulty": "EASY",
                    "estimated_duration": 15,
                    "recommendation_reason": "환경 보호",
                    "priority_score": 9
                }
            ]
        )

        patcher = patch_critic(DummyReport([
            DummyEvaluation("한강 플로깅 쓰레기 수거", True, "Approved", "승인됨"),
            DummyEvaluation("텀블러 실천하기", True, "Approved", "승인됨")
        ]))
        try:
            result = validate_candidates(state)
        finally:
            patcher.stop()

        candidates = result["candidate_quests"]
        self.assertEqual(len(candidates), 2)
        self.assertEqual(len(result["accumulated_candidates"]), 2)
        self.assertEqual(candidates[0]["quest_type"], "VOLUNTEER")
        self.assertEqual(candidates[1]["quest_type"], "GOOD_DEED")

    def test_volunteer_mapping_uses_actual_keys(self):
        """봉사 데이터의 quest_summary/location 키가 설명과 장소에 정확히 매핑되어야 함"""
        state = build_state(
            retrieved_volunteers=[
                {
                    "id": 514690,
                    "title": "과천종합사회복지관 청소년 성장멘토링 멘토 자원봉사자 모집",
                    "content": "과천종합사회복지관 청소년 성장멘토링 멘토 자원봉사자 모집\n청소년 대상 1:1 학습 지원 멘토를 모집합니다.",
                    # 검증 노드는 content 가 아니라 quest_summary 를 설명으로 쓴다
                    # (validation_agent.py:88). volunteer_agent 도 두 키를 함께 내보낸다.
                    "quest_summary": "청소년 대상 1:1 학습 지원 멘토로 참여합니다.",
                    "category": "아동청소년",
                    "location": "경기 과천시 별양상가1로 10",
                    "url": "https://www.vms.or.kr",
                    "is_volunteer": True
                }
            ]
        )

        patcher = patch_critic(DummyReport([
            DummyEvaluation("과천종합사회복지관 청소년 성장멘토링 멘토 자원봉사자 모집", True, "Approved", "승인됨")
        ]))
        try:
            result = validate_candidates(state)
        finally:
            patcher.stop()

        quest = result["candidate_quests"][0]

        # 설명이 기본값이 아닌 실제 공고 본문이어야 함
        self.assertNotEqual(quest["quest_description"], "지역 봉사활동 참여")
        self.assertIn("청소년 대상 1:1 학습 지원", quest["quest_description"])
        # 요약문 앞에 제목이 중복으로 붙지 않아야 함
        self.assertFalse(quest["quest_description"].startswith(quest["quest_title"]))
        # 장소가 None이 아닌 실제 주소여야 함
        self.assertEqual(quest["location"], "경기 과천시 별양상가1로 10")
        # 추천 사유에 기본 문자열이 아닌 실제 주소가 들어가야 함
        self.assertIn("경기 과천시 별양상가1로 10", quest["recommendation_reason"])

    def test_volunteer_priority_score_follows_search_rank(self):
        """봉사 후보의 priority_score가 하이브리드 검색 순위에 따라 차등 부여되어야 함"""
        volunteers = [
            {"id": i, "title": f"봉사{i}", "content": f"봉사{i}\n내용{i}", "location": f"주소{i}"}
            for i in range(3)
        ]
        state = build_state(retrieved_volunteers=volunteers)

        patcher = patch_critic(DummyReport([
            DummyEvaluation(f"봉사{i}", True, "Approved", "승인됨") for i in range(3)
        ]))
        try:
            result = validate_candidates(state)
        finally:
            patcher.stop()

        scores = [q["priority_score"] for q in result["candidate_quests"]]
        self.assertEqual(scores, [10, 9, 8])

    def test_rejected_quest_records_reasons(self):
        """반려된 후보의 사유가 영문/한글 목록에 각각 수집되어야 함"""
        state = build_state(
            ai_good_deeds=[
                {
                    "category_name": "COMMUNITY",
                    "quest_title": "동네 벽화 그리기",
                    "quest_description": "벽화 그리기",
                    "quest_target": "TEAM",
                    "quest_type": "GOOD_DEED",
                    "location": None,
                    "difficulty": "HARD",
                    "estimated_duration": 180,
                    "recommendation_reason": "테스트",
                    "priority_score": 5
                }
            ]
        )

        patcher = patch_critic(DummyReport([
            DummyEvaluation("동네 벽화 그리기", False, "Too risky", "위험 요소가 있습니다")
        ]))
        try:
            result = validate_candidates(state)
        finally:
            patcher.stop()

        self.assertEqual(result["candidate_quests"], [])
        self.assertEqual(len(result["rejection_reasons_en"]), 1)
        self.assertIn("Too risky", result["rejection_reasons_en"][0])
        self.assertIn("위험 요소가 있습니다", result["rejection_reasons_ko"][0])

    def test_duplicate_title_filtered_by_accumulated(self):
        """이전 회차에 이미 합격한 제목과 중복되는 후보는 1차 검수에서 제외되어야 함"""
        state = build_state(
            accumulated_candidates=[{"quest_title": "텀블러 실천하기", "quest_type": "GOOD_DEED"}],
            ai_good_deeds=[
                {
                    "category_name": "ENVIRONMENT",
                    "quest_title": "텀블러 실천하기",
                    "quest_description": "개인 텀블러 사용",
                    "quest_target": "SOLO",
                    "quest_type": "GOOD_DEED",
                    "location": None,
                    "difficulty": "EASY",
                    "estimated_duration": 15,
                    "recommendation_reason": "환경 보호",
                    "priority_score": 9
                }
            ]
        )

        with patch(f"{MODULE}.get_openai_model") as mock_get_openai:
            result = validate_candidates(state)
            # 1차 검수에서 전부 걸러졌으므로 비평가 LLM은 호출되지 않아야 함
            mock_get_openai.assert_not_called()

        self.assertEqual(result["candidate_quests"], [])


class TestRouteValidation(unittest.TestCase):

    def test_returns_volunteer_when_search_still_possible(self):
        """봉사 데이터가 비었고 재수색 여지가 남아 있으면 봉사 수색 노드로 회귀해야 함"""
        state = build_state(
            retrieved_volunteers=[],
            skip_volunteer_agent=False,
            accumulated_candidates=[{"quest_title": f"Q{i}"} for i in range(3)]
        )
        self.assertEqual(route_validation(state), "volunteer")

    def test_returns_planner_when_volunteer_search_exhausted(self):
        """봉사 수색이 종료된 상태에서 후보가 부족하면 일상 선행 확보를 위해 플래너로 회귀해야 함"""
        state = build_state(
            retrieved_volunteers=[],
            skip_volunteer_agent=True,
            accumulated_candidates=[{"quest_title": f"Q{i}"} for i in range(3)]
        )
        self.assertEqual(route_validation(state), "planner")

    def test_returns_response_when_enough_candidates(self):
        """후보 5개 이상을 확보하면 응답 생성 노드로 이동해야 함"""
        state = build_state(
            retrieved_volunteers=[{"title": "봉사1"}],
            accumulated_candidates=[{"quest_title": f"Q{i}"} for i in range(5)]
        )
        self.assertEqual(route_validation(state), "response")

    def test_enough_candidates_wins_over_empty_volunteers(self):
        """봉사 데이터가 비어 있어도 후보 5개를 확보했다면 재수색 없이 종료해야 함"""
        state = build_state(
            retrieved_volunteers=[],
            skip_volunteer_agent=False,
            accumulated_candidates=[{"quest_title": f"Q{i}"} for i in range(5)]
        )
        self.assertEqual(route_validation(state), "response")

    def test_returns_response_when_max_retries_reached(self):
        """재시도 횟수를 초과하면 후보가 부족해도 강제로 응답 생성 노드로 이동해야 함"""
        state = build_state(
            retrieved_volunteers=[{"title": "봉사1"}],
            accumulated_candidates=[{"quest_title": "Q1"}],
            retry_count=2
        )
        self.assertEqual(route_validation(state), "response")

    def test_returns_planner_when_candidates_insufficient(self):
        """봉사는 있으나 후보가 부족하고 재시도 여유가 있으면 플래너로 회귀해야 함"""
        state = build_state(
            retrieved_volunteers=[{"title": "봉사1"}],
            accumulated_candidates=[{"quest_title": "Q1"}],
            retry_count=0
        )
        self.assertEqual(route_validation(state), "planner")


if __name__ == "__main__":
    unittest.main()