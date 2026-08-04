from pydantic import BaseModel, ConfigDict, field_serializer
from typing import Optional
from datetime import datetime
from decimal import Decimal
from backend.app.map.enums import CompetitionStatus




# 공통 datetime(Timestamp)포맷 (년-월-일 시:분:초)
def fmt_datetime(dt: Optional[datetime]) -> Optional[str]:
    return dt.strftime("%Y-%m-%d %H:%M:%S") if dt else None

# =========================================================
# VolunteerCenter (봉사센터) - VMS 크롤링으로 채워지는 테이블
# center_id/region_id 제외 나머지는 모두 null 가능
# =========================================================

# update_at 은 외부 api로 요청받는게 아니기 때문에 create에 안씀
class VolunteerCenterCreate(BaseModel):
    region_id: int
    vol_name: Optional[str] = None
    vol_address: Optional[str] = None
    target: Optional[str] = None
    vms_url: Optional[str] = None
    vol_qual: Optional[str] = None
    vol_act: Optional[str] = None
    vol_date: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None

# 지도 탭 - 봉사센터 조회/핀 표시용 응답
class VolunteerCenterResponse(BaseModel):
    center_id: int
    region_id: int
    vol_name: Optional[str]
    vol_address: Optional[str]
    vol_title: Optional[str]
    target: Optional[str]
    vms_url: Optional[str]
    vol_qual: Optional[str]
    vol_act: Optional[str]
    vol_date: Optional[str]
    latitude: Optional[Decimal]
    longitude: Optional[Decimal]
    # 마지막 크롤링 확인 시각 - 오래된(사라진) 공고를 조회 단계에서 자연스럽게 제외/재노출하는 데 사용
    updated_at: datetime


 # 지도 SDK가 float을 기대하므로 Decimal -> float 변환
    @field_serializer("latitude", "longitude")
    def serialize_coord(self, value: Optional[Decimal], _info):
        return float(value) if value is not None else None
 
    @field_serializer("updated_at")
    def serialize_datetime(self, dt: datetime, _info):
        return fmt_datetime(dt)
 
    model_config = ConfigDict(from_attributes=True)

# =========================================================
# City (시도)
# =========================================================

class CityCreate(BaseModel):
    city_name: str
 
 
class CityResponse(BaseModel):
    city_id: int
    city_name: str
    created_at: datetime
    updated_at: datetime
 
    @field_serializer("created_at", "updated_at")
    def serialize_datetime(self, dt: datetime, _info):
        return fmt_datetime(dt)
 
    model_config = ConfigDict(from_attributes=True)
 
 
class CityUpdate(BaseModel):
    city_name: Optional[str] = None


# =========================================================
# Region (시군구) - city 참조
# =========================================================
 
class RegionCreate(BaseModel):
    city_id: int
    region_name: str
 
 
class RegionResponse(BaseModel):
    region_id: int
    city_id: int
    region_name: str
    created_at: datetime
    updated_at: datetime
 
    @field_serializer("created_at", "updated_at")
    def serialize_datetime(self, dt: datetime, _info):
        return fmt_datetime(dt)
 
    model_config = ConfigDict(from_attributes=True)
 
 
class RegionUpdate(BaseModel):
    region_name: Optional[str] = None

# =========================================================
# Competition (동네대항전 대회)
# =========================================================
 
class CompetitionCreate(BaseModel):
    title: str
    description: Optional[str] = None
    status: CompetitionStatus = CompetitionStatus.IN_PROGRESS
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
 
 
class CompetitionResponse(BaseModel):
    competition_id: int
    title: Optional[str]
    description: Optional[str]
    status: Optional[CompetitionStatus]
    start_at: Optional[datetime]
    end_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
 
    @field_serializer("start_at", "end_at", "created_at", "updated_at")
    def serialize_datetime(self, dt: Optional[datetime], _info):
        return fmt_datetime(dt)
 
    model_config = ConfigDict(from_attributes=True)
 
 
class CompetitionUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[CompetitionStatus] = None
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
 
 
# =========================================================
# CompetitionParticipant (대회 참가 지역 - 점수/순위)
# =========================================================
 
class CompetitionParticipantCreate(BaseModel):
    competition_id: int
    region_id: int
 
 
# score/rank는 서버(집계 로직)가 계산해서 채우는 값 -> Update 전용으로 분리
class CompetitionParticipantUpdate(BaseModel):
    score: Optional[int] = None
    rank: Optional[int] = None
 
 
class CompetitionParticipantResponse(BaseModel):
    participant_id: int
    competition_id: int
    region_id: int
    score: Optional[int]
    rank: Optional[int]
    joined_at: datetime
    updated_at: datetime
 
    @field_serializer("joined_at", "updated_at")
    def serialize_datetime(self, dt: datetime, _info):
        return fmt_datetime(dt)
 
    model_config = ConfigDict(from_attributes=True)
 
 
# =========================================================
# CompetitionContribution (기여 원장 - 점수 집계/롤백용, UI 직접 노출 X)
# =========================================================
 
class CompetitionContributionCreate(BaseModel):
    competition_id: int
    user_id: int
    submission_id: int
    region_id: int
    points: Optional[int] = None
 
 
class CompetitionContributionResponse(BaseModel):
    contribution_id: int
    competition_id: int
    user_id: int
    submission_id: int
    region_id: int
    points: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]
 
    @field_serializer("created_at", "updated_at")
    def serialize_datetime(self, dt: Optional[datetime], _info):
        return fmt_datetime(dt)
 
    model_config = ConfigDict(from_attributes=True)