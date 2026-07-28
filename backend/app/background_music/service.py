"""
backend/app/background_music/service.py

BGM(BackgroundMusic) 목록 조회 도메인 서비스 레이어.
BackgroundMusic 모델은 short_form 도메인에 정의되어 있으므로(정션 테이블 없이
short_form.bgm_id가 이 테이블을 그대로 참조) 별도로 복제하지 않고 그대로 재사용한다.
"""

from typing import Optional

from sqlalchemy.orm import Session

from backend.app.short_form.models import BackgroundMusic
from backend.app.short_form.schemas import BackgroundMusicList, BackgroundMusicRead
from backend.app.common.s3_client import generate_download_presigned_url


def list_background_music(db: Session, mood_tag: Optional[str] = None) -> BackgroundMusicList:
    """
    음악 선택 팝업(스토리보드 화면)에서 쓰는 BGM 전체 목록 조회.
    mood_tag가 주어지면 해당 무드 태그와 정확히 일치하는 BGM만 필터링한다
    (예: "신나는", "잔잔한" 등 - short_form AI 파이프라인의 MOOD_TAG_VOCAB과 동일한 값 기준).
    """
    query = db.query(BackgroundMusic)
    if mood_tag is not None:
        query = query.filter(BackgroundMusic.mood_tag == mood_tag)

    bgms = query.order_by(BackgroundMusic.created_at.desc()).all()

    items = [
        BackgroundMusicRead(
            bgm_id=bgm.bgm_id,
            title=bgm.title,
            mood_tag=bgm.mood_tag,
            source_info=bgm.source_info,
            # s3_key는 그대로 노출하지 않고, 매 조회마다 presigned URL로 변환해서 내려줌
            preview_url=generate_download_presigned_url(bgm.s3_key),
        )
        for bgm in bgms
    ]
    return BackgroundMusicList(items=items, total=len(items))
