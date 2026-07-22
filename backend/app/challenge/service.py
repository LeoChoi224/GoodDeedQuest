from __future__ import annotations

# =========================================================
# [반드시 확인 및 검토할 사항]
#
# 1. commit()과 rollback()은 이 Service에서 직접 처리하지 않습니다.
#    - common/database.py의 get_db()가 요청 성공 시 commit(), 오류 발생 시 rollback()을 자동으로 처리합니다.
#
# 2. quest_id가 실제로 존재하는지는 DB 외래키가 최종적으로 검사합니다.
#    - 추후 QuestRepository가 확정되면 팀 생성 전에 존재 여부와 참가 가능 상태를 Service에서 먼저 확인하는 것이 좋습니다.
#
# 3. Repository는 현재 Team 객체와 현재 참가 인원(int)을 함께 반환합니다.
#    - 추후 Quest 모델이 완성되면 퀘스트 제목, 카테고리, 장소 등은 JOIN하여 함께 조회.
#
# 4. 현재 팀 멤버 조회는 TeamMember 정보만 반환합니다.
#    - 사용자 닉네임, 프로필 이미지 등이 필요하면 User 테이블과 JOIN하는 Repository 메서드를 추가.
#
# =========================================================

from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.app.auth.models import User
from backend.app.challenge.enums import (
    TeamMemberRole,
    TeamStatus,
)
from backend.app.challenge.models import (
    Team,
    TeamMember,
)
from backend.app.challenge.repository import (
    TeamMemberRepository,
    TeamRepository,
    TeamSortType,
)
from backend.app.challenge.schema import TeamCreate
from backend.app.common.auth import get_password_hash


class ChallengeTeamService:
    """Challenge 팀 관련 비즈니스 로직을 처리하는 Service."""

    @staticmethod
    def create_team(
        session: Session,
        *,
        team_data: TeamCreate,
        current_user: User,
    ) -> Team:
        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="비활성화된 사용자는 팀을 생성할 수 없습니다.",
            )

        # 팀 만료 시간이 전달된 경우 현재보다 미래인지 확인.
        if team_data.expires_at is not None:
            current_time = datetime.now(
                tz=team_data.expires_at.tzinfo
            )
            if team_data.expires_at <= current_time:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="팀 만료 시간은 현재 시각보다 이후여야 합니다.",
                )

        # 공개 팀은 비밀번호를 저장하지 않습니다.
        password_hash: str | None = None

        # 비공개 팀일 때만 원문 비밀번호를 해시 처리.
        if not team_data.is_public and team_data.password is not None:
            password_hash = get_password_hash(
                team_data.password
            )

        # Team 테이블에 새로운 팀 정보를 저장.
        team = TeamRepository.create_team(
            session,
            leader_id=current_user.user_id,
            quest_id=team_data.quest_id,
            name=team_data.name,
            password_hash=password_hash,
            notification=team_data.notification,
            region=team_data.region,
            is_public=team_data.is_public,
            max_members=team_data.max_members,
            expires_at=team_data.expires_at,
        )

        # 팀 생성자를 해당 팀의 LEADER 멤버로 추가.
        TeamMemberRepository.add_member(
            session,
            team_id=team.team_id,
            user_id=current_user.user_id,
            role_in_team=TeamMemberRole.LEADER,
        )

        session.refresh(team)

        return team
    
    # 검색·필터·정렬 조건에 맞는 팀 목록을 조회.
    @staticmethod
    def get_teams(
        session: Session,
        *,
        quest_id: int | None = None,
        team_status: TeamStatus | None = TeamStatus.RECRUITING,
        is_public: bool | None = None,
        region: str | None = None,
        search: str | None = None,
        sort_by: TeamSortType = "latest",
        page: int = 1,
        size: int = 20,
    ) -> list[tuple[Team, int]]:
        # 요청한 페이지에 해당하는 데이터를 조회하기 위해 앞에서 건너뛸 개수를 계산.
        # page - 1 을 하는 이유는 1페아지에서는 아무것도 건너뛰면 안되기 때문.
        offset = (page - 1) * size

        # Repository에서 팀 정보와 현재 참가 인원을 함께 조회.
        teams = TeamRepository.get_teams(
            session,
            quest_id=quest_id,
            status=team_status,
            is_public=is_public,
            region=region,
            search=search,
            sort_by=sort_by,
            offset=offset,
            limit=size,
        )

        return teams

    # 특정 팀의 상세 정보와 현재 참가 인원을 조회.
    @staticmethod
    def get_team_detail(
        session: Session,
        *,
        team_id: int,
    ) -> tuple[Team, int]:
        team = TeamRepository.get_team_by_id(
            session,
            team_id,
        )
        if team is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="존재하지 않는 팀입니다.",
            )
        current_members = (
            TeamMemberRepository.count_team_members(
                session,
                team_id=team_id,
            )
        )

        return team, current_members

    # 특정 팀에 참가 중인 전체 팀 멤버를 조회.
    @staticmethod
    def get_team_members(
        session: Session,
        *,
        team_id: int,
    ) -> list[TeamMember]:
        team = TeamRepository.get_team_by_id(
            session,
            team_id,
        )
        if team is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="존재하지 않는 팀입니다.",
            )
        members = TeamMemberRepository.get_team_members(
            session,
            team_id=team_id,
        )

        return members

    # 현재 로그인 사용자가 참여 중인 팀 목록을 조회.
    @staticmethod
    def get_my_teams(
        session: Session,
        *,
        current_user: User,
        team_status: TeamStatus | None = None,
        page: int = 1,
        size: int = 20,
    ) -> list[tuple[Team, int]]:
        offset = (page - 1) * size

        teams = TeamRepository.get_user_teams(
            session,
            user_id=current_user.user_id,
            status=team_status,
            offset=offset,
            limit=size,
        )

        return teams