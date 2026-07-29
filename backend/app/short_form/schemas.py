"""
선행퀘스트 - AI 숏폼 생성 도메인 Pydantic 스키마

이슈 #6 [숏폼생성] 스토리보드 화면 - AI 대본 생성 팝업 기능 추가 대응.
models.py(SQLAlchemy)에 대응하는 API 요청/응답 스키마.

컨벤션:
- 파일명: snake_case (schemas.py)
- 클래스명: PascalCase
- 필드명: snake_case (프론트에서 camelCase 변환이 필요하면 별도 alias 처리)
"""
from datetime import datetime

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field
from backend.app.short_form.enums import ShortFormStatus

# ─────────────────────────────────────────────
# 공통 Base
# ─────────────────────────────────────────────
class ORMBase(BaseModel):
    """DB 모델 -> 응답 스키마 변환을 위한 공통 설정"""
    model_config = ConfigDict(from_attributes=True)


# ─────────────────────────────────────────────
# BackgroundMusic 스키마
# ─────────────────────────────────────────────
class BackgroundMusicRead(ORMBase):
    """음악 목록/선택 화면에서 사용하는 응답 스키마"""
    bgm_id: int
    title: str
    mood_tag: Optional[str] = None
    source_info: Optional[str] = None
    # s3_key는 그대로 노출하지 않고, 프리사인드 URL로 변환해서 내려줄 필드
    preview_url: Optional[str] = Field(
        default=None,
        description="s3_key로 생성한 presigned URL (서비스 레이어에서 채워 넣음)",
    )


class BackgroundMusicList(BaseModel):
    """무드 필터링된 음악 목록 응답"""
    items: List[BackgroundMusicRead]
    total: int


# ─────────────────────────────────────────────
# AI 대본(캡션) 생성 팝업 관련 스키마 (이슈 #6 핵심)
# ─────────────────────────────────────────────
class CaptionItem(BaseModel):
    """개별 미디어(이미지/클립)에 매칭되는 AI 생성 캡션 한 줄"""
    media_s3_key: str = Field(..., description="원본 인증 이미지/클립의 S3 key")
    order: int = Field(..., ge=0, description="스토리보드 내 노출 순서")
    caption: str = Field(..., max_length=200, description="AI가 생성한(또는 사용자가 수정한) 캡션 텍스트")


class ScriptGenerateRequest(BaseModel):
    """
    [AI 대본 생성 팝업] '생성하기' 클릭 시 요청 바디.
    ShortformMedia 정션 테이블이 없으므로, 선택된 이미지 목록을 직접 전달.
    """
    selected_media_s3_keys: List[str] = Field(
        ..., min_length=1, description="사용자가 선택한 최대 30일치 인증 이미지 S3 key 목록"
    )
    # 제목(ShortForm.title, 영상 자체 제목)은 사용자 입력을 받지 않고 항상 AI(LLM Story Agent)가 생성함
    # ⭐ 수정: quest_title 필드 추가 - ShortForm에 quest_id 연결이 없고(선택 이미지가 여러
    # 퀘스트에 걸쳐 있을 수 있어 역추적으로는 하나로 특정 불가) LLM Story Agent가 자막
    # 프롬프트에 쓰는 "완료한 퀘스트 제목"이라, 프론트가 대본 생성 요청 시 직접 실어 보냄
    quest_title: str = Field(..., max_length=255, description="자막 문구에 들어갈 완료한 퀘스트 제목 (ShortForm.title과는 별개)")


class ScriptGenerateResponse(BaseModel):
    """AI 대본 생성 결과 - 팝업에 표시되어 사용자가 리뷰/수정하게 됨"""
    shorts_id: int
    status: ShortFormStatus
    title: str = Field(..., description="AI가 생성한 숏폼 제목 (팝업에서 캡션과 함께 수정 가능)")
    captions: List[CaptionItem]


class ScriptUpdateRequest(BaseModel):
    """사용자가 팝업에서 제목/캡션을 직접 수정한 뒤 저장할 때 요청 바디"""
    title: str = Field(..., max_length=255)
    captions: List[CaptionItem] = Field(..., min_length=1)


# ─────────────────────────────────────────────
# ShortForm 스키마
# ─────────────────────────────────────────────
class ShortFormCreateRequest(BaseModel):
    """
    숏폼 생성 시작 요청.
    (수동 경로: 대본 팝업 -> 음악 선택 -> ... / 자동 경로: 바로 최종 렌더링)
    """
    # ⭐ 수정: title 필드 추가 - ShortForm.title이 NOT NULL인데 지금까지 요청에 없어서
    # create_shortform()이 title 없이 INSERT를 시도해 IntegrityError가 나던 문제 수정
    title: str = Field(..., max_length=255, description="숏폼 영상 제목 (대본 팝업에서 확정된 제목 또는 사용자 입력)")
    selected_media_s3_keys: List[str] = Field(..., min_length=1)
    bgm_id: Optional[int] = Field(default=None, description="자동 생성(⑥) 경로는 null로 전달, RAG가 자동 매칭")
    ai_generated_captions: Optional[List[CaptionItem]] = None
    is_auto_generated: bool = Field(default=False, description="자동 생성 경로 여부 (음악/대본 팝업 스킵)")


class ShortFormGenerateRequest(BaseModel):
    """
    [영상 생성하기] 버튼 클릭 시 요청 바디.
    사용자가 팝업에서 최종 확정한 media_keys/captions를 큐잉 단계로 전달.
    (ShortFormMedia 정션 테이블이 없으므로 DB 저장 없이 Celery 파라미터로만 사용)
    """
    media_keys: List[str] = Field(..., min_length=1)
    captions: List[CaptionItem] = Field(..., min_length=1)


class ShortFormRead(ORMBase):
    """숏폼 상세 조회/최종 재생 화면 응답"""
    shorts_id: int
    user_id: int
    bgm_id: int
    title: str
    ai_generated_captions: Optional[List[CaptionItem]] = None
    status: ShortFormStatus
    # final_video_s3_key 원본 대신 CDN 재생 URL로 변환해서 내려줌
    video_url: Optional[str] = Field(
        default=None, description="final_video_s3_key 기반 CloudFront URL"
    )
    created_at: datetime
    updated_at: datetime


class ShortFormStatusRead(BaseModel):
    """폴링용 경량 상태 조회 응답 (Celery 진행 상태 확인)"""
    shorts_id: int
    status: ShortFormStatus
    video_url: Optional[str] = None
    error_message: Optional[str] = None