from datetime import datetime
from decimal import Decimal
from sqlalchemy import BigInteger, Integer, String, Text, ForeignKey, DECIMAL, TIMESTAMP, Enum, func
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.common.database import Base
from backend.app.map.enums import CompetitionStatus


class VolunteerCenter(Base):
    __tablename__ = "volunteer_center"

    # 크롤링 데이터기에 fk pk를 제외한 나머지가 모두 null이될수있음
    center_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True, comment="봉사센터 ID")
    region_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("region.region_id"), nullable=False, comment="지역 FK")
    vol_name: Mapped[str] = mapped_column(String(200), nullable=True, comment="봉사센터명")
    vol_address: Mapped[str] = mapped_column(String(255), nullable=True, comment="봉사센터 주소")
    target: Mapped[str] = mapped_column(String(200), nullable=True, comment="봉사 대상")
    vms_url: Mapped[str] = mapped_column(String(500), nullable=True, comment="VMS 원본 URL")
    vol_qual: Mapped[str] = mapped_column(String(500), nullable=True, comment="봉사 자격요건")
    vol_act: Mapped[str] = mapped_column(String(2000), nullable=True, comment="봉사 활동내용")
    vol_date: Mapped[str] = mapped_column(String(1000), nullable=True, comment="봉사 가능일자")
    # Decimal (Python 코드안에서의 타입) DECIMAL (DB테이블에 저장되는 방식)
    # 크롤링 시 좌표 매칭 실패 가능성있어서 null 허용
    latitude: Mapped[Decimal] = mapped_column(DECIMAL(10, 7), nullable=True, comment="봉사센터 위도")
    longitude: Mapped[Decimal] = mapped_column(DECIMAL(10, 7), nullable=True, comment="봉사센터 경도")
    # 크롤링 갱신 시각 - 오래된(사라진) 공고 판별용
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), comment="마지막 크롤링 확인 시각")

class Region(Base):
    __tablename__ = "region"

    region_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True, comment="지역 고유 번호")
    city_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("city.city_id"), nullable=False, comment="시도FK")
    # ERD는 클라우드 자동생성본이라 아직 NULL로 되어있으나, 팀 확정 방침에 따라 NOT NULL로 지정
    region_name: Mapped[str] = mapped_column(String(100), nullable=False, comment="지역명(시군구)")
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now(), comment="생성일시")
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), comment="수정일시")


class City(Base):
    __tablename__ = "city"

    city_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True, comment="행정구역 고유번호")
    # ERD는 클라우드 자동생성본이라 아직 NULL로 되어있으나, 추구하는 방향 따라 NOT NULL로 지정
    city_name: Mapped[str] = mapped_column(String(100), nullable=False, comment="행정구역명")
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now(), comment="생성일시")
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), comment="수정일시")


class Competition(Base):
    __tablename__ = "competition"

    competition_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="대회 고유번호")
    title: Mapped[str] = mapped_column(String(200), nullable=True, comment="대회명")
    description: Mapped[str] = mapped_column(Text, nullable=True, comment="대회 설명")
    status: Mapped[CompetitionStatus] = mapped_column(Enum(CompetitionStatus), nullable=True, comment="대회 상태 (IN_PROGRESS/SETTLING)")
    start_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=True, comment="시작일시")
    end_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=True, comment="종료일시")
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now(), comment="생성일시")
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), comment="수정일시")


class CompetitionParticipant(Base):
    __tablename__ = "competition_participant"

    participant_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="참가 고유번호")
    competition_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("competition.competition_id"), nullable=False, comment="대회 FK")
    region_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("region.region_id"), nullable=False, index=True, comment="참가 지역 FK")
    score: Mapped[int] = mapped_column(Integer, nullable=True, comment="지역 누적 점수")
    rank: Mapped[int] = mapped_column(Integer, nullable=True, comment="지역 순위")
    joined_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now(), comment="참가일시")
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), comment="수정일시")


class CompetitionContribution(Base):
    __tablename__ = "competition_contribution"

    contribution_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="기여 고유번호")
    competition_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("competition.competition_id"), nullable=False, comment="대회 FK")
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("user.user_id"), nullable=False, comment="기여자 user FK")
    submission_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("quest_submission.submission_id"), nullable=False, comment="퀘스트 인증 제출 FK")
    region_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("region.region_id"), nullable=False, index=True, comment="기여 지역 FK")
    points: Mapped[int] = mapped_column(Integer, nullable=True, comment="획득 포인트")
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now(), comment="생성일시")
    # INSERT 시 자동으로는 안 채워지지만
    # onupdate는 넣어서 실제 UPDATE 발생 시엔 갱신되도록 처리
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=True, onupdate=func.now(), comment="수정일시")