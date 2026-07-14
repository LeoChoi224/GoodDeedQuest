"""
backend/app/shortform/service.py

숏폼 생성 도메인 서비스 레이어.
라우터(엔드포인트)와 models/schemas 사이에서 실제 "비즈니스 로직"을 담당하는 계층.
라우터는 이 파일의 함수들을 호출만 하고, DB 쿼리/외부 API 호출 같은 세부 구현은
전부 여기에 모아둔다 (테스트/재사용 용이하게 하기 위함).

포함 기능:
- ShortForm 생성 (수동 선곡 / RAG 자동 매칭)
- S3 Presigned URL 발급 (업로드용 / 조회용)
- Celery 태스크 큐잉 (AI 파이프라인 트리거)
- ShortForm.status 직접 DB 업데이트
- AI 대본 생성 팝업 플로우: 대본 생성 / 수정 검증

TODO: ForeignKey('User.user_id') → 팀원 User 모델 확정 후 snake_case 테이블명으로 정정
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional

import boto3
import httpx
from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound

from app.shortform.models import ShortForm, BackgroundMusic, ShortFormStatus
from app.shortform.schemas import (
    ShortFormCreateRequest,
    ScriptGenerateRequest,
    ScriptGenerateResponse,
    ScriptUpdateRequest,
    ShortFormStatusRead,
    CaptionItem,
)
from app.core.config import settings  # AWS_REGION, S3_BUCKET_NAME, AI_SERVER_URL 등 환경설정
from app.shortform.tasks import render_shortform_task  # Celery task, tasks.py에 정의 가정


# ---------------------------------------------------------------------------
# S3 클라이언트 & Presigned URL
#
# Presigned URL: S3 접근 권한을 임시로 부여하는 서명된 URL.
# 서버가 파일을 직접 주고받지 않고, 클라이언트(RN 앱)가 이 URL로 S3에
# 직접 업로드/다운로드하게 해서 서버 부하를 줄이는 방식.
# ---------------------------------------------------------------------------

# boto3 S3 클라이언트는 모듈 로드 시 한 번만 생성해서 재사용 (매 요청마다 새로 만들지 않음)
_s3_client = boto3.client(
    "s3",
    region_name=settings.AWS_REGION,
)

PRESIGNED_UPLOAD_EXPIRE_SECONDS = 300      # 5분 - 업로드용은 짧게 (클라이언트가 바로 씀)
PRESIGNED_DOWNLOAD_EXPIRE_SECONDS = 3600   # 1시간 - 조회용은 폴링/재생 도중 만료되지 않도록 여유


def generate_upload_presigned_url(s3_key: str, content_type: str) -> str:
    """
    클라이언트가 직접 S3에 파일을 업로드할 수 있도록 presigned PUT URL 발급.
    (배경음악 업로드, 최종 영상 업로드 등에 사용)

    Args:
        s3_key: 업로드될 S3 객체 키 (예: "shortform/{shortform_id}/output.mp4")
        content_type: 업로드할 파일의 MIME 타입 (예: "video/mp4")
    """
    return _s3_client.generate_presigned_url(
        ClientMethod="put_object",
        Params={
            "Bucket": settings.S3_BUCKET_NAME,
            "Key": s3_key,
            "ContentType": content_type,
        },
        ExpiresIn=PRESIGNED_UPLOAD_EXPIRE_SECONDS,
    )


def generate_download_presigned_url(s3_key: str) -> str:
    """
    저장된 s3_key를 실제 조회 가능한 presigned GET URL로 변환.
    ShortForm.final_video_s3_key, BackgroundMusic.s3_key 등 DB에는 key만 저장되어 있으므로,
    API 응답(schemas의 video_url, preview_url)으로 내려주기 직전에 이 함수로 변환한다.
    """
    return _s3_client.generate_presigned_url(
        ClientMethod="get_object",
        Params={
            "Bucket": settings.S3_BUCKET_NAME,
            "Key": s3_key,
        },
        ExpiresIn=PRESIGNED_DOWNLOAD_EXPIRE_SECONDS,
    )


# ---------------------------------------------------------------------------
# BGM 자동 매칭 (RAG) - 자동 생성 경로 전용
# ---------------------------------------------------------------------------

def _resolve_bgm_id_for_auto_mode(db: Session, request: ShortFormCreateRequest) -> str:
    """
    request.bgm_id가 None으로 온 자동 생성 경로에서 호출.
    RAG 기반 무드 매칭 결과로 bgm_id를 채워서 반환한다.
    ShortForm.bgm_id는 NOT NULL 컬럼이므로, insert 전에 반드시 값이 확정되어야 함
    (그래서 create_shortform 안에서 insert 직전에 이 함수를 호출).

    실제 RAG 매칭 로직(LangChain RAG Agent 호출: 사용자가 선택한 이미지의 무드를
    벡터화해서 BackgroundMusic의 mood_tag와 유사도 비교)은 AI 파이프라인 구현
    단계에서 별도 모듈(예: app.shortform.ai.bgm_matcher)로 분리할 예정.
    지금은 서비스 레이어에서 이 함수를 호출하는 "자리"만 먼저 확보해둔 상태.
    """
    # TODO: RAG Agent 연동 (무드 벡터 검색 → 최적 BGM 매칭)으로 아래 쿼리 대체
    # 임시 fallback: 가장 최근에 등록된 BGM 하나를 그냥 가져옴 (실제 매칭 로직 아님)
    matched_bgm = (
        db.query(BackgroundMusic)
        .order_by(BackgroundMusic.created_at.desc())
        .first()
    )
    if matched_bgm is None:
        # BGM이 하나도 없는 극단적인 케이스 (seed 데이터 누락 등) 방어
        raise NoResultFound("자동 매칭 가능한 BackgroundMusic이 존재하지 않습니다.")
    return matched_bgm.bgm_id


# ---------------------------------------------------------------------------
# ShortForm 생성
# ---------------------------------------------------------------------------

def create_shortform(
    db: Session,
    user_id: str,
    request: ShortFormCreateRequest,
) -> ShortForm:
    """
    ShortForm row를 PENDING 상태로 생성.

    주의: 선택된 미디어(media_keys)는 이 시점에 DB에 저장하지 않는다.
    ERD에 ShortFormMedia 같은 junction 테이블이 없기 때문에, media_keys는
    이후 큐잉 단계(queue_shortform_generation)에서 Celery 태스크 파라미터로만
    전달되는 ephemeral(휘발성) 데이터로 취급한다.
    """
    bgm_id = request.bgm_id
    if bgm_id is None:
        # 사용자가 BGM을 직접 고르지 않은 "자동 생성" 경로 → RAG 매칭으로 채움
        bgm_id = _resolve_bgm_id_for_auto_mode(db, request)

    shortform = ShortForm(
        shortform_id=str(uuid.uuid4()),  # PK는 서버에서 UUID로 미리 생성 (오토인크리먼트 X)
        user_id=user_id,
        bgm_id=bgm_id,
        status=ShortFormStatus.PENDING,  # 생성 직후엔 항상 PENDING, 아직 아무 작업도 시작 안 함
        created_at=datetime.utcnow(),
    )
    db.add(shortform)
    db.commit()
    db.refresh(shortform)  # commit 이후 DB가 채워준 값(예: 트리거로 생성되는 컬럼)을 다시 읽어옴
    return shortform


# ---------------------------------------------------------------------------
# 상태 업데이트 (직접 DB write, Redis 불필요)
#
# 상태 전이가 한 작업당 최대 3~4번(PENDING→GENERATING→COMPLETED/FAILED)뿐이라
# 별도 캐시 레이어 없이 DB에 바로 쓰고 바로 읽어도 충분하다고 판단함.
# ---------------------------------------------------------------------------

def update_shortform_status(
    db: Session,
    shortform_id: str,
    status: ShortFormStatus,
    final_video_s3_key: Optional[str] = None,
    error_message: Optional[str] = None,
) -> ShortForm:
    """
    PENDING → GENERATING → COMPLETED / FAILED 상태 전이를 직접 DB에 반영.
    Celery 워커(render_shortform_task)가 파이프라인 각 단계에 진입/완료할 때마다 호출.

    Args:
        final_video_s3_key: COMPLETED로 바뀔 때만 값을 넘겨서 함께 저장
        error_message: FAILED로 바뀔 때 실패 사유를 남기기 위함 (프론트 에러 표시용)
    """
    shortform = (
        db.query(ShortForm)
        .filter(ShortForm.shortform_id == shortform_id)
        .one()  # 없으면 예외 발생 (호출부에서 shortform_id 존재를 이미 보장했다는 전제)
    )
    shortform.status = status
    if final_video_s3_key is not None:
        shortform.final_video_s3_key = final_video_s3_key
    if error_message is not None:
        shortform.error_message = error_message
    shortform.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(shortform)
    return shortform


def get_shortform_status(db: Session, shortform_id: str) -> ShortFormStatusRead:
    """
    프론트엔드가 생성 진행 상황을 확인하기 위해 주기적으로(폴링) 호출하는 조회 함수.

    video_url은 DB 컬럼이 아니라 API 응답 전용 필드(schemas.py 참고) — 저장된
    s3_key를 매 요청마다 즉석에서 presigned URL로 변환해서 내려준다. COMPLETED
    상태가 아니면 아직 영상이 없으므로 불필요한 S3 호출을 하지 않고 None 반환.
    """
    shortform = (
        db.query(ShortForm)
        .filter(ShortForm.shortform_id == shortform_id)
        .one()
    )
    video_url = None
    if shortform.status == ShortFormStatus.COMPLETED and shortform.final_video_s3_key:
        video_url = generate_download_presigned_url(shortform.final_video_s3_key)

    return ShortFormStatusRead(
        shortform_id=shortform.shortform_id,
        status=shortform.status,
        video_url=video_url,
        error_message=shortform.error_message,
    )


# ---------------------------------------------------------------------------
# Celery 태스크 큐잉 (AI 파이프라인 트리거)
# ---------------------------------------------------------------------------

def queue_shortform_generation(
    db: Session,
    shortform_id: str,
    media_keys: list[str],
    captions: list[CaptionItem],
) -> None:
    """
    사용자가 팝업에서 대본(캡션)을 최종 확정하고 "생성하기"를 누르면 호출.

    media_keys, captions는 DB에 저장하지 않고 Celery 태스크 파라미터로만
    전달한다 (ShortFormMedia 같은 junction 테이블이 없으므로). 태스크 큐잉과
    동시에 상태를 GENERATING으로 바꿔서, 사용자가 중복으로 "생성하기"를
    다시 누르지 못하게 프론트에서 막을 수 있는 신호를 준다.
    """
    update_shortform_status(db, shortform_id, ShortFormStatus.GENERATING)

    # .delay()는 Celery 태스크를 비동기 큐에 등록만 하고 즉시 리턴한다.
    # 실제 렌더링(Vision/RAG/Story/Validation/FFmpeg Agent 체인)은 워커 프로세스에서 처리.
    render_shortform_task.delay(
        shortform_id=shortform_id,
        media_keys=media_keys,
        captions=[c.model_dump() for c in captions],  # Pydantic 모델 → dict (Celery 직렬화용)
    )


# ---------------------------------------------------------------------------
# AI 대본 생성 팝업 (스토리보드 화면 - AI 대본 생성 팝업 기능)
#
# 설계 전제: 캡션(대본) 수정본은 DB/캐시에 저장하지 않는다.
# 프론트엔드가 팝업이 열려있는 동안 캡션 상태를 자체적으로 들고 있다가,
# 사용자가 최종 "생성하기"를 누르는 시점에만 queue_shortform_generation()의
# captions 파라미터로 한 번에 전달한다. 따라서 아래 두 함수는 모두
# stateless이며 DB에 쓰기 작업을 하지 않는다 (조회는 필요 시에만 수행).
# ---------------------------------------------------------------------------

AI_SCRIPT_GENERATE_TIMEOUT_SECONDS = 30.0
MAX_CAPTION_COUNT = 20          # 30초 영상 기준 상한 (자막이 너무 많으면 화면이 복잡해짐 방지)
MAX_CAPTION_TEXT_LENGTH = 40    # 9:16 세로 화면에서 한 줄로 표시 가능한 대략적인 글자 수 상한


def generate_ai_script(
    db: Session,
    shortform_id: str,
    request: ScriptGenerateRequest,
) -> ScriptGenerateResponse:
    """
    스토리보드 화면에서 'AI 대본 생성' 팝업을 처음 열 때 호출.

    Vision Agent(이미지 분석) → RAG Agent(비슷한 사례 검색) → LLM Story Agent(대본 작성)
    체인은 이 백엔드가 아니라 별도 AI 서버가 담당한다. 여기서는:
      1) AI 서버에 HTTP로 요청을 던지고
      2) 응답받은 캡션 데이터를 CaptionItem 스키마로 변환/검증만 한다

    결과는 DB에 저장하지 않고 응답으로만 내려준다. (프론트가 이 응답을
    팝업 상태로 들고 있다가 사용자가 직접 수정하는 흐름)
    """
    # shortform이 실제로 존재하는지 먼저 확인 (없는 ID로 AI 서버 호출 낭비 방지)
    shortform = (
        db.query(ShortForm)
        .filter(ShortForm.shortform_id == shortform_id)
        .one()
    )

    payload = {
        "shortform_id": shortform_id,
        "media_keys": request.media_keys,
        "mood_tag": request.mood_tag,
    }

    try:
        response = httpx.post(
            f"{settings.AI_SERVER_URL}/generate-script",
            json=payload,
            timeout=AI_SCRIPT_GENERATE_TIMEOUT_SECONDS,
        )
        response.raise_for_status()  # 4xx/5xx면 예외 발생시켜 아래 except로 이동
    except httpx.HTTPError as exc:
        # AI 서버 호출 자체가 실패한 경우 (타임아웃, 서버 다운 등)
        # ShortForm.status를 FAILED로 남겨서, 폴링 중인 프론트가 팝업에서
        # "다시 시도" UI를 띄울 수 있게 한다.
        update_shortform_status(
            db,
            shortform_id,
            ShortFormStatus.FAILED,
            error_message=f"AI 대본 생성 서버 호출 실패: {exc}",
        )
        raise  # 라우터에서 적절한 HTTP 에러 응답으로 변환하도록 다시 던짐

    ai_result = response.json()
    # AI 서버 응답의 각 캡션 dict를 CaptionItem 객체로 변환 (타입 검증 겸함)
    captions = [
        CaptionItem(**caption_raw) for caption_raw in ai_result.get("captions", [])
    ]
    _validate_captions(captions)  # 개수/길이 제약 검증 (수정 검증 함수와 로직 공유)

    return ScriptGenerateResponse(
        shortform_id=shortform_id,
        captions=captions,
    )


def validate_edited_captions(request: ScriptUpdateRequest) -> ScriptGenerateResponse:
    """
    사용자가 팝업에서 AI가 생성한 캡션을 직접 수정했을 때 호출하는 "검증 전용" 함수.
    이름 그대로 저장(update)이 아니라 validate이다 — DB에는 아무것도 쓰지 않는다.

    프론트가 팝업을 닫지 않고 계속 편집하는 동안, 텍스트를 고칠 때마다(또는
    "다음" 버튼을 누를 때) 이 함수를 호출해서 규칙 위반 여부를 즉시 알려주는
    용도로 사용한다. 실제 최종 반영은 사용자가 "생성하기"를 눌러
    queue_shortform_generation()이 호출될 때 한 번만 일어난다.
    """
    _validate_captions(request.captions)
    return ScriptGenerateResponse(
        shortform_id=request.shortform_id,
        captions=request.captions,
    )


def _validate_captions(captions: list[CaptionItem]) -> None:
    """
    캡션 리스트 공통 검증 로직. generate_ai_script / validate_edited_captions
    양쪽에서 재사용하기 위해 private 헬퍼로 분리함 (내부 전용이라 _ 접두사).
    """
    if not captions:
        raise ValueError("캡션이 최소 1개 이상 필요합니다.")
    if len(captions) > MAX_CAPTION_COUNT:
        raise ValueError(
            f"캡션은 최대 {MAX_CAPTION_COUNT}개까지 허용됩니다. (현재 {len(captions)}개)"
        )
    for caption in captions:
        if len(caption.text) > MAX_CAPTION_TEXT_LENGTH:
            # 에러 메시지에 캡션 앞부분만 잘라서 보여줘서 어떤 캡션이 문제인지 식별 가능하게 함
            raise ValueError(
                f"캡션 텍스트는 {MAX_CAPTION_TEXT_LENGTH}자를 초과할 수 없습니다: "
                f"'{caption.text[:20]}...'"
            )