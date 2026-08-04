import unittest
from unittest.mock import patch, MagicMock

from ai.app.quest_recommend.nodes.volunteer_agent import (
    retrieve_volunteers,
    VOLUNTEER_FETCH_LIMIT,
)

MODULE = "ai.app.quest_recommend.nodes.volunteer_agent"


def make_docs(count: int, start_id: int = 1):
    """DB에서 픽업된 봉사 공고 딕셔너리 목록을 생성하는 테스트 헬퍼"""
    return [
        {
            "id": start_id + i,
            "title": f"봉사공고{start_id + i}",
            "content": f"봉사공고{start_id + i}\n활동 상세 내용",
            "category": "지역사회",
            "location": f"서울시 테스트구 {start_id + i}",
            "url": "https://www.vms.or.kr",
            "is_volunteer": True,
            "vector": [0.1, 0.2, 0.3],
        }
        for i in range(count)
    ]


def build_state(**overrides):
    """봉사 수색 노드 테스트용 기본 State를 구성하고 필요한 값만 덮어쓰는 헬퍼"""
    base = {
        "recommendation_strategy": {"search_query": "지역사회 봉사"},
        "user_profile": {
            "latitude": 37.402,
            "longitude": 126.97669,
            "interests": ["COMMUNITY"],
        },
        "retrieved_volunteers": [],
        "searched_volunteer_ids": [],
    }
    base.update(overrides)
    return base


class TestRetrieveVolunteers(unittest.TestCase):

    def setUp(self):
        """DB 세션, 벡터 어댑터, DB 조회 함수를 매 테스트마다 격리하여 모킹"""
        self.session_patcher = patch(f"{MODULE}.SessionLocal")
        self.adapter_patcher = patch(f"{MODULE}.get_vector_store_adapter")
        self.loader_patcher = patch(f"{MODULE}.load_volunteer_centers_from_db")

        self.mock_session = self.session_patcher.start()
        self.mock_get_adapter = self.adapter_patcher.start()
        self.mock_loader = self.loader_patcher.start()

        self.mock_adapter = MagicMock()
        self.mock_get_adapter.return_value = self.mock_adapter

    def tearDown(self):
        self.session_patcher.stop()
        self.adapter_patcher.stop()
        self.loader_patcher.stop()

    def test_skip_flag_true_when_no_documents(self):
        """반경 내 신규 공고가 0건이면 재수색을 종료하도록 skip_volunteer_agent가 True여야 함"""
        self.mock_loader.return_value = []

        result = retrieve_volunteers(build_state())

        self.assertEqual(result["retrieved_volunteers"], [])
        self.assertTrue(result["skip_volunteer_agent"])
        # 공고가 없으므로 하이브리드 수색은 호출되지 않아야 함
        self.mock_adapter.hybrid_search.assert_not_called()

    def test_skip_flag_true_when_fetch_below_limit(self):
        """조회량이 상한 미만이면 반경 내 공고를 모두 소진한 것으로 보고 재수색을 종료해야 함"""
        docs = make_docs(2)
        self.mock_loader.return_value = docs
        self.mock_adapter.hybrid_search.return_value = docs

        result = retrieve_volunteers(build_state())

        self.assertEqual(len(result["retrieved_volunteers"]), 2)
        self.assertTrue(result["skip_volunteer_agent"])

    def test_skip_flag_false_when_fetch_reaches_limit(self):
        """조회량이 상한에 도달하면 아직 남은 공고가 있을 수 있으므로 재수색 여지를 남겨야 함"""
        docs = make_docs(VOLUNTEER_FETCH_LIMIT)
        self.mock_loader.return_value = docs
        self.mock_adapter.hybrid_search.return_value = docs[:5]

        result = retrieve_volunteers(build_state())

        self.assertEqual(len(result["retrieved_volunteers"]), 5)
        self.assertFalse(result["skip_volunteer_agent"])

    def test_skip_flag_true_when_hybrid_search_returns_nothing(self):
        """공고는 있으나 하이브리드 수색이 끝내 0건이면 무한 재수색을 막기 위해 종료해야 함"""
        self.mock_loader.return_value = make_docs(VOLUNTEER_FETCH_LIMIT)
        # 1차 수색과 관심사 기반 2차 수색 모두 0건
        self.mock_adapter.hybrid_search.return_value = []

        result = retrieve_volunteers(build_state())

        self.assertEqual(result["retrieved_volunteers"], [])
        self.assertTrue(result["skip_volunteer_agent"])
        self.assertEqual(self.mock_adapter.hybrid_search.call_count, 2)

    def test_searched_ids_accumulate_across_rounds(self):
        """이번 회차에 조회한 공고 아이디가 기존 누적 목록에 더해져 반환되어야 함"""
        self.mock_loader.return_value = make_docs(3, start_id=11)
        self.mock_adapter.hybrid_search.return_value = make_docs(3, start_id=11)

        state = build_state(searched_volunteer_ids=[1, 2, 3])
        result = retrieve_volunteers(state)

        self.assertEqual(result["searched_volunteer_ids"], [1, 2, 3, 11, 12, 13])

    def test_previous_ids_passed_as_exclude_ids(self):
        """누적 조회 이력이 DB 조회의 제외 목록(exclude_ids)으로 그대로 전달되어야 함"""
        self.mock_loader.return_value = make_docs(2, start_id=21)
        self.mock_adapter.hybrid_search.return_value = make_docs(2, start_id=21)

        retrieve_volunteers(build_state(searched_volunteer_ids=[7, 8]))

        _, kwargs = self.mock_loader.call_args
        self.assertEqual(kwargs["exclude_ids"], [7, 8])

    def test_fallback_search_uses_interest_keyword(self):
        """1차 수색이 0건이면 사용자 관심사 첫 항목으로 2차 수색을 수행해야 함"""
        self.mock_loader.return_value = make_docs(2)
        self.mock_adapter.hybrid_search.side_effect = [[], make_docs(1)]

        result = retrieve_volunteers(build_state())

        second_call_kwargs = self.mock_adapter.hybrid_search.call_args_list[1][1]
        self.assertEqual(second_call_kwargs["query"], "COMMUNITY")
        self.assertEqual(len(result["retrieved_volunteers"]), 1)

    def test_blank_search_query_falls_back_to_default(self):
        """검색 쿼리가 공백이거나 비어 있으면 기본 키워드 'volunteer'로 대체되어야 함"""
        self.mock_loader.return_value = make_docs(2)
        self.mock_adapter.hybrid_search.return_value = make_docs(2)

        state = build_state(recommendation_strategy={"search_query": "   "})
        retrieve_volunteers(state)

        first_call_kwargs = self.mock_adapter.hybrid_search.call_args_list[0][1]
        self.assertEqual(first_call_kwargs["query"], "volunteer")

    def test_missing_coordinates_do_not_crash(self):
        """사용자 좌표가 없어도 예외 없이 빈 결과와 종료 플래그를 반환해야 함"""
        self.mock_loader.return_value = []

        state = build_state(user_profile={"latitude": None, "longitude": None, "interests": []})
        result = retrieve_volunteers(state)

        self.assertEqual(result["retrieved_volunteers"], [])
        self.assertTrue(result["skip_volunteer_agent"])


if __name__ == "__main__":
    unittest.main()