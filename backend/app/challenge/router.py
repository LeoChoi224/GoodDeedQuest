from __future__ import annotations

# =========================================================
# [Challenge Router 구현 기준]
#
# 1. 주요 API
#    - POST   /challenges/teams
#    - GET    /challenges/teams
#    - GET    /challenges/my-teams
#    - GET    /challenges/teams/{team_id}
#    - GET    /challenges/teams/{team_id}/members
#    - GET    /challenges/teams/{team_id}/recommendations
#    - POST   /challenges/teams/{team_id}/join
#    - DELETE /challenges/teams/{team_id}/leave
#    - POST   /challenges/invites
#    - GET    /challenges/my-invites
#    - PATCH  /challenges/invites/{invite_id}
#
# 2. 인증 정책
#    - 팀 목록·상세·멤버 목록은 로그인 없이 조회할 수 있습니다.
#    - 팀 생성, 내 팀 조회, 참가, 나가기, 초대 및 초대 응답은
#      로그인 사용자만 사용할 수 있습니다.
#    - AI 팀원 추천은 로그인한 팀장만 요청할 수 있으며,
#      세부 권한과 팀 상태는 ChallengeRecommendationService가 검증합니다.
#
# 3. AI 추천 API
#    - top_k는 1명 이상 5명 이하로 제한합니다.
#    - AI 추천 결과는 TeamRecommendationResponse로 검증해 반환합니다.
#    - 추천 결과의 user_id는 기존 POST /challenges/invites 요청에 사용합니다.
#
# 4. 초대 자동 만료
#    - 초대 목록 조회와 초대 응답 시 만료 상태를 즉시 반영합니다.
#    - Celery Beat가 만료된 PENDING 초대를 정기적으로 처리합니다.
# =========================================================

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import Literal

from backend.app.auth.router import get_current_db_user
from backend.app.auth.models import User
from backend.app.challenge.schema import (
    TeamCreate,
    TeamDetailResponse,
    TeamInviteCreate,
    TeamInviteResponse,
    TeamInviteStatusUpdate,
    TeamListItemResponse,
    TeamMemberResponse,
    TeamPasswordVerify,
    TeamResponse,
    TeamRecommendationResponse,
)
from backend.app.challenge.service import (
    ChallengeRecommendationService,
    ChallengeTeamService,
)
from backend.app.common.database import get_db
from backend.app.common.response import APIResponse
from backend.app.challenge.enums import (
    TeamInviteStatus,
    TeamStatus,
)


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


# 현재 로그인 사용자가 팀장인 팀의 AI 추천 사용자 목록을 조회하는 API.
@router.get(
    "/teams/{team_id}/recommendations",
    response_model=APIResponse[TeamRecommendationResponse],
    status_code=status.HTTP_200_OK,
    summary="Challenge 팀 AI 추천 사용자 목록 조회",
)
def get_team_member_recommendations(
    # 추천 대상 Challenge 팀 ID를 URL 경로로 전달.
    team_id: int,

    # AI 서버에서 반환할 최대 추천 사용자 수를 지정.
    top_k: int = Query(
        default=5,
        ge=1,
        le=5,
        description="반환할 최대 추천 사용자 수",
    ),

    # 직전 추천 결과에서 제외할 사용자 ID를 쉼표로 구분해 전달.
    excluded_user_ids: str | None = Query(
        default=None,
        pattern=r"^[1-9]\d*(,[1-9]\d*){0,4}$",
        description=(
            "직전 추천 결과에서 제외할 사용자 ID. "
            "쉼표로 구분하며 최대 5명까지 전달합니다."
        ),
    ),


    session: Session = Depends(get_db),

    # 인증 Dependency에서 현재 로그인 사용자 정보를 주입.
    current_user: User = Depends(
        get_current_db_user
    ),
) -> APIResponse[TeamRecommendationResponse]:
    """팀장이 현재 팀에 적합한 사용자 추천 목록을 조회합니다."""

    # "3,7,12" 형식의 Query 값을 정수 ID 목록으로 변환.
    parsed_excluded_user_ids = (
        [
            int(user_id)
            for user_id in excluded_user_ids.split(",")
        ]
        if excluded_user_ids
        else []
    )

    # 후보 조회부터 AI 서버 호출까지의 추천 흐름을 Service에 요청.
    recommendations = (
        ChallengeRecommendationService
        .get_team_member_recommendations(
            session,
            team_id=team_id,
            current_user=current_user,
            top_k=top_k,
            excluded_user_ids=parsed_excluded_user_ids,
        )
    )

    # AI 추천 결과를 프로젝트의 공통 응답 형식으로 반환.
    return APIResponse.ok(
        data=recommendations,
        message="팀원 추천 목록을 성공적으로 조회했습니다.",
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


# 현재 로그인 사용자가 팀장인 팀에 특정 사용자를 초대하는 API.
@router.post(
    "/invites",
    response_model=APIResponse[TeamInviteResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Challenge 팀 사용자 직접 초대",
)
def create_team_invite(
    # 초대할 팀 ID, 사용자 ID와 선택적인 만료 시각을 요청 Body로 전달.
    invite_data: TeamInviteCreate,

    session: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_db_user
    ),
) -> APIResponse[TeamInviteResponse]:
    """팀장이 특정 사용자를 자신의 Challenge 팀에 초대합니다."""

    # Service에서 팀장 권한, 팀 상태, 정원과 중복 초대를 검사.
    invite = ChallengeTeamService.create_team_invite(
        session,
        invite_data=invite_data,
        current_user=current_user,
    )

    # 생성되거나 갱신된 TeamInvite 객체를 응답 Schema로 변환.
    response_data = TeamInviteResponse.model_validate(
        invite
    )

    return APIResponse.ok(
        data=response_data,
        message="사용자를 팀에 성공적으로 초대했습니다.",
    )

# 현재 로그인 사용자가 받은 처리 대기 중 초대 목록을 조회하는 API.
@router.get(
    "/my-invites",
    response_model=APIResponse[
        list[TeamInviteResponse]
    ],
    status_code=status.HTTP_200_OK,
    summary="내가 받은 Challenge 팀 초대 목록 조회",
)
def get_my_invites(
    page: int = Query(
        default=1,
        ge=1,
        description="조회할 페이지 번호",
    ),

    size: int = Query(
        default=20,
        ge=1,
        le=100,
        description="한 페이지에서 조회할 초대 개수",
    ),

    session: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_db_user
    ),
) -> APIResponse[list[TeamInviteResponse]]:
    
    # Service에서 만료된 초대를 정리한 후 현재 사용자의 초대를 조회.
    invites = ChallengeTeamService.get_received_invites(
        session,
        current_user=current_user,
        page=page,
        size=size,
    )

    # TeamInvite ORM 객체 목록을 응답 Schema 목록으로 변환.
    response_data = [
        TeamInviteResponse.model_validate(
            invite
        )
        for invite in invites
    ]

    return APIResponse.ok(
        data=response_data,
        message="받은 팀 초대 목록을 성공적으로 조회했습니다.",
    )

# 현재 로그인 사용자가 받은 초대를 수락하거나 거절하는 API.
@router.patch(
    "/invites/{invite_id}",
    response_model=APIResponse[TeamInviteResponse],
    status_code=status.HTTP_200_OK,
    summary="Challenge 팀 초대 수락 또는 거절",
)
def respond_team_invite(
    # 처리할 팀 초대 ID를 URL 경로로 전달.
    invite_id: int,

    # ACCEPTED 또는 REJECTED 상태를 요청 Body로 전달.
    update_data: TeamInviteStatusUpdate,

    session: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_db_user
    ),
) -> APIResponse[TeamInviteResponse]:
    """현재 로그인 사용자가 받은 초대를 수락하거나 거절합니다."""

    # Service에서 초대 소유권과 팀 참가 가능 여부를 검사하고 상태를 변경.
    invite = ChallengeTeamService.respond_team_invite(
        session,
        invite_id=invite_id,
        update_data=update_data,
        current_user=current_user,
    )

    # 처리된 TeamInvite 객체를 응답 Schema로 변환.
    response_data = TeamInviteResponse.model_validate(
        invite
    )

    if update_data.status == TeamInviteStatus.ACCEPTED:
        message = "팀 초대를 성공적으로 수락했습니다."
    else:
        message = "팀 초대를 성공적으로 거절했습니다."

    return APIResponse.ok(
        data=response_data,
        message=message,
    )