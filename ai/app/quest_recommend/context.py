from datetime import datetime
from typing import Dict, Any
import httpx
import logging

from ai.app.quest_recommend.state import RecommendState

logger = logging.getLogger(__name__)

# Open-Meteo API 호출(위도, 경도로 실시간 날씨 정보를 가져옴)
def get_weather(latitude, longitude):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current_weather=true"
    response = httpx.get(url, timeout=3.0)
    
    if response.status_code == 200:
        return response.json()

def analyze_context(state: RecommendState) -> Dict[str, Any]:
    """
    현재 시간, 요일, 날씨 및 위치 정보를 바탕으로
    주변 상황 컨텍스트(context)를 생성하는 LangGraph 노드 함수입니다.
    """
    # TODO Geolocation API 연동 시 아래 주석해제
    latitude = 37.49946184056819
    longitude = 127.03589438761209
    # latitude = state.get("latitude")
    # longitude = state.get("longitude")

    now = datetime.now()
    weekday = now.weekday()

    if weekday in [5, 6]:
        is_weekend = True 
        day_of_week_type = "주말"
    else:
        is_weekend = False
        day_of_week_type = "평일"

    today_weather = "맑음"
    try:
        current_weather = get_weather(latitude, longitude).get("current_weather", {})
        weather_code = current_weather.get("weathercode", 0)
            
        match weather_code:
            case code if code in [0, 1, 2, 3]:
                today_weather = "맑음"
            case code if code in [51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82]:
                today_weather = "비"
            case code if code in [71, 73, 75, 77, 85, 86]:
                today_weather = "눈"
            case _:
                today_weather = "흐림"
    except Exception as e:
        logger.warning(f"Failed to fetch real-time weather: {e}. Fallback to '맑음'.")
    
    is_outdoor_feasible = False if today_weather in ["비", "눈"] else True

    return {"context": {
        "current_date": str(now.date()),
        "day_of_week_type": day_of_week_type,
        "is_weekend": is_weekend,
        "today_weather": today_weather,
        "is_outdoor_feasible": is_outdoor_feasible
    }}