from fastapi import APIRouter, Depends, Query
from typing import List
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.common.database import get_db
from backend.app.common.response import APIResponse
from backend.app.common.auth import get_current_user
from backend.app.map.models import VolunteerCenter, Region, Competition, CompetitionParticipant, CompetitionContribution, City
from backend.app.auth.models import User
from backend.app.map.schemas import VolunteerCenterResponse
from backend.app.map.enums import CompetitionStatus
from backend.app.map.ai_client import VolCategoryCommentAIClient, VolCategoryCommentClientError


router = APIRouter(prefix="/map", tags=["Map Quests"])

# ai/app/vol_category/classify.py의 CATEGORIES 키와 동일하게 유지 (실제 배정 가능한 카테고리 목록, '기타' 제외)
ALL_VOLUNTEER_CATEGORIES = ["환경", "동물", "아동청소년", "어르신", "장애인", "교육", "다문화", "재난안전", "지역사회"]


class TeamSelectRequest(BaseModel):
    region_id: int


def _get_current_competition(db: Session, include_settling: bool = False) -> Competition | None:
    """진행 중(IN_PROGRESS)인 대회 조회. include_settling=True면 정산 중(SETTLING)까지 포함해서
    조회용(랭킹 화면)에서 재사용 - 매주 월~토 진행, 일요일 정산이라는 사이클 기준.
    쓰기 작업(team-select, 참여 자동 이월)은 항상 include_settling=False로 IN_PROGRESS만 써야 함."""
    statuses = [CompetitionStatus.IN_PROGRESS]
    if include_settling:
        statuses.append(CompetitionStatus.SETTLING)
    return (
        db.query(Competition)
        .filter(Competition.status.in_(statuses))
        .order_by(Competition.start_at.desc())
        .first()
    )


def _ensure_participant(db: Session, competition_id: int, region_id: int) -> None:
    """해당 대회에 이 지역 참여 row가 없으면 새로 생성(점수 0부터 시작).
    매주 새 대회가 시작될 때, 이미 지역을 설정해둔 유저가 /main에 들어오기만 해도
    자동으로 참여가 이어지도록 하기 위한 헬퍼 - team-select에서도 동일하게 재사용."""
    exists = (
        db.query(CompetitionParticipant)
        .filter(
            CompetitionParticipant.competition_id == competition_id,
            CompetitionParticipant.region_id == region_id,
        )
        .first()
    )
    if exists is None:
        db.add(CompetitionParticipant(competition_id=competition_id, region_id=region_id, score=0))
        db.commit()


def initialize_all_participants(db: Session, competition_id: int) -> None:
    """새 대회 시작 시 전국 모든 시군구(Region)를 참여 지역으로 점수 0부터 일괄 등록.
    공공데이터포털 기준으로 전 시군구를 이미 Region 테이블에 등록해뒀고, 대회 참여 대상도
    전 지역이라 이전 대회 참여 이력과 무관하게 매번 전체로 새로 시작하면 됨.
    새 대회를 만드는 시점(관리자/스케줄러)에서 호출해야 함 - 대회 생성 로직 자체가
    아직 없어서(팀 확인 필요) 여기 함수만 준비해두고, 만들어지면 그 코드에서 호출하면 됨."""
    all_region_ids = db.query(Region.region_id).all()
    for (region_id,) in all_region_ids:
        _ensure_participant(db, competition_id, region_id)


@router.get("/main")
def get_map_main(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """지도메인 - 참여지역 설정여부 확인 + 매주 참여 자동 이월"""
    db_user = db.query(User).filter(User.user_id == user["id"]).first()

    if db_user is None or db_user.region_id is None:
        # 참여 지역 미설정 -> 팀 설정하기 버튼 활성화
        return APIResponse.ok(data={"has_region": False, "region": None})

    region = db.query(Region).filter(Region.region_id == db_user.region_id).first()

    # 매주 자동 참여 이월: 새 대회(IN_PROGRESS)가 시작됐는데 이번 대회엔 아직 참여 row가 없으면
    # 여기서 자동 생성 - 유저가 팀을 따로 다시 선택할 필요 없이 이어짐
    competition = _get_current_competition(db, include_settling=False)
    if competition is not None:
        _ensure_participant(db, competition.competition_id, db_user.region_id)

    return APIResponse.ok(data={
        "has_region": True,
        "region": {
            "region_id": region.region_id,
            "region_name": region.region_name,
            # 프론트가 시/도 SVG 표시명(강원/전북 개명 이슈 흡수용 매핑)을 역산할 때 필요
            "city_id": region.city_id,
        },
    })


@router.get("/cities/{city_id}/regions")
def get_regions_by_city(
    city_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """참여 지역 선택 팝업(TeamSelectPopup) - 시/도 선택 시 하위 시군구 목록 조회용.
    대회/랭킹과 무관한 순수 조회라 대회 존재 여부와 상관없이 항상 응답함."""
    regions = (
        db.query(Region)
        .filter(Region.city_id == city_id)
        .order_by(Region.region_name)
        .all()
    )
    return APIResponse.ok(data=[
        {"region_id": r.region_id, "region_name": r.region_name} for r in regions
    ])


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
    """대항전전국지도 - 시/도별 순위 (시군구 점수 합산). 정산 중(토요일까지 결과 고정)에도 조회 가능"""
    competition = _get_current_competition(db, include_settling=True)
    if competition is None:
        return APIResponse.fail(message="진행 중이거나 정산 중인 대항전이 없습니다")

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
    """시군구 랭킹페이지 - 특정 시/도 하위 시군구 순위. 정산 중(토요일까지 결과 고정)에도 조회 가능"""
    competition = _get_current_competition(db, include_settling=True)
    if competition is None:
        return APIResponse.fail(message="진행 중이거나 정산 중인 대항전이 없습니다")

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


@router.get("/region-ranking/{region_id}")
def get_region_detail_ranking(
    region_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """시군구별 상세 랭킹페이지 - 개인 랭킹 + AI 부족봉사 추천(ai_category 기반 실집계).
    부족한 카테고리는 '이 지역'을 기준으로 판단하지만, 추천 시설은 그 카테고리가 부족한 바로 이 지역이 아니라
    '다른 지역'에서 찾아서 보여줌 (같은 지역에서 찾으면 애초에 부족하다고 판단된 카테고리라 항상 텅 비거나
    의미 없는 결과가 나오기 때문 - "우리 동네엔 없지만 다른 동네엔 이런 봉사가 있다"는 참고용 추천).
    정산 중에도 조회 가능"""
    competition = _get_current_competition(db, include_settling=True)
    if competition is None:
        return APIResponse.fail(message="진행 중이거나 정산 중인 대항전이 없습니다")

    region = db.query(Region).filter(Region.region_id == region_id).first()
    if region is None:
        return APIResponse.fail(message="존재하지 않는 지역입니다")

    # 개인 랭킹 - CompetitionContribution(퀘스트 인증 건별 기여) 합산
    personal_results = (
        db.query(
            User.user_id,
            User.nickname,
            func.coalesce(func.sum(CompetitionContribution.points), 0).label("total_points"),
        )
        .join(CompetitionContribution, CompetitionContribution.user_id == User.user_id)
        .filter(
            CompetitionContribution.competition_id == competition.competition_id,
            CompetitionContribution.region_id == region_id,
        )
        .group_by(User.user_id, User.nickname)
        .order_by(func.sum(CompetitionContribution.points).desc())
        .all()
    )

    personal_ranking = [
        {"rank": idx + 1, "user_id": r.user_id, "nickname": r.nickname, "score": r.total_points}
        for idx, r in enumerate(personal_results)
    ]

    # AI 부족봉사 판단 - VolunteerCenter.ai_category(임베딩+키워드 기반 사전 분류, ai/app/vol_category 배치)로 집계.
    # 지역에 존재하는 카테고리뿐 아니라 아예 0건인 카테고리도 "부족"으로 잡히도록 전체 카테고리 목록 기준으로 채움.
    raw_counts = dict(
        db.query(VolunteerCenter.ai_category, func.count(VolunteerCenter.center_id))
        .filter(VolunteerCenter.region_id == region_id, VolunteerCenter.ai_category.isnot(None))
        .group_by(VolunteerCenter.ai_category)
        .all()
    )
    category_counts = {cat: raw_counts.get(cat, 0) for cat in ALL_VOLUNTEER_CATEGORIES}
    lacking_category = min(category_counts, key=category_counts.get)

    # 추천은 '다른 지역'에서 같은 카테고리 시설을 찾음 (이유는 위 docstring 참고)
    # 안내 문구에 지역명을 넣기 위해 Region을 조인해서 region_name도 함께 가져옴
    recommended = (
        db.query(VolunteerCenter, Region.region_name)
        .join(Region, Region.region_id == VolunteerCenter.region_id)
        .filter(
            VolunteerCenter.ai_category == lacking_category,
            VolunteerCenter.region_id != region_id,
        )
        .limit(3)
        .all()
    )

    recommended_facilities = [
        {
            "center_id": f.center_id,
            "vol_name": f.vol_name,
            "ai_category": f.ai_category,
            "region_id": f.region_id,
            "region_name": facility_region_name,
        }
        for f, facility_region_name in recommended
    ]

    # LLM 자연어 안내 문구 생성 - AI 서버 호출 실패 시에도 region-ranking API 전체가 죽으면 안 되므로
    # 규칙 기반 문구로 대체하고 계속 진행 (개인 랭킹 등 핵심 데이터는 이 문구와 무관하게 항상 반환되어야 함)
    try:
        lacking_category_comment = VolCategoryCommentAIClient().request_comment(
            payload={
                "region_name": region.region_name,
                "lacking_category": lacking_category,
                "recommended_facilities": [
                    {"vol_name": rf["vol_name"], "region_name": rf["region_name"]}
                    for rf in recommended_facilities
                ],
            }
        )
    except VolCategoryCommentClientError:
        lacking_category_comment = (
            f"{region.region_name}은(는) 다른 지역에 비해 '{lacking_category}' 관련 봉사가 부족해요."
        )

    return APIResponse.ok(data={
        "region_id": region_id,
        "region_name": region.region_name,
        "competition_id": competition.competition_id,
        "personal_ranking": personal_ranking,
        "lacking_category": lacking_category,
        "lacking_category_comment": lacking_category_comment,
        "recommended_facilities": recommended_facilities,
    })


@router.post("/team-select")
def select_competition_team(
    payload: TeamSelectRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """대항전 팀선택 페이지 - 참여 지역 등록/변경 (쓰기 작업).
    최초 선택(아직 region_id 없는 유저)은 언제든 허용.
    이미 지역이 있는 유저의 "변경"은 정산 중(SETTLING)에만 허용 - 진행 중에 바꾸면
    같은 대회 안에서 기여(CompetitionContribution)가 옛 지역/새 지역으로 쪼개지는 문제 방지."""
    db_user = db.query(User).filter(User.user_id == user["id"]).first()
    if db_user is None:
        return APIResponse.fail(message="사용자를 찾을 수 없습니다")

    is_first_selection = db_user.region_id is None

    if is_first_selection:
        competition = _get_current_competition(db, include_settling=True)
    else:
        competition = (
            db.query(Competition)
            .filter(Competition.status == CompetitionStatus.SETTLING)
            .order_by(Competition.start_at.desc())
            .first()
        )
        if competition is None:
            return APIResponse.fail(message="팀 변경은 정산 중(다음 대회 준비 기간)에만 가능합니다")

    if competition is None:
        return APIResponse.fail(message="진행 중이거나 정산 중인 대항전이 없습니다")

    region = db.query(Region).filter(Region.region_id == payload.region_id).first()
    if region is None:
        return APIResponse.fail(message="존재하지 않는 지역입니다")

    db_user.region_id = payload.region_id
    db.commit()

    # 지금 대회가 IN_PROGRESS(최초 선택인 경우만 가능)일 때만 바로 참여 row 등록.
    # SETTLING 중 변경은 참여 row를 만들지 않음 - 다음 주 새 대회가 IN_PROGRESS로 시작될 때
    # /main의 자동 이월(_ensure_participant) 또는 carry_forward_participants가 처리함.
    if competition.status == CompetitionStatus.IN_PROGRESS:
        _ensure_participant(db, competition.competition_id, payload.region_id)

    db.refresh(db_user)

    return APIResponse.ok(
        data={
            "region_id": db_user.region_id,
            "region_name": region.region_name,
            "competition_id": competition.competition_id,
        },
        message="참여 지역이 설정되었습니다",
    )