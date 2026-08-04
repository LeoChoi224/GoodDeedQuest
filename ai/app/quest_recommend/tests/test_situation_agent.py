from unittest.mock import patch, MagicMock

from ai.app.quest_recommend.nodes.situation_agent import (
    analyze_situation,
    WEATHER_API_TIMEOUT_SECONDS,
)


def build_state(latitude=None, longitude=None):
    """날씨 분석에 필요한 최소 State를 구성하는 테스트 헬퍼"""
    return {
        "user_id": 1,
        "latitude": latitude,
        "longitude": longitude,
        "user_profile": {}
    }


def build_weather_response(payload, status_code=200):
    """httpx.get의 반환값을 흉내내는 Mock 응답 객체를 생성하는 테스트 헬퍼"""
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.json.return_value = payload
    return mock_response


def test_analyze_situation_without_coordinates():
    """좌표가 없으면 날씨 API를 부르지 않고 맑음으로 진행한다"""
    result = analyze_situation(build_state())
    context = result.get("situation_context", {})

    assert context.get("today_weather") == "sunny"
    assert context.get("is_outdoor_feasible") is True
    assert "current_date" in context
    assert "day_of_week_type" in context


@patch("ai.app.quest_recommend.nodes.situation_agent.httpx.get")
def test_analyze_situation_rainy_weather(mock_get):
    """비(weathercode 61) 응답이면 야외 활동 불가로 판정한다"""
    mock_get.return_value = build_weather_response({"current_weather": {"weathercode": 61}})

    result = analyze_situation(build_state(37.5665, 126.9780))
    context = result.get("situation_context", {})

    assert context.get("today_weather") == "rainy"
    assert context.get("is_outdoor_feasible") is False


@patch("ai.app.quest_recommend.nodes.situation_agent.httpx.get")
def test_analyze_situation_snowy_weather(mock_get):
    """눈(weathercode 73) 응답이면 야외 활동 불가로 판정한다"""
    mock_get.return_value = build_weather_response({"current_weather": {"weathercode": 73}})

    result = analyze_situation(build_state(37.5665, 126.9780))
    context = result.get("situation_context", {})

    assert context.get("today_weather") == "snowy"
    assert context.get("is_outdoor_feasible") is False


@patch("ai.app.quest_recommend.nodes.situation_agent.httpx.get")
def test_analyze_situation_api_fallback_on_exception(mock_get):
    """통신 예외가 나도 노드는 죽지 않고 맑음으로 폴백한다"""
    mock_get.side_effect = Exception("Connection Timeout")

    result = analyze_situation(build_state(37.5665, 126.9780))
    context = result.get("situation_context", {})

    assert context.get("today_weather") == "sunny"
    assert context.get("is_outdoor_feasible") is True


@patch("ai.app.quest_recommend.nodes.situation_agent.httpx.get")
def test_analyze_situation_fallback_on_http_error(mock_get):
    """200이 아닌 응답이면 맑음으로 폴백한다"""
    mock_get.return_value = build_weather_response({}, status_code=500)

    result = analyze_situation(build_state(37.5665, 126.9780))
    context = result.get("situation_context", {})

    assert context.get("today_weather") == "sunny"


@patch("ai.app.quest_recommend.nodes.situation_agent.httpx.get")
def test_analyze_situation_null_weathercode_falls_back_to_sunny(mock_get):
    """
    weathercode가 null로 오면 흐림이 아니라 맑음이어야 한다.
    .get의 기본값은 키가 없을 때만 쓰이므로, None을 걸러내지 않으면 case _ 로 빠져 cloudy가 된다.
    """
    mock_get.return_value = build_weather_response({"current_weather": {"weathercode": None}})

    result = analyze_situation(build_state(37.5665, 126.9780))
    context = result.get("situation_context", {})

    assert context.get("today_weather") == "sunny"
    assert context.get("is_outdoor_feasible") is True


@patch("ai.app.quest_recommend.nodes.situation_agent.httpx.get")
def test_analyze_situation_missing_current_weather_falls_back_to_sunny(mock_get):
    """current_weather 키 자체가 없어도 맑음으로 폴백한다"""
    mock_get.return_value = build_weather_response({"latitude": 37.5, "longitude": 127.0})

    result = analyze_situation(build_state(37.5665, 126.9780))
    context = result.get("situation_context", {})

    assert context.get("today_weather") == "sunny"


@patch("ai.app.quest_recommend.nodes.situation_agent.httpx.get")
def test_analyze_situation_non_dict_response_falls_back_to_sunny(mock_get):
    """응답 본문이 dict가 아니어도 AttributeError 없이 맑음으로 폴백한다"""
    mock_get.return_value = build_weather_response([{"weathercode": 61}])

    result = analyze_situation(build_state(37.5665, 126.9780))
    context = result.get("situation_context", {})

    assert context.get("today_weather") == "sunny"


@patch("ai.app.quest_recommend.nodes.situation_agent.httpx.get")
def test_weather_api_called_with_configured_timeout(mock_get):
    """날씨 API 호출에 설정된 타임아웃 상수가 그대로 적용되는지 확인한다"""
    mock_get.return_value = build_weather_response({"current_weather": {"weathercode": 0}})

    analyze_situation(build_state(37.5665, 126.9780))

    _, kwargs = mock_get.call_args
    assert kwargs.get("timeout") == WEATHER_API_TIMEOUT_SECONDS