"""
backend/app/background_music/router.py

BGM(배경음악) 목록 조회 도메인 API 라우터.
service.py 함수를 실제 엔드포인트로 노출한다.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.common.database import get_db
from backend.app.auth.router import get_current_db_user
from backend.app.auth.models import User

from backend.app.short_form.schemas import BackgroundMusicList
from backend.app.background_music.service import list_background_music

# prefix="/background-music" -> 아래 모든 엔드포인트 경로 앞에 자동으로 붙음 (예: GET /background-music)
router = APIRouter(prefix="/background-music", tags=["BackgroundMusic"])


@router.get("", response_model=BackgroundMusicList)
def list_background_music_endpoint(
    mood_tag: Optional[str] = Query(
        default=None, description="분위기 태그로 필터링 (예: 신나는, 잔잔한). 생략 시 전체 목록 반환"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_db_user),  # 인증 필수 - 토큰 없으면 401
):
    """
    음악 선택 팝업(스토리보드 화면)에서 BGM 목록을 보여주기 위한 조회 엔드포인트.
    """
    return list_background_music(db, mood_tag)
