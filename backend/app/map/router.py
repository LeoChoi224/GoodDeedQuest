from fastapi import APIRouter, Depends, Query
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.common.database import get_db
from backend.app.common.response import APIResponse
from backend.app.common.auth import get_current_user
from backend.app.map.models import VolunteerCenter, Region, Competition, CompetitionParticipant, City
from backend.app.auth.models import User
from backend.app.map.schemas import VolunteerCenterResponse
from backend.app.map.enums import CompetitionStatus


router = APIRouter(prefix="/map", tags=["Map Quests"])


@router.get("/main")
def get_map_main(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """지도메인 - 참여지역 설정여부 확인"""
    db_user = db.query(User).filter(User.user_id == user["id"]).first()

    if db_user is None or db_user.region_id is None:
        # 참여 지역 미설정 -> 팀 설정하기 버튼 활성화
        return APIResponse.ok(data={"has_region": False, "region": None})

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


@router.get("/national-ranking")
def get_national_ranking(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """대항전전국지도 - 시/도별 순위 (시군구 점수 합산)"""
    competition = (
        db.query(Competition)
        .filter(Competition.status == CompetitionStatus.IN_PROGRESS)
        .first()
    )
    if competition is None:
        return APIResponse.fail(message="진행 중인 대항전이 없습니다")

    results = (
        db.query(
            City.city_id,
            City.city_name,
            func.coalesce(func.sum(CompetitionParticipant.score), 0).label("total_score"),
        )
        .join(Region, Region.city_id == City.city_id)
        .join(CompetitionParticipant, CompetitionParticipant.region_id == Region.region_id)
        .filter(CompetitionParticipant.competition_id == competition.competition_id)
        .group_by(City.city_id, City.city_name)
        .order_by(func.sum(CompetitionParticipant.score).desc())
        .all()
    )

    ranking = [
        {"rank": idx + 1, "city_id": r.city_id, "city_name": r.city_name, "total_score": r.total_score}
        for idx, r in enumerate(results)
    ]
    return APIResponse.ok(data={"competition_id": competition.competition_id, "ranking": ranking})


@router.get("/city-ranking/{city_id}")
def get_city_ranking(
    city_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """시군구 랭킹페이지 - 특정 시/도 하위 시군구 순위"""
    competition = (
        db.query(Competition)
        .filter(Competition.status == CompetitionStatus.IN_PROGRESS)
        .first()
    )
    if competition is None:
        return APIResponse.fail(message="진행 중인 대항전이 없습니다")

    results = (
        db.query(Region.region_id, Region.region_name, CompetitionParticipant.score)
        .join(CompetitionParticipant, CompetitionParticipant.region_id == Region.region_id)
        .filter(
            Region.city_id == city_id,
            CompetitionParticipant.competition_id == competition.competition_id,
        )
        .order_by(CompetitionParticipant.score.desc())
        .all()
    )

    ranking = [
        {"rank": idx + 1, "region_id": r.region_id, "region_name": r.region_name, "score": r.score or 0}
        for idx, r in enumerate(results)
    ]
    return APIResponse.ok(data={"city_id": city_id, "competition_id": competition.competition_id, "ranking": ranking})