from __future__ import annotations

# =========================================================
# [반드시 확인 및 검토할 사항]
#
# 1. 공통 JWT 인증 사용
#    - JWT 생성/검증은 backend.app.common.auth 에서만 관리합니다.
#    - Admin에서는 JWT를 다시 해석하지 않습니다.
#
# 2. 현재 로그인 사용자 조회
#    - verify_token()이 반환하는 이메일(sub)을 이용하여 User를 조회합니다.
#
# 3. 관리자 권한 확인
#    - 로그인 여부
#    - 활성 계정 여부(is_active)
#    - ADMIN 권한 여부(role)
#    위 3가지를 모두 통과해야 Admin API 접근이 가능합니다.
#
# 4. 로그인 구조가 변경되더라도
#    - common.auth.verify_token()만 수정하면
#      Admin 코드는 그대로 사용할 수 있습니다.
# =========================================================

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.auth.models import User
from backend.app.auth.enums import UserRole
from backend.app.common.auth import (
    oauth2_scheme,
    verify_token,
)
from backend.app.common.database import get_db

# 인증 실패 시 공통으로 사용할 Exception을 생성.
def _credentials_exception() -> HTTPException:

    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="로그인이 필요하거나 인증 정보가 올바르지 않습니다.",
        headers={
            "WWW-Authenticate": "Bearer",
        },
    )


# 현재 로그인한 사용자를 조회.
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Access Token을 검증하고
    현재 로그인한 User를 반환합니다.
    """

    # Access Token이 존재하지 않으면 인증 실패 처리.
    if not token:
        raise _credentials_exception()

    try:
        email = verify_token(token)

    except Exception:
        raise _credentials_exception()

    # 이메일로 현재 로그인한 사용자를 조회.
    result = await db.execute(
        select(User).where(
            User.email == email,
        )
    )

    current_user = result.scalar_one_or_none()

    # DB에 사용자가 없으면 인증 실패 처리.
    if current_user is None:
        raise _credentials_exception()

    return current_user


# 현재 로그인한 사용자가 관리자 권한인지 확인.
async def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:

    # 비활성 계정은 관리자 기능을 사용할 수 없습니다.
    if current_user.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성 계정입니다.",
        )

    # ADMIN 권한이 아니면 접근을 차단.
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다.",
        )

    return current_user