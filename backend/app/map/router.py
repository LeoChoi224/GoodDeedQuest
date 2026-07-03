from fastapi import APIRouter, Depends, Query
from typing import List
from pydantic import BaseModel
from backend.app.common.response import APIResponse
from backend.app.common.auth import get_current_user

router = APIRouter(prefix="/map", tags=["Map Quests"])

class MapQuestSchema(BaseModel):
    id: int
    title: str
    lat: float
    lng: float
    address: str
    xp_reward: int

MOCK_LOCATIONS = [
    {"id": 1, "title": "플로깅(조깅하며 쓰레기 줍기)", "lat": 37.5562, "lng": 126.9223, "address": "서울시 마포구 신촌로 160", "xp_reward": 50},
    {"id": 2, "title": "동네 쓰레기 분리수거함 청소", "lat": 37.5585, "lng": 126.9255, "address": "서울시 마포구 창전동 12", "xp_reward": 70},
    {"id": 3, "title": "교통약자 도우미 활동", "lat": 37.5540, "lng": 126.9201, "address": "신촌역 7번 출구", "xp_reward": 100}
]

@router.get("/quests", response_model=APIResponse[List[MapQuestSchema]])
def get_nearby_quests(
    lat: float = Query(..., description="위도 (Latitude)"),
    lng: float = Query(..., description="경도 (Longitude)"),
    radius_meters: int = Query(1000, description="반경 (미터 단위)"),
    user: dict = Depends(get_current_user)
):
    """현재 사용자의 위경도 좌표를 기준으로 반경 내의 선행 퀘스트 지점 목록을 반환합니다."""
    # 실제 프로덕션에서는 spatial query나 DB Geolocation 함수 이용
    return APIResponse.ok(data=MOCK_LOCATIONS, message=f"반경 {radius_meters}m 내의 주변 퀘스트 검색 성공")
