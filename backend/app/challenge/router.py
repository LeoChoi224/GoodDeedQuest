from __future__ import annotations

# =========================================================
# [반드시 확인 및 검토할 사항]
#
# 1. 팀 생성 API 주소는 다음과 같습니다.
#    - POST /challenges/teams
#
# 2. 로그인 사용자 확인은 auth/router.py의 get_current_db_user 의존성을 재사용합니다.
#    - Authorization 헤더에 Bearer 액세스 토큰이 필요합니다. (추후 확인 필요)
# =========================================================

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.app.auth.router import get_current_db_user
from backend.app.auth.models import User
from backend.app.challenge.schema import (
    TeamCreate,
    TeamResponse,
)
from backend.app.challenge.service import ChallengeTeamService
from backend.app.common.database import get_db
from backend.app.common.response import APIResponse


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