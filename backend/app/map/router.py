from fastapi import APIRouter, Depends, Query
from typing import List
from sqlalchemy.orm import Session
from backend.app.common.database import get_db
from backend.app.common.response import APIResponse
from backend.app.common.auth import get_current_user
from backend.app.map.models import VolunteerCenter, Region
from backend.app.auth.models import User
from backend.app.map.schemas import VolunteerCenterResponse

router = APIRouter(prefix="/map", tags=["Map Quests"])

@router.get("/main")
def get_map_main(
    db: Session = Depends(get_db),
    user: dict =  Depends(get_current_user),
):
    """지도메인 - 참여지역 설정여부 확인"""
    db_user = db.query(User).filter(User.user_id == user["id"]).first()

    if db_user is None or db_user.region_id is None:
        # 참여 지역 미설정 -> 팀 설정하기 버튼 활성화
        return APIResponse.ok(data={"has_region": False, "region":None})
    
    region = db.query(Region).filter(Region.region_id == db_user.region_id).first()
    return APIResponse.ok(data={"has_region": True, "region": {"region_id": region.region_id, "region_name": region.region_name}})
    
    


@router.get("/volunteer-centers", response_model=APIResponse[List[VolunteerCenterResponse]])
def get_nearby_volunteer_centers(
    lat: float = Query(..., description="내 위치 위도"),
    lng: float = Query(..., description="내 위치 경도"),
    radius_km: float = Query(3.0, description="반경(km)"),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """내 주변 둘러보기 - 반경 내 봉사센터 목록 조회"""
    delta = radius_km / 111  # 위경도 1도 ≈ 111km 근사

    centers = (
        db.query(VolunteerCenter)
        .filter(
            VolunteerCenter.latitude.isnot(None),
            VolunteerCenter.longitude.isnot(None),
            VolunteerCenter.latitude.between(lat - delta, lat + delta),
            VolunteerCenter.longitude.between(lng - delta, lng + delta),
        )
        .all()
    )

    return APIResponse.ok(data=centers, message=f"반경 {radius_km}km 내 봉사센터 조회 성공")