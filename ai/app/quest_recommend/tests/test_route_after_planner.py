import unittest

from ai.app.quest_recommend.nodes.planner_agent import route_after_planner

# 그래프에 등록된 병렬 실행 대상 노드명 (graph.py의 add_conditional_edges 경로 목록과 일치해야 함)
PARALLEL_NODES = {"volunteer", "good_deed"}


class TestRouteAfterPlanner(unittest.TestCase):
    """
    Planner 수립 직후 어떤 노드를 병렬 실행할지 결정하는 라우터 함수 검증.
    봉사 수색이 종료된 상태(skip_volunteer_agent=True)에서는 결과가 동일할 것이 확실한
    봉사 수색을 건너뛰어야 하며, 그 외에는 항상 두 노드를 함께 실행해야 합니다.
    """

    def test_runs_both_nodes_when_flag_is_false(self):
        """봉사 수색이 아직 종료되지 않았다면 봉사와 일상 선행을 병렬 실행해야 함"""
        result = route_after_planner({"skip_volunteer_agent": False})

        self.assertEqual(result, ["volunteer", "good_deed"])

    def test_runs_both_nodes_when_flag_is_absent(self):
        """플래그가 아직 State에 없는 최초 실행에서도 기본값으로 두 노드를 모두 실행해야 함"""
        result = route_after_planner({})

        self.assertEqual(result, ["volunteer", "good_deed"])

    def test_skips_volunteer_when_search_exhausted(self):
        """봉사 수색이 종료된 경우 봉사 노드를 건너뛰고 일상 선행만 실행해야 함"""
        result = route_after_planner({"skip_volunteer_agent": True})

        self.assertEqual(result, ["good_deed"])
        self.assertNotIn("volunteer", result)

    def test_good_deed_always_runs(self):
        """어떤 상태에서도 일상 선행 생성은 반드시 실행되어야 함 (5개 확보의 유일한 수단)"""
        for flag in (True, False):
            with self.subTest(skip_volunteer_agent=flag):
                self.assertIn("good_deed", route_after_planner({"skip_volunteer_agent": flag}))

    def test_never_returns_empty_list(self):
        """빈 리스트를 반환하면 후속 노드가 하나도 예약되지 않아 그래프가 멈추므로 항상 1개 이상이어야 함"""
        for state in ({}, {"skip_volunteer_agent": True}, {"skip_volunteer_agent": False}):
            with self.subTest(state=state):
                self.assertTrue(route_after_planner(state))

    def test_returns_list_type(self):
        """LangGraph의 병렬 팬아웃 규약상 반환값은 노드명 문자열의 리스트여야 함"""
        result = route_after_planner({"skip_volunteer_agent": False})

        self.assertIsInstance(result, list)
        self.assertTrue(all(isinstance(node, str) for node in result))

    def test_returns_only_registered_node_names(self):
        """그래프에 등록되지 않은 노드명을 반환하면 실행 시점에 라우팅 오류가 발생하므로 검증"""
        for state in ({}, {"skip_volunteer_agent": True}, {"skip_volunteer_agent": False}):
            with self.subTest(state=state):
                self.assertTrue(set(route_after_planner(state)).issubset(PARALLEL_NODES))

    def test_ignores_unrelated_state_values(self):
        """분기 판단은 skip_volunteer_agent만 보고, 다른 State 값에는 영향을 받지 않아야 함"""
        state = {
            "skip_volunteer_agent": True,
            "retry_count": 2,
            "retrieved_volunteers": [{"id": 1, "title": "봉사1"}],
            "accumulated_candidates": [{"quest_title": "Q1"}],
            "searched_volunteer_ids": [1, 2, 3],
        }

        self.assertEqual(route_after_planner(state), ["good_deed"])


if __name__ == "__main__":
    unittest.main()