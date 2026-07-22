from __future__ import annotations

# =========================================================
# [반드시 확인 및 검토할 사항]
#
# 1. Challenge 팀 API 주소
#    - POST   /challenges/teams
#    - GET    /challenges/teams
#    - GET    /challenges/my-teams
#    - GET    /challenges/teams/{team_id}
#    - GET    /challenges/teams/{team_id}/members
#    - POST   /challenges/teams/{team_id}/join
#    - DELETE /challenges/teams/{team_id}/leave
#
# 2. 팀 참가 및 나가기 API는 로그인 전용입니다. (추후 확인 필요)
#    - auth/router.py의 get_current_db_user 의존성을 재사용합니다.
#    - Authorization 헤더에 Bearer 액세스 토큰이 필요합니다. 
#
# 3. 팀 목록 조회 / 팀 상세 조회 / 팀 멤버 목록 조회 / 내가 참여 중인 팀 목록 조회 API 주소
#    - GET /challenges/teams
#    - GET /challenges/my-teams
#    - GET /challenges/teams/{team_id}
#    - GET /challenges/teams/{team_id}/members
#
# 4. 팀 목록, 팀 상세, 팀 멤버 목록은 현재 로그인 없이 조회할 수 있도록 작성했습니다.
#    - 추후 인증 필수 정책으로 변경되면 current_user Dependency를 추가.
#
# 5. 팀 멤버 목록은 현재 user_id와 역할 정보만 반환합니다.
#    - 닉네임과 프로필 이미지는 User 모델 JOIN 구현 후 추가.
# =========================================================

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import Literal

from backend.app.auth.router import get_current_db_user
from backend.app.auth.models import User
from backend.app.challenge.schema import (
    TeamCreate,
    TeamDetailResponse,
    TeamListItemResponse,
    TeamMemberResponse,
    TeamPasswordVerify,
    TeamResponse,
)
from backend.app.challenge.service import ChallengeTeamService
from backend.app.common.database import get_db
from backend.app.common.response import APIResponse
from backend.app.challenge.enums import TeamStatus


# Challenge 기능의 공통 URL과 Swagger 태그를 설정.
router = APIRouter(
    prefix="/challenges",
    tags=["Challenge"],
)

@router.post(
    "/teams",
    response_model=APIResponse[TeamResponse],
    status_code=status.HTTP_201_CREATED,
)
def create_team(
    team_data: TeamCreate,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_db_user),
) -> APIResponse[TeamResponse]:

    # Service에 팀 생성 요청과 로그인 사용자 정보를 전달.
    team = ChallengeTeamService.create_team(
        session,
        team_data=team_data,
        current_user=current_user,
    )

    # ORM Team 객체를 응답용 Pydantic Schema로 변환.
    response_data = TeamResponse.model_validate(team)

    # 공통 APIResponse 형식으로 생성 결과를 반환.
    return APIResponse.ok(
        data=response_data,
        message="팀이 성공적으로 생성되었습니다.",
    )


# 검색·필터·정렬 조건에 맞는 팀 목록을 조회하는 API.
@router.get(
    "/teams",
    response_model=APIResponse[list[TeamListItemResponse]],
    status_code=status.HTTP_200_OK,
    summary="Challenge 팀 목록 조회",
)
def get_teams(
    quest_id: int | None = Query(
        default=None,
        gt=0,
        description="조회할 퀘스트 ID",
    ),

    team_status: TeamStatus | None = Query(
        default=TeamStatus.RECRUITING,
        alias="status",
        description="조회할 팀 상태",
    ),

    is_public: bool | None = Query(
        default=None,
        description="팀 공개 여부",
    ),

    region: str | None = Query(
        default=None,
        max_length=100,
        description="팀 활동 지역",
    ),

    search: str | None = Query(
        default=None,
        max_length=100,
        description="검색할 팀 이름",
    ),

    # 팀 목록의 정렬 순서를 지정.
    sort_by: Literal[
        "latest",
        "oldest",
        "name",
    ] = Query(
        default="latest",
        description="정렬 방식: latest, oldest, name",
    ),

    page: int = Query(
        default=1,
        ge=1,
        description="조회할 페이지 번호",
    ),

    size: int = Query(
        default=20,
        ge=1,
        le=100,
        description="한 페이지에서 조회할 팀 개수",
    ),

    session: Session = Depends(get_db),
) -> APIResponse[list[TeamListItemResponse]]:
    """조건에 맞는 Challenge 팀 목록을 조회합니다."""

    # Service에서 팀 객체와 각 팀의 현재 참가 인원을 함께 조회.
    team_rows = ChallengeTeamService.get_teams(
        session,
        quest_id=quest_id,
        team_status=team_status,
        is_public=is_public,
        region=region,
        search=search,
        sort_by=sort_by,
        page=page,
        size=size,
    )

    # Team 객체와 현재 참가 인원을 목록 응답 Schema로 변환.
    response_data = [
        TeamListItemResponse(
            **TeamResponse.model_validate(
                team
            ).model_dump(),
            current_members=current_members,
        )
        for team, current_members in team_rows
    ]

    return APIResponse.ok(
        data=response_data,
        message="팀 목록을 성공적으로 조회했습니다.",
    )


# 현재 로그인 사용자가 참가 중인 팀 목록을 조회하는 API.
@router.get(
    "/my-teams",
    response_model=APIResponse[list[TeamListItemResponse]],
    status_code=status.HTTP_200_OK,
    summary="내가 참여 중인 Challenge 팀 목록 조회",
)
def get_my_teams(
    team_status: TeamStatus | None = Query(
        default=None,
        alias="status",
        description="조회할 팀 상태",
    ),

    page: int = Query(
        default=1,
        ge=1,
        description="조회할 페이지 번호",
    ),

    size: int = Query(
        default=20,
        ge=1,
        le=100,
        description="한 페이지에서 조회할 팀 개수",
    ),

    session: Session = Depends(get_db),

    # 인증 Dependency에서 현재 로그인 사용자 정보를 주입.
    current_user: User = Depends(
        get_current_db_user
    ),
) -> APIResponse[list[TeamListItemResponse]]:

    # 현재 로그인 사용자의 ID를 기준으로 참가 팀 목록을 조회.
    team_rows = ChallengeTeamService.get_my_teams(
        session,
        current_user=current_user,
        team_status=team_status,
        page=page,
        size=size,
    )

    # Team 객체와 현재 참가 인원을 목록 응답 Schema로 변환.
    response_data = [
        TeamListItemResponse(
            **TeamResponse.model_validate(
                team
            ).model_dump(),
            current_members=current_members,
        )
        for team, current_members in team_rows
    ]

    return APIResponse.ok(
        data=response_data,
        message="참여 중인 팀 목록을 성공적으로 조회했습니다.",
    )

# 공개 또는 비공개 Challenge 팀에 참가하는 API.
@router.post(
    "/teams/{team_id}/join",
    response_model=APIResponse[TeamMemberResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Challenge 팀 참가",
)
def join_team(
    team_id: int,

    # 공개 팀은 Body를 생략할 수 있고,
    # 비공개 팀은 비밀번호를 Body로 전달.
    password_data: TeamPasswordVerify | None = None,

    session: Session = Depends(get_db),

    current_user: User = Depends(
        get_current_db_user
    ),
) -> APIResponse[TeamMemberResponse]:
    # 요청 Body가 없으면 공개 팀 참가이므로 비밀번호를 None으로 설정.
    password = (
        password_data.password
        if password_data is not None
        else None
    )

    # Service에서 참가 상태, 정원, 중복 참가 및 비밀번호를 검사.
    member = ChallengeTeamService.join_team(
        session,
        team_id=team_id,
        password=password,
        current_user=current_user,
    )

    # 생성된 TeamMember 객체를 응답 Schema로 변환.
    response_data = TeamMemberResponse.model_validate(
        member
    )

    # 팀 참가 결과를 공통 API 응답 형식으로 반환.
    return APIResponse.ok(
        data=response_data,
        message="팀에 성공적으로 참가했습니다.",
    )


# 현재 로그인 사용자가 참가 중인 팀에서 나가는 API.
@router.delete(
    "/teams/{team_id}/leave",
    response_model=APIResponse[None],
    status_code=status.HTTP_200_OK,
    summary="Challenge 팀 나가기",
)
def leave_team(
    team_id: int,
    session: Session = Depends(get_db),

    current_user: User = Depends(
        get_current_db_user
    ),
) -> APIResponse[None]:
    # Service에서 일반 팀원 나가기 또는 팀장 자동 위임을 처리.
    ChallengeTeamService.leave_team(
        session,
        team_id=team_id,
        current_user=current_user,
    )

    return APIResponse.ok(
        data=None,
        message="팀에서 성공적으로 나갔습니다.",
    )


# 특정 팀에 참가 중인 전체 멤버를 조회하는 API.
@router.get(
    "/teams/{team_id}/members",
    response_model=APIResponse[
        list[TeamMemberResponse]
    ],
    status_code=status.HTTP_200_OK,
    summary="Challenge 팀 멤버 목록 조회",
)
def get_team_members(
    team_id: int,
    session: Session = Depends(get_db),
) -> APIResponse[list[TeamMemberResponse]]:

    # Service에서 팀 존재 여부를 검사하고 전체 멤버를 조회.
    members = ChallengeTeamService.get_team_members(
        session,
        team_id=team_id,
    )

    # TeamMember ORM 객체를 응답 Schema 목록으로 변환.
    response_data = [
        TeamMemberResponse.model_validate(
            member
        )
        for member in members
    ]

    # 프로젝트의 공통 API 응답 형식으로 팀 멤버 목록을 반환.
    return APIResponse.ok(
        data=response_data,
        message="팀 멤버 목록을 성공적으로 조회했습니다.",
    )


# 특정 팀의 상세 정보와 현재 참가 인원을 조회하는 API.
@router.get(
    "/teams/{team_id}",
    response_model=APIResponse[TeamDetailResponse],
    status_code=status.HTTP_200_OK,
    summary="Challenge 팀 상세 조회",
)
def get_team_detail(
    team_id: int,

    session: Session = Depends(get_db),
) -> APIResponse[TeamDetailResponse]:

    # Service에서 팀 정보와 현재 참가 인원을 함께 조회.
    team, current_members = (
        ChallengeTeamService.get_team_detail(
            session,
            team_id=team_id,
        )
    )

    # Team 객체에 현재 참가 인원을 결합하여 상세 응답 Schema로 변환.
    response_data = TeamDetailResponse(
        **TeamResponse.model_validate(
            team
        ).model_dump(),
        current_members=current_members,
    )

    return APIResponse.ok(
        data=response_data,
        message="팀 상세 정보를 성공적으로 조회했습니다.",
    )