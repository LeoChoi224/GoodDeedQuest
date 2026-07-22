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
from backend.app.common.auth import (
    get_password_hash,
    verify_password,
)


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
    
    # 공개 또는 비공개 Challenge 팀에 참가.
    @staticmethod
    def join_team(
        session: Session,
        *,
        team_id: int,
        password: str | None,
        current_user: User,
    ) -> TeamMember:
        # 참가하려는 팀 정보를 조회.
        team = TeamRepository.get_team_by_id(
            session,
            team_id,
        )
        if team is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="존재하지 않는 팀입니다.",
            )
        if team.status != TeamStatus.RECRUITING:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="현재 참가할 수 없는 상태의 팀입니다.",
            )
        if team.expires_at is not None:
            current_time = datetime.now(
                tz=team.expires_at.tzinfo
            )

            if team.expires_at <= current_time:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="이미 만료된 팀입니다.",
                )

        # 현재 사용자가 이미 해당 팀에 참가하고 있는지 확인.
        existing_member = (
            TeamMemberRepository.get_member_by_team_and_user(
                session,
                team_id=team_id,
                user_id=current_user.user_id,
            )
        )
        if existing_member is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="이미 참가 중인 팀입니다.",
            )

        # 팀의 현재 참가 인원을 조회.
        current_members = (
            TeamMemberRepository.count_team_members(
                session,
                team_id=team_id,
            )
        )
        if current_members >= team.max_members:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="팀 정원이 모두 찼습니다.",
            )

        # 비공개 팀은 비밀번호를 확인.
        if not team.is_public:
            if password is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="비공개 팀 비밀번호를 입력해 주세요.",
                )

            if team.password_hash is None:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="팀 비밀번호 정보가 올바르지 않습니다.",
                )

            # 입력한 비밀번호와 저장된 비밀번호 해시를 비교.
            is_password_valid = verify_password(
                password,
                team.password_hash,
            )
            if not is_password_valid:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="팀 비밀번호가 일치하지 않습니다.",
                )

        # 모든 참가 조건을 통과하면 일반 팀원으로 추가.
        member = TeamMemberRepository.add_member(
            session,
            team_id=team_id,
            user_id=current_user.user_id,
            role_in_team=TeamMemberRole.MEMBER,
        )

        return member

    # 현재 로그인 사용자가 참가 중인 팀에서 나갈때.
    @staticmethod
    def leave_team(
        session: Session,
        *,
        team_id: int,
        current_user: User,
    ) -> None:
        # 나가려는 팀 정보를 조회.
        team = TeamRepository.get_team_by_id(
            session,
            team_id,
        )
        if team is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="존재하지 않는 팀입니다.",
            )

        # 현재 사용자의 팀 참가 정보를 조회.
        current_member = (
            TeamMemberRepository.get_member_by_team_and_user(
                session,
                team_id=team_id,
                user_id=current_user.user_id,
            )
        )

        if current_member is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="현재 사용자는 해당 팀에 참가하고 있지 않습니다.",
            )

        # 현재 팀에 참가하고 있는 전체 인원을 조회.
        current_members = (
            TeamMemberRepository.count_team_members(
                session,
                team_id=team_id,
            )
        )

        # 현재 사용자가 마지막 팀원이면 팀 자체를 삭제.
        if current_members == 1:
            TeamRepository.delete_team(
                session,
                team=team,
            )
            return

        # 현재 사용자가 팀장인지 확인.
        is_leader = (
            current_member.role_in_team
            == TeamMemberRole.LEADER
        )

        # 팀장이 나가는 경우 새로운 팀장을 자동으로 지정.
        if is_leader:
            # 기존 팀장을 제외하고 가장 먼저 참가한 팀원을 조회.
            next_leader = (
                TeamMemberRepository.get_next_leader_candidate(
                    session,
                    team_id=team_id,
                    excluding_user_id=current_user.user_id,
                )
            )

            # 남은 인원은 있지만 팀장 후보를 찾지 못한 경우를 처리 (방어코드).
            if next_leader is None:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="새로운 팀장 후보를 찾을 수 없습니다.",
                )

            # 가장 먼저 참가한 팀원을 LEADER로 변경.
            TeamMemberRepository.update_member_role(
                session,
                member=next_leader,
                role_in_team=TeamMemberRole.LEADER,
            )

            # Team 테이블의 leader_id도 새로운 팀장으로 변경.
            TeamRepository.update_team_leader(
                session,
                team=team,
                new_leader_id=next_leader.user_id,
            )

        # 일반 팀원 또는 위임이 끝난 기존 팀장의 참가 정보를 삭제.
        TeamMemberRepository.remove_member(
            session,
            member=current_member,
        )
