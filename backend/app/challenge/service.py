from __future__ import annotations

# =========================================================
# [Challenge Service 구현 기준]
#
# 1. 트랜잭션 처리
#    - Repository와 Service는 commit()과 rollback()을 직접 호출하지 않습니다.
#    - FastAPI 요청에서는 common/database.py의 get_db()가
#      요청 성공 시 commit(), 오류 발생 시 rollback()을 처리합니다.
#    - Celery 작업에서는 tasks.py가 commit(), rollback(), close()를 처리합니다.
#
# 2. 팀 기능
#    - 팀 생성, 목록·상세 조회, 참가, 나가기, 팀장 위임,
#      사용자 초대와 초대 수락·거절 로직을 처리합니다.
#    - 권한, 팀 상태, 정원, 비밀번호와 중복 참가 여부를 검증합니다.
#
# 3. 초대 자동 만료
#    - 초대 목록 조회와 초대 응답 시 만료 상태를 즉시 반영합니다.
#    - Celery Beat가 만료된 PENDING 초대를 정기적으로 처리합니다.
#
# 4. AI 팀원 추천 후보 조회
#    - 추천 요청자가 활성 사용자이며 해당 팀의 팀장인지 확인합니다.
#    - 팀 모집 상태, 만료 여부와 정원을 검증합니다.
#    - 확정된 제외 조건을 적용해 추천 후보를 조회합니다.
#    - 후보 사용자의 최근 30일 승인 활동을
#      카테고리·난이도·활동 시간대별 통계로 변환합니다.
#
# 5. AI 서버 연동과 응답 검증
#    - 후보가 없으면 AI 서버를 호출하지 않고 빈 추천 응답을 반환합니다.
#    - 후보가 있으면 동기 HTTP Client를 통해 AI 서버를 호출합니다.
#    - Timeout, 연결 실패, 처리 불가와 계약 오류를
#      적절한 HTTP 상태 코드로 변환합니다.
#    - AI 응답의 점수, 순위, 추천 수와 전체 구조를 Pydantic으로 검증합니다.
#    - 요청한 팀·Quest·top_k와 응답값이 일치하는지 확인합니다.
#    - Backend가 전달하지 않은 후보가 추천 결과에 포함되는 것을 차단합니다.
#
# 6. 추천 결과의 초대 연결
#    - 추천 결과의 user_id는 기존 TeamInviteCreate 요청에 사용합니다.
#    - 실제 초대 시 ChallengeTeamService.create_team_invite()가
#      권한, 정원, 팀원 여부와 기존 초대 상태를 다시 검증합니다.
# =========================================================

from pydantic import ValidationError
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.app.auth.models import User
from backend.app.challenge.ai_client import (
    ChallengeRecommendationAIClient,
    ChallengeRecommendationConnectionError,
    ChallengeRecommendationRequestError,
    ChallengeRecommendationResponseError,
    ChallengeRecommendationTimeoutError,
    ChallengeRecommendationUnavailableError,
)
from backend.app.challenge.enums import (
    TeamInviteStatus,
    TeamMemberRole,
    TeamStatus,
)
from backend.app.challenge.models import (
    Team,
    TeamInvite,
    TeamMember,
)
from backend.app.challenge.repository import (
    ChallengeRecommendationRepository,
    TeamInviteRepository,
    TeamMemberRepository,
    TeamRepository,
    TeamSortType,
)
from backend.app.challenge.schema import (
    TeamCreate,
    TeamInviteCreate,
    TeamInviteStatusUpdate,
    TeamRecommendationResponse,
)
from backend.app.common.auth import (
    get_password_hash,
    verify_password,
)

# 초대 만료 시간이 별도로 전달되지 않았을 때 사용할 기본 유효기간입니다.
DEFAULT_INVITE_EXPIRATION_DAYS = 30

# AI 추천에서 최근 활동으로 인정할 기간입니다.
RECOMMENDATION_ACTIVITY_DAYS = 30

# 팀 초대를 최근 거절한 사용자를 추천에서 제외할 기간입니다.
RECOMMENDATION_REJECTION_COOLDOWN_DAYS = 7

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
        # page - 1을 하는 이유는 1페이지에서는 아무 데이터도 건너뛰면 안 되기 때문.
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
        # 비활성화된 사용자의 팀 참가를 차단.
        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="비활성화된 사용자는 팀에 참가할 수 없습니다.",
            )

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
    # 팀장이 특정 사용자를 Challenge 팀에 직접 초대.
    @staticmethod
    def create_team_invite(
        session: Session,
        *,
        invite_data: TeamInviteCreate,
        current_user: User,
    ) -> TeamInvite:
        """팀장이 특정 사용자를 Challenge 팀에 직접 초대합니다."""

        # 비활성화된 사용자가 초대를 생성하는 것을 차단.
        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="비활성화된 사용자는 팀원을 초대할 수 없습니다.",
            )

        # 요청받은 팀 ID로 팀 정보를 조회.
        team = TeamRepository.get_team_by_id(
            session,
            invite_data.team_id,
        )

        # 존재하지 않는 팀에 대한 초대 생성을 차단.
        if team is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="존재하지 않는 팀입니다.",
            )

        # Team 테이블에 저장된 leader_id를 기준으로 팀장 권한을 확인.
        if team.leader_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="팀장만 사용자를 초대할 수 있습니다.",
            )

        # 현재 팀원을 모집 중인 팀만 새로운 초대를 생성할 수 있도록 검사.
        if team.status != TeamStatus.RECRUITING:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="현재 팀원을 모집 중인 팀이 아닙니다.",
            )

        # 팀 만료 시간이 설정된 경우 이미 만료된 팀인지 확인.
        if team.expires_at is not None:
            current_time = datetime.now(
                tz=team.expires_at.tzinfo,
            )

            if team.expires_at <= current_time:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="이미 만료된 팀입니다.",
                )

        # 팀장이 자기 자신을 초대하는 요청을 차단.
        if invite_data.user_id == current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="자기 자신을 초대할 수 없습니다.",
            )

        # 초대받을 사용자가 실제로 존재하는지 조회.
        invited_user = session.get(
            User,
            invite_data.user_id,
        )

        # 존재하지 않는 사용자를 초대하는 것을 차단.
        if invited_user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="초대할 사용자를 찾을 수 없습니다.",
            )

        # 비활성화된 사용자를 팀에 초대하는 것을 차단.
        if not invited_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="비활성화된 사용자는 팀에 초대할 수 없습니다.",
            )

        # 초대받을 사용자가 이미 해당 팀에 참가 중인지 확인.
        existing_member = (
            TeamMemberRepository.get_member_by_team_and_user(
                session,
                team_id=team.team_id,
                user_id=invite_data.user_id,
            )
        )

        # 이미 팀에 참가 중인 사용자를 다시 초대하는 것을 차단.
        if existing_member is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="이미 해당 팀에 참가 중인 사용자입니다.",
            )

        # 현재 팀 참가 인원을 조회.
        current_members = (
            TeamMemberRepository.count_team_members(
                session,
                team_id=team.team_id,
            )
        )

        # 이미 최대 정원에 도달한 팀의 초대 생성을 차단.
        if current_members >= team.max_members:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="팀 정원이 모두 찼습니다.",
            )

        # 클라이언트가 전달한 초대 만료 시간을 가져옴.
        expires_at = invite_data.expires_at

        # 만료 시간이 없으면 현재 시각으로부터 30일 후로 자동 설정.
        if expires_at is None:
            expires_at = (
                datetime.now(timezone.utc)
                + timedelta(
                    days=DEFAULT_INVITE_EXPIRATION_DAYS,
                )
            )

        # 만료 시간이 전달된 경우 현재보다 미래인지 확인.
        else:
            current_time = datetime.now(
                tz=expires_at.tzinfo,
            )

            if expires_at <= current_time:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="초대 만료 시간은 현재 시각보다 이후여야 합니다.",
                )

        # 같은 팀에서 같은 사용자에게 생성된 기존 초대가 있는지 확인.
        existing_invite = (
            TeamInviteRepository.get_invite_by_team_and_user(
                session,
                team_id=team.team_id,
                user_id=invite_data.user_id,
            )
        )

        # 기존 초대가 없으면 새로운 초대 데이터를 생성.
        if existing_invite is None:
            invite = TeamInviteRepository.create_invite(
                session,
                team_id=team.team_id,
                user_id=invite_data.user_id,
                expires_at=expires_at,
            )

            return invite

        # 기존 초대가 아직 응답 대기 상태이면 중복 초대를 차단.
        if existing_invite.status == TeamInviteStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="이미 처리 대기 중인 초대가 있습니다.",
            )

        # 기존 초대가 이미 수락된 상태이면 재초대를 차단.
        if existing_invite.status == TeamInviteStatus.ACCEPTED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="이미 수락 처리된 초대입니다.",
            )

        # 거절되었거나 만료된 초대는 기존 행을 다시 PENDING 상태로 변경.
        renewed_invite = TeamInviteRepository.renew_invite(
            session,
            invite=existing_invite,
            expires_at=expires_at,
        )

        return renewed_invite

    # 현재 로그인 사용자가 받은 처리 대기 중 초대 목록을 조회.
    @staticmethod
    def get_received_invites(
        session: Session,
        *,
        current_user: User,
        page: int = 1,
        size: int = 20,
    ) -> list[TeamInvite]:
        """현재 로그인 사용자가 받은 대기 중 초대를 조회합니다."""

        # 목록 조회 전에 만료 시간이 지난 초대를 EXPIRED 상태로 변경.
        ChallengeTeamService.expire_pending_invites(
            session,
        )

        # 요청 페이지에 맞는 offset 값을 계산.
        offset = (page - 1) * size

        # 현재 사용자가 받은 PENDING 상태의 초대 목록을 조회.
        invites = TeamInviteRepository.get_user_pending_invites(
            session,
            user_id=current_user.user_id,
            offset=offset,
            limit=size,
        )

        return invites

    # 현재 로그인 사용자가 받은 초대를 수락하거나 거절.
    @staticmethod
    def respond_team_invite(
        session: Session,
        *,
        invite_id: int,
        update_data: TeamInviteStatusUpdate,
        current_user: User,
    ) -> TeamInvite:
        """현재 로그인 사용자가 받은 초대를 수락하거나 거절합니다."""

        # 초대 처리 전에 만료 시간이 지난 초대를 EXPIRED 상태로 변경.
        ChallengeTeamService.expire_pending_invites(
            session,
        )

        # 초대 ID를 기준으로 초대 데이터를 조회.
        invite = TeamInviteRepository.get_invite_by_id(
            session,
            invite_id,
        )

        # 존재하지 않는 초대 요청을 차단.
        if invite is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="존재하지 않는 초대입니다.",
            )

        # 초대받은 사용자 본인만 초대를 처리할 수 있도록 검사.
        if invite.user_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="해당 초대를 처리할 권한이 없습니다.",
            )

        # 이미 처리되었거나 만료된 초대의 중복 처리를 차단.
        if invite.status != TeamInviteStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="이미 처리되었거나 만료된 초대입니다.",
            )

        # 비활성화된 사용자가 초대를 처리하는 것을 차단.
        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="비활성화된 사용자는 초대를 처리할 수 없습니다.",
            )

        # 사용자가 초대를 거절하면 멤버 추가 없이 상태만 변경.
        if update_data.status == TeamInviteStatus.REJECTED:
            rejected_invite = (
                TeamInviteRepository.update_invite_status(
                    session,
                    invite=invite,
                    status=TeamInviteStatus.REJECTED,
                )
            )

            return rejected_invite

        # 초대에 연결된 팀 정보를 조회.
        team = TeamRepository.get_team_by_id(
            session,
            invite.team_id,
        )

        # 초대 이후 팀이 삭제된 비정상 상황을 처리.
        if team is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="초대에 연결된 팀을 찾을 수 없습니다.",
            )

        # 현재 팀원을 모집 중인 팀의 초대만 수락 가능.
        if team.status != TeamStatus.RECRUITING:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="현재 참가할 수 없는 상태의 팀입니다.",
            )

        # 초대 수락 시점에 팀이 만료되었는지 다시 확인.
        if team.expires_at is not None:
            current_time = datetime.now(
                tz=team.expires_at.tzinfo,
            )

            if team.expires_at <= current_time:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="이미 만료된 팀입니다.",
                )

        # 초대 이후 사용자가 직접 참가했을 가능성이 있어 멤버 여부를 재확인.
        existing_member = (
            TeamMemberRepository.get_member_by_team_and_user(
                session,
                team_id=team.team_id,
                user_id=current_user.user_id,
            )
        )

        # 이미 참가 중인 사용자의 초대 수락을 차단.
        if existing_member is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="이미 해당 팀에 참가 중입니다.",
            )

        # 초대 생성 이후 팀 정원이 찼을 가능성이 있어 현재 인원을 재조회.
        current_members = (
            TeamMemberRepository.count_team_members(
                session,
                team_id=team.team_id,
            )
        )

        # 최대 정원에 도달한 경우 초대 수락을 차단.
        if current_members >= team.max_members:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="팀 정원이 모두 차서 초대를 수락할 수 없습니다.",
            )

        # 모든 조건을 통과하면 초대받은 사용자를 일반 팀원으로 추가.
        TeamMemberRepository.add_member(
            session,
            team_id=team.team_id,
            user_id=current_user.user_id,
            role_in_team=TeamMemberRole.MEMBER,
        )

        # 팀원 추가가 완료된 후 초대 상태를 ACCEPTED로 변경.
        accepted_invite = (
            TeamInviteRepository.update_invite_status(
                session,
                invite=invite,
                status=TeamInviteStatus.ACCEPTED,
            )
        )

        return accepted_invite

    # 만료 시간이 지난 PENDING 초대를 EXPIRED 상태로 일괄 변경.
    @staticmethod
    def expire_pending_invites(
        session: Session,
    ) -> int:
        """만료 시간이 지난 처리 대기 중 초대를 만료 처리합니다."""

        # Repository에 현재 UTC 시각을 전달하여 만료된 초대를 변경.
        expired_count = (
            TeamInviteRepository.expire_pending_invites(
                session,
                current_time=datetime.now(timezone.utc),
            )
        )

        # 상태가 변경된 초대 개수를 반환.
        return expired_count



class ChallengeRecommendationService:
    """AI 팀원 추천 후보 조회와 데이터 정리를 담당하는 Service."""

    @staticmethod
    def _normalize_enum_value(value: Any) -> str | None:
        """Enum 또는 문자열 값을 AI 전달용 문자열로 변환."""

        if value is None:
            return None

        enum_value = getattr(value, "value", None)

        if enum_value is not None:
            return str(enum_value)

        return str(value)


    @staticmethod
    def _normalize_active_time_values(
        value: Any,
    ) -> list[Any]:
        """팀·Quest 활동 시간 값을 AI 요청용 목록으로 변환합니다."""

        # 활동 시간 값이 없으면 빈 목록을 반환합니다.
        if value is None:
            return []

        # 이미 목록이라면 그대로 반환합니다.
        if isinstance(value, list):
            return value

        # tuple 또는 set이면 목록으로 변환합니다.
        if isinstance(value, (tuple, set)):
            return list(value)

        # 단일 값이면 요소 하나를 가진 목록으로 변환합니다.
        return [value]

    @staticmethod
    def _get_active_time_bucket(submitted_at: datetime) -> int:
        """Quest 제출 시각을 0·6·12·18시 기준 활동 시간대로 변환.

        예시:
        - 00:00~05:59 → 0
        - 06:00~11:59 → 6
        - 12:00~17:59 → 12
        - 18:00~23:59 → 18
        """

        hour = submitted_at.hour

        if hour < 6:
            return 0

        if hour < 12:
            return 6

        if hour < 18:
            return 12

        return 18

    @staticmethod
    def _build_recent_activity_map(
        activity_rows: list[tuple[Any, Any, Any]],
    ) -> dict[int, dict[str, Any]]:
        """최근 Quest 수행 기록을 사용자별 통계로 정리.

        Repository에서 가져온 수행 기록을 이용해 사용자별로 다음 정보를 만든다.

        - 최근 완료한 전체 Quest 수
        - 카테고리별 완료 횟수
        - 난이도별 완료 횟수
        - 활동 시간대별 완료 횟수
        """

        # 후보별 최근 활동 통계를 저장.
        activity_map: dict[int, dict[str, Any]] = {}

        for submission, quest, category in activity_rows:
            user_id = submission.user_id

            # 해당 사용자의 통계가 아직 없으면 기본 구조를 만든다.
            if user_id not in activity_map:
                activity_map[user_id] = {
                    "completed_count": 0,
                    "category_counts": defaultdict(int),
                    "difficulty_counts": defaultdict(int),
                    "active_time_counts": defaultdict(int),
                }

            user_activity = activity_map[user_id]

            # 전체 완료 횟수를 1 증가.
            user_activity["completed_count"] += 1

            # 수행한 Quest의 카테고리 횟수를 증가.
            category_key = str(category.name)
            user_activity["category_counts"][category_key] += 1

            # 수행한 Quest의 난이도 횟수를 증가.
            difficulty_key = (
                ChallengeRecommendationService
                ._normalize_enum_value(
                    quest.difficulty,
                )
            )

            if difficulty_key is not None:
                user_activity["difficulty_counts"][difficulty_key] += 1

            # Quest 제출 시각을 활동 시간대로 변환하여 횟수를 증가.
            active_time_bucket = (
                ChallengeRecommendationService
                ._get_active_time_bucket(
                    submission.submitted_at,
                )
            )

            user_activity["active_time_counts"][
                str(active_time_bucket)
            ] += 1

        # defaultdict를 일반 dict로 변경하여 JSON 변환이 가능하게 만든다.
        for user_activity in activity_map.values():
            user_activity["category_counts"] = dict(
                user_activity["category_counts"]
            )
            user_activity["difficulty_counts"] = dict(
                user_activity["difficulty_counts"]
            )
            user_activity["active_time_counts"] = dict(
                user_activity["active_time_counts"]
            )

        return activity_map

    @staticmethod
    def get_recommendation_candidates(
        session: Session,
        *,
        team_id: int,
        current_user: User,
    ) -> dict[str, Any]:
        """AI 팀원 추천에 사용할 후보 사용자 데이터를 조회.

        처리 순서:

        1. 현재 사용자의 이용 가능 여부 확인
        2. 추천 대상 팀·Quest·Category 조회
        3. 현재 사용자가 팀장인지 확인
        4. 팀 상태·만료·정원 확인
        5. 추천 가능한 후보 사용자 조회
        6. 후보 사용자의 최근 30일 승인 활동 조회
        7. 최근 활동을 사용자별 통계로 정리

        추천 점수 계산과 Top-K 선정은 AI Server에서 처리합니다.
        """

        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="비활성화된 사용자는 팀원 추천을 요청할 수 없습니다.",
            )

        # 추천 대상 팀과 연결된 Quest·Category·현재 인원을 조회.
        context = (
            ChallengeRecommendationRepository
            .get_team_recommendation_context(
                session,
                team_id=team_id,
            )
        )

        if context is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="존재하지 않는 팀입니다.",
            )

        team, quest, category, current_members = context

        if team.leader_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="팀장만 팀원 추천을 요청할 수 있습니다.",
            )

        if team.status != TeamStatus.RECRUITING:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="현재 팀원을 모집 중인 팀이 아닙니다.",
            )

        # 팀 만료 여부와 최근 활동 기간 계산에 사용할 현재 UTC 시각.
        current_time = datetime.now(timezone.utc)

        if (
            team.expires_at is not None
            and team.expires_at <= current_time
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="이미 만료된 팀입니다.",
            )

        if current_members >= team.max_members:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="팀 정원이 모두 찼습니다.",
            )

        # 최근 초대 거절자를 제외하기 위한 기준 시각.
        rejected_since = current_time - timedelta(
            days=RECOMMENDATION_REJECTION_COOLDOWN_DAYS,
        )

        # 확정된 제외 조건을 적용해 추천 가능한 후보를 조회.
        candidates = (
            ChallengeRecommendationRepository
            .list_recommendation_candidates(
                session,
                requester_id=current_user.user_id,
                team_id=team.team_id,
                quest_id=team.quest_id,
                rejected_since=rejected_since,
            )
        )

        # 후보가 없으면 AI Server를 호출하지 않도록 빈 후보 목록을 반환.
        if not candidates:
            return {
                "requester_id": current_user.user_id,
                "team": {
                    "team_id": team.team_id,
                    "quest_id": team.quest_id,
                    "name": team.name,
                    "region": team.region,
                    "current_members": current_members,
                    "max_members": team.max_members,
                },
                "quest": {
                    "quest_id": quest.quest_id,
                    "category_id": category.category_id,
                    "category_name": category.name,
                    "title": quest.quest_title,
                    "description": quest.quest_description,
                    "difficulty": (
                        ChallengeRecommendationService
                        ._normalize_enum_value(
                            quest.difficulty,
                        )
                    ),
                    "active_time": (
                        ChallengeRecommendationService
                        ._normalize_active_time_values(
                            getattr(quest, "active_time", None),
                        )
                    ),
                    "location": quest.location,
                    "embedding": quest.quest_embedding,
                },
                "candidates": [],
            }

        # 최근 활동으로 인정할 시작 시각을 계산.
        activity_since = current_time - timedelta(
            days=RECOMMENDATION_ACTIVITY_DAYS,
        )

        # 후보 사용자 ID만 별도로 모읍니다.
        candidate_user_ids = [
            candidate.user_id
            for candidate, _ in candidates
        ]

        # 후보들의 최근 30일 승인 활동을 한 번에 조회.
        activity_rows = (
            ChallengeRecommendationRepository
            .list_recent_candidate_activities(
                session,
                candidate_user_ids=candidate_user_ids,
                since=activity_since,
            )
        )

        # 조회한 수행 기록을 사용자별 활동 통계로 정리.
        activity_map = (
            ChallengeRecommendationService
            ._build_recent_activity_map(
                activity_rows,
            )
        )

        # 후보별로 AI Server에 전달할 데이터를 구성.
        candidate_data: list[dict[str, Any]] = []

        for candidate, region_name in candidates:
            recent_activity = activity_map.get(
                candidate.user_id,
                {
                    "completed_count": 0,
                    "category_counts": {},
                    "difficulty_counts": {},
                    "active_time_counts": {},
                },
            )

            candidate_data.append(
                {
                    "user_id": candidate.user_id,
                    "nickname": candidate.nickname,
                    "profile_image_url": candidate.profile_image_url,
                    "region_id": candidate.region_id,
                    "region": region_name,
                    "preferred_categories": candidate.category or [],
                    "preferred_difficulty": (
                        ChallengeRecommendationService
                        ._normalize_enum_value(
                            candidate.preferred_difficulty,
                        )
                    ),
                    "active_time": candidate.active_time or [],
                    "current_level": candidate.current_level,
                    "daily_streak": candidate.daily_streak,
                    "latitude": (
                        float(candidate.current_latitude)
                        if candidate.current_latitude is not None
                        else None
                    ),
                    "longitude": (
                        float(candidate.current_longitude)
                        if candidate.current_longitude is not None
                        else None
                    ),
                    "profile_embedding": candidate.profile_embedding,
                    "recent_activity": recent_activity,
                }
            )

        # 다음 AI Server 단계에서 바로 사용할 수 있는 형태로 반환.
        return {
            "requester_id": current_user.user_id,
            "team": {
                "team_id": team.team_id,
                "quest_id": team.quest_id,
                "name": team.name,
                "region": team.region,
                "current_members": current_members,
                "max_members": team.max_members,
            },
            "quest": {
                "quest_id": quest.quest_id,
                "category_id": category.category_id,
                "category_name": category.name,
                "title": quest.quest_title,
                "description": quest.quest_description,
                "difficulty": (
                    ChallengeRecommendationService
                    ._normalize_enum_value(
                        quest.difficulty,
                    )
                ),
                "active_time": (
                    ChallengeRecommendationService
                    ._normalize_active_time_values(
                        getattr(quest, "active_time", None),
                    )
                ),
                "location": quest.location,
                "embedding": quest.quest_embedding,
            },
            "candidates": candidate_data,
        }


    @staticmethod
    def get_team_member_recommendations(
        session: Session,
        *,
        team_id: int,
        current_user: User,
        top_k: int = 5,
        ai_client: ChallengeRecommendationAIClient | None = None,
    ) -> TeamRecommendationResponse:
        """후보 데이터를 준비하고 AI 서버의 최종 추천 결과를 검증."""

        # Router 외부에서 호출해도 추천 수 범위를 보장.
        if not 1 <= top_k <= 20:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="추천 인원은 1명 이상 20명 이하여야 합니다.",
            )

        # 기존 후보 조회 로직을 재사용해 권한·팀 상태·제외 조건을 검증.
        payload = (
            ChallengeRecommendationService
            .get_recommendation_candidates(
                session,
                team_id=team_id,
                current_user=current_user,
            )
        )

        # AI 서버가 최종 추천 결과 수를 결정할 수 있도록 요청값을 추가.
        payload["top_k"] = top_k

        # AI 응답에 포함할 수 있는 정상 후보 사용자 ID를 저장.
        candidate_user_ids = {
            candidate["user_id"]
            for candidate in payload["candidates"]
        }

        # 후보가 없으면 AI 서버를 호출하지 않고 검증된 빈 응답을 반환.
        if not payload["candidates"]:
            return TeamRecommendationResponse(
                team_id=payload["team"]["team_id"],
                quest_id=payload["quest"]["quest_id"],
                recommendations=[],
                requested_top_k=top_k,
                recommendation_count=0,
                warnings=[],
            )

        # 테스트에서는 가짜 Client를 주입하고 실제 실행에서는 기본 Client 생성.
        recommendation_client = (
            ai_client
            if ai_client is not None
            else ChallengeRecommendationAIClient()
        )

        try:
            # 후보 데이터를 AI 서버에 전달하고 원시 JSON 응답을 조회.
            raw_response = (
                recommendation_client
                .request_recommendations(
                    payload=payload,
                )
            )

        except ChallengeRecommendationTimeoutError as exc:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="AI 추천 서버의 응답 시간이 초과되었습니다.",
            ) from exc

        except ChallengeRecommendationConnectionError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI 추천 서버에 연결할 수 없습니다.",
            ) from exc

        except ChallengeRecommendationUnavailableError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI 팀원 추천 처리에 실패했습니다.",
            ) from exc

        except ChallengeRecommendationRequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="AI 추천 요청 데이터 형식이 올바르지 않습니다.",
            ) from exc

        except ChallengeRecommendationResponseError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="AI 추천 서버의 응답 형식이 올바르지 않습니다.",
            ) from exc

        try:
            # 200 응답이라도 필드·점수·순위·개수 구조를 Pydantic으로 검증.
            response_data = (
                TeamRecommendationResponse
                .model_validate(
                    raw_response,
                )
            )

        except ValidationError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="AI 추천 서버의 응답 형식이 올바르지 않습니다.",
            ) from exc

        # AI 서버가 다른 팀의 결과를 반환하는 계약 오류를 차단.
        if response_data.team_id != payload["team"]["team_id"]:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="AI 추천 서버가 잘못된 팀 정보를 반환했습니다.",
            )

        # AI 서버가 다른 Quest 결과를 반환하는 계약 오류를 차단.
        if response_data.quest_id != payload["quest"]["quest_id"]:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="AI 추천 서버가 잘못된 Quest 정보를 반환했습니다.",
            )

        # 요청값과 AI 응답의 추천 수 기준이 달라지는 문제를 차단.
        if response_data.requested_top_k != top_k:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="AI 추천 서버가 잘못된 추천 수 정보를 반환했습니다.",
            )

        # Backend가 전달하지 않은 사용자가 추천 결과에 포함되는 것을 차단.
        invalid_recommended_user_ids = {
            recommendation.user_id
            for recommendation in response_data.recommendations
            if recommendation.user_id not in candidate_user_ids
        }

        if invalid_recommended_user_ids:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="AI 추천 서버가 후보가 아닌 사용자를 반환했습니다.",
            )

        return response_data