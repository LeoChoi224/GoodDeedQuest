"""
backend/app/short_form/service.py

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
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx
from fastapi import HTTPException  # ⭐ 수정: AI 서버 타임아웃/장애를 502/504로 명확히 응답하기 위해 추가
from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound  # .one() 조회 시 결과가 없으면 발생하는 예외 (라우터에서 404로 변환 예정)

from backend.app.common.datetime_utils import to_utc_aware  # ⭐ 수정: 퀘스트 완료시간 KST 표시 버그 수정
from backend.app.short_form.models import ShortForm, BackgroundMusic, ShortFormStatus
from backend.app.short_form.schemas import (
    ShortFormCreateRequest,
    ScriptGenerateRequest,
    ScriptGenerateResponse,
    ScriptUpdateRequest,
    ShortFormStatusRead,
    CaptionItem,
    EligibleMediaItem,
)

from backend.app.common.config import get_setting  # DATABASE_URL, AI_SERVICE_URL 등 환경설정 (.env 기반)
from backend.app.common.s3_client import (
    generate_upload_presigned_url,
    generate_download_presigned_url,
    get_video_thumbnail_key,
)  # S3 presigned URL 발급 함수 (공용 모듈로 분리됨 - 다른 도메인도 재사용)

# 사진 선택 화면용 인증 이미지 조회 대상 테이블. community 도메인과 조회 대상은
# 같지만 용도(숏폼 소재 선택)가 달라 쿼리 로직은 이 도메인 안에서 독립적으로 작성한다
# (community.repository의 함수를 import해서 재사용하지 않음).
from backend.app.quest_verification.enums import SubmissionStatus, MediaType
from backend.app.quest_verification.models import QuestSubmission

from backend.app.short_form.tasks import render_shortform_task  # Celery task, tasks.py에 정의 가정

# ⭐ 수정: uuid import 제거 (shorts_id는 autoincrement라 더 이상 수동 생성 안 함)

# ⭐ 수정: settings 미정의(NameError) 수정 - get_setting()만 import하고 settings.AI_SERVICE_URL로
# 참조하던 버그. 모듈 레벨에서 한 번 호출해서 settings로 바인딩.
settings = get_setting()

# ---------------------------------------------------------------------------
# 사진 선택 화면 - 숏폼 소재로 쓸 수 있는 인증 이미지 조회
#
# community 도메인의 GET /community/quest-submissions/recent와 조회 대상
# 테이블(QuestSubmission)은 같지만, 커뮤니티 게시글 작성용과 숏폼 소재 선택용은
# 목적이 다르고 향후 응답 형태가 갈라질 수 있어 독립적인 쿼리로 분리해둔다.
# ---------------------------------------------------------------------------

ELIGIBLE_MEDIA_MAX_DAYS = 30  # ScriptGenerateRequest.selected_media_s3_keys 문서상 "최대 30일치"와 동일한 기준


# ⭐ 수정: QuestSubmission.media_url을 항상 S3 key로 가정하고 무조건 presign하면,
# 이미 완전한 URL로 저장된 값(레거시/외부 데이터 등)을 만났을 때 잘못된 key로
# 서명된 URL이 만들어져 썸네일이 투명하게(로드 실패) 보이는 버그가 있었다.
# community/service.py의 _to_download_url, admin/service.py의 동일 패턴과 맞춰
# 이미 http(s)://로 시작하면 그대로 두고, 아니면 presign하도록 가드를 추가한다.
def _to_thumbnail_url(stored_media_url: str) -> str:
    if stored_media_url.startswith(("http://", "https://")):
        return stored_media_url
    return generate_download_presigned_url(stored_media_url)


def get_eligible_media(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 20,
) -> list[EligibleMediaItem]:
    """
    사진 선택 화면(그리드)에서 숏폼 소재로 고를 수 있는, 최근 30일 내
    승인된 퀘스트 인증 제출의 이미지 목록을 반환한다.

    media_url은 썸네일 표시용으로 매 조회마다 즉석에서 발급하는 presigned URL,
    media_s3_key는 이후 /shortforms 생성 요청(selected_media_s3_keys)에
    그대로 넘길 원본 S3 key다.

    ⭐ 수정: GOOD_DEED 퀘스트는 대표 증빙이 동영상이라 그대로는 이미지 소재로 쓸 수
    없었는데, 제외하는 대신 대표 프레임 1장을 뽑아 이미지로 등록해 소재 후보에
    포함시킨다(get_video_thumbnail_key). 보조 사진(extra_media_urls)도 실제로는
    사진 파일이라 함께 풀어서 각각 별도 항목으로 반환한다 - 제출 1건이 여러 장의
    선택 가능한 사진으로 이어질 수 있으므로, 화면에서는 submission_id가 아니라
    media_s3_key가 각 항목의 고유 식별자가 된다.
    """
    submitted_after = datetime.now(timezone.utc) - timedelta(days=ELIGIBLE_MEDIA_MAX_DAYS)

    submissions = (
        db.query(QuestSubmission)
        .filter(
            QuestSubmission.user_id == user_id,
            QuestSubmission.final_status == SubmissionStatus.ACCEPTED,
            QuestSubmission.submitted_at >= submitted_after,
        )
        .order_by(
            QuestSubmission.submitted_at.desc(),
            QuestSubmission.submission_id.desc(),
        )
        .offset(skip)
        .limit(limit)
        .all()
    )

    items: list[EligibleMediaItem] = []
    for submission in submissions:
        # ⭐ 수정: 프론트가 "동영상에서 뽑은 대표 프레임" 항목을 사진과 구분해서 배지로
        # 보여줄 수 있도록, 키마다 원본이 동영상이었는지(is_video)를 함께 들고 다닌다.
        photo_keys: list[tuple[str, bool]] = []

        if submission.media_url:
            if submission.media_type == MediaType.VIDEO:
                try:
                    photo_keys.append((get_video_thumbnail_key(submission.media_url), True))
                except Exception as error:
                    print(
                        f"동영상 썸네일 추출 실패(해당 제출은 소재 목록에서 제외): "
                        f"submission_id={submission.submission_id} {type(error).__name__}: {error}"
                    )
            else:
                photo_keys.append((submission.media_url, False))

        photo_keys.extend((key, False) for key in (submission.extra_media_urls or []))

        for key, is_video in photo_keys:
            items.append(
                EligibleMediaItem(
                    submission_id=submission.submission_id,
                    quest_id=submission.quest_id,
                    media_url=_to_thumbnail_url(key),
                    media_s3_key=key,
                    is_video=is_video,
                    submitted_at=to_utc_aware(submission.submitted_at),  # ⭐ 수정: naive UTC -> UTC-aware로 내려서 프론트가 KST로 정확히 변환하게 함
                )
            )

    return items


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
    # ⚠️ 주의: 지금은 사용자가 선택한 이미지 무드와 무관하게 항상 같은 결과가 나옴
    matched_bgm = (
        db.query(BackgroundMusic)
        .order_by(BackgroundMusic.created_at.desc())  # 최신 등록순 정렬 → 첫 번째가 가장 최근 것
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
    user_id: int,
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
    # bgm_id가 None이 아니면(=사용자가 수동으로 골랐으면) 그대로 사용, 별도 검증 없음

    # ⭐ 수정: shorts_id는 models.py 기준 Integer autoincrement PK라 직접 값을 넣지 않음
    shortform = ShortForm(
        user_id=user_id,
        bgm_id=bgm_id,
        title=request.title,  # ⭐ 수정: title 컬럼이 NOT NULL인데 누락되어 IntegrityError가 나던 부분 - 요청 값 그대로 사용
        status=ShortFormStatus.PENDING,  # 생성 직후엔 항상 PENDING, 아직 아무 작업도 시작 안 함
        created_at=datetime.now(timezone.utc),
    )
    db.add(shortform)     # 세션에 등록 (아직 DB에 반영 안 됨)
    db.commit()            # 실제 DB에 INSERT 실행
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
    shorts_id: int,  # ⭐ 수정: shortform_id(str) → shorts_id(int)
    status: ShortFormStatus,
    final_video_s3_key: Optional[str] = None,
    error_message: Optional[str] = None,
) -> ShortForm:
    """
    PENDING → GENERATING → COMPLETED / FAILED 상태 전이를 직접 DB에 반영.
    Celery 워커(render_shortform_task)가 파이프라인 각 단계에 진입/완료할 때마다 호출.

    Args:
        final_video_s3_key: COMPLETED로 바뀔 때만 값을 넘겨서 함께 저장
        error_message: FAILED로 바뀔 때만 저장되며, 그 외 상태로 전이 시
            이전에 남아있던 실패 메시지는 자동으로 초기화된다.
    """
    shortform = (
        db.query(ShortForm)
        .filter(ShortForm.shorts_id == shorts_id)  # ⭐ 수정: 컬럼명 shorts_id로 변경
        .one()  # 없으면 예외 발생 (호출부에서 shorts_id 존재를 이미 보장했다는 전제)
    )
    shortform.status = status

    # final_video_s3_key는 COMPLETED 전이 시에만 넘어오므로, 그 외 호출에서는
    # None으로 넘어와 기존 값을 건드리지 않고 그대로 둠
    if final_video_s3_key is not None:
        shortform.final_video_s3_key = final_video_s3_key

    # ⚠️ 이 부분이 핵심: error_message는 파라미터 유무가 아니라 "지금 바뀌는 상태가
    # FAILED인지 아닌지"로 판단한다. 그래야 재시도가 성공(COMPLETED)했을 때
    # 이전 실패 시도에서 남아있던 에러 메시지가 그대로 남아있는 버그를 막을 수 있음.
    if status == ShortFormStatus.FAILED:
        shortform.error_message = error_message
    else:
        shortform.error_message = None  # FAILED가 아니면 항상 초기화

    shortform.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(shortform)
    return shortform


def get_shortform_status(db: Session, shorts_id: int) -> ShortFormStatusRead:  # ⭐ 수정: shortform_id(str) → shorts_id(int)
    """
    프론트엔드가 생성 진행 상황을 확인하기 위해 주기적으로(폴링) 호출하는 조회 함수.

    video_url은 DB 컬럼이 아니라 API 응답 전용 필드(schemas.py 참고) — 저장된
    s3_key를 매 요청마다 즉석에서 presigned URL로 변환해서 내려준다. COMPLETED
    상태가 아니면 아직 영상이 없으므로 불필요한 S3 호출을 하지 않고 None 반환.
    """
    shortform = (
        db.query(ShortForm)
        .filter(ShortForm.shorts_id == shorts_id)  # ⭐ 수정: 컬럼명 shorts_id로 변경
        .one()
    )
    video_url = None
    # COMPLETED이면서 실제 s3_key가 저장되어 있을 때만 presigned URL 발급
    # (COMPLETED인데 s3_key가 없는 비정상 케이스도 방어)
    if shortform.status == ShortFormStatus.COMPLETED and shortform.final_video_s3_key:
        video_url = generate_download_presigned_url(shortform.final_video_s3_key)

    return ShortFormStatusRead(
        shorts_id=shortform.shorts_id,  # ⭐ 수정: 필드명 shorts_id로 변경
        status=shortform.status,
        video_url=video_url,
        error_message=shortform.error_message,  # FAILED가 아니면 항상 None (위 update 로직 덕분)
    )


# ---------------------------------------------------------------------------
# Celery 태스크 큐잉 (AI 파이프라인 트리거)
# ---------------------------------------------------------------------------

def queue_shortform_generation(
    db: Session,
    shorts_id: int,  # ⭐ 수정: shortform_id(str) → shorts_id(int)
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
    # 큐잉과 동시에 GENERATING으로 바꿔서, 프론트가 폴링(get_shortform_status)했을 때
    # 즉시 "생성 중" 상태를 확인하고 중복 클릭을 막을 수 있게 함
    update_shortform_status(db, shorts_id, ShortFormStatus.GENERATING)  # ⭐ 수정: shorts_id로 변경

    # .delay()는 Celery 태스크를 비동기 큐에 등록만 하고 즉시 리턴한다.
    # 실제 렌더링(Vision/RAG/Story/Validation/FFmpeg Agent 체인)은 워커 프로세스에서 처리.
    render_shortform_task.delay(
        shorts_id=shorts_id,  # ⭐ 수정: shortform_id → shorts_id
        media_keys=media_keys,
        captions=[c.model_dump() for c in captions],  # Pydantic 모델 → dict (Celery 직렬화용, JSON으로 큐에 전달되기 때문)
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

AI_SCRIPT_GENERATE_TIMEOUT_SECONDS = 60.0  # ⭐ 수정: Gemini 할당량 초과 시 OpenAI 폴백까지 걸리는 시간을 감안해 30 → 60초로 상향
MAX_CAPTION_COUNT = 20          # 30초 영상 기준 상한 (자막이 너무 많으면 화면이 복잡해짐 방지)
MAX_CAPTION_TEXT_LENGTH = 40    # 9:16 세로 화면에서 한 줄로 표시 가능한 대략적인 글자 수 상한


def generate_ai_script(
    db: Session,
    shorts_id: int,  # ⭐ 수정: shortform_id(str) → shorts_id(int)
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
    # 존재하지 않으면 .one()이 NoResultFound를 던지고, 라우터에서 404로 변환될 예정
    shortform = (
        db.query(ShortForm)
        .filter(ShortForm.shorts_id == shorts_id)  # ⭐ 수정: 컬럼명 shorts_id로 변경
        .one()
    )

    # AI 서버가 대본을 생성하는 데 필요한 최소 정보만 payload로 구성
    # ⭐ 수정: request.media_keys/request.mood_tag는 ScriptGenerateRequest에 없는 필드였음
    # → 실제 스키마 필드인 selected_media_s3_keys로 수정 (mood_tag는 스키마에 없어 제거)
    payload = {
        "shorts_id": shorts_id,  # ⭐ 수정: shortform_id → shorts_id
        "user_name": shortform.user.nickname,  # ⭐ 수정: LLM Story Agent 프롬프트용 - ShortForm.user 관계로 바로 조회
        "quest_title": request.quest_title,  # ⭐ 수정: LLM Story Agent 프롬프트용 - 프론트가 실어 보낸 값 그대로 전달
        "media_keys": request.selected_media_s3_keys,
    }

    try:
        # 동기(sync) 방식 호출. 만약 라우터가 async def라면 httpx.AsyncClient로
        # 바꿔서 이벤트 루프를 블로킹하지 않도록 검토 필요 (현재는 라우터 미구현 상태)
        response = httpx.post(
            f"{settings.AI_SERVICE_URL}/generate-script",
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
            shorts_id,  # ⭐ 수정: shortform_id → shorts_id
            ShortFormStatus.FAILED,
            error_message=f"AI 대본 생성 서버 호출 실패: {exc}",
        )
        # ⭐ 수정: bare raise였던 걸 HTTPException으로 교체.
        # httpx 예외를 그대로 올리면 FastAPI가 처리 못 해 프론트가 detail 없는
        # 순수 500(트레이스백)을 받는다 - 프론트는 error.response.data.detail을 읽으므로
        # 타임아웃/그 외 장애를 구분해 명확한 상태 코드+detail로 응답한다.
        if isinstance(exc, httpx.TimeoutException):
            raise HTTPException(
                status_code=504,
                detail="AI 대본 생성이 시간 내에 끝나지 않았습니다. 잠시 후 다시 시도해주세요.",
            ) from exc
        raise HTTPException(
            status_code=502,
            detail="AI 대본 생성 서버 호출에 실패했습니다.",
        ) from exc

    ai_result = response.json()
    # AI 서버 응답의 각 캡션 dict를 CaptionItem 객체로 변환 (타입 검증 겸함)
    # 만약 AI 서버 응답 형식이 스키마와 안 맞으면 여기서 pydantic ValidationError 발생
    captions = [
        CaptionItem(**caption_raw) for caption_raw in ai_result.get("captions", [])
    ]
    _validate_captions(captions)  # 개수/길이 제약 검증 (수정 검증 함수와 로직 공유)

    # ⭐ 수정: ScriptGenerateResponse는 status/title이 required 필드인데 기존엔 누락되어
    # ValidationError가 나던 부분 - shortform.status와 AI 응답의 title로 채움
    return ScriptGenerateResponse(
        shorts_id=shorts_id,  # ⭐ 수정: shortform_id → shorts_id
        status=shortform.status,
        title=ai_result.get("title", ""),
        captions=captions,
        bgm_id=ai_result.get("bgm_id"),  # ⭐ 수정: AI 서버가 매칭한 분위기 기반 BGM (없으면 None)
    )


def validate_edited_captions(shorts_id: int, request: ScriptUpdateRequest) -> ScriptGenerateResponse:
    """
    사용자가 팝업에서 AI가 생성한 캡션을 직접 수정했을 때 호출하는 "검증 전용" 함수.
    이름 그대로 저장(update)이 아니라 validate이다 — DB에는 아무것도 쓰지 않는다.

    프론트가 팝업을 닫지 않고 계속 편집하는 동안, 텍스트를 고칠 때마다(또는
    "다음" 버튼을 누를 때) 이 함수를 호출해서 규칙 위반 여부를 즉시 알려주는
    용도로 사용한다. 실제 최종 반영은 사용자가 "생성하기"를 눌러
    queue_shortform_generation()이 호출될 때 한 번만 일어난다.
    """
    # DB 조회 없음, Session 파라미터도 없음 → 완전히 stateless한 순수 검증 함수
    _validate_captions(request.captions)
    # ⭐ 수정: status 필드 채움 - 아직 렌더링 전 단계이므로 PENDING 고정
    # ⭐ 수정: ScriptUpdateRequest엔 shorts_id 필드가 없어 request.shorts_id 참조가
    # AttributeError였음 → router가 path parameter로 이미 받아 넘겨주는 shorts_id 사용
    return ScriptGenerateResponse(
        shorts_id=shorts_id,
        status=ShortFormStatus.PENDING,
        title=request.title,
        captions=request.captions,  # 입력받은 캡션을 그대로 되돌려줌 (검증 통과했다는 의미)
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
        # ⭐ 수정: caption.text -> CaptionItem 실제 필드명인 caption.caption으로 변경
        if len(caption.caption) > MAX_CAPTION_TEXT_LENGTH:
            # 에러 메시지에 캡션 앞부분만 잘라서 보여줘서 어떤 캡션이 문제인지 식별 가능하게 함
            raise ValueError(
                f"캡션 텍스트는 {MAX_CAPTION_TEXT_LENGTH}자를 초과할 수 없습니다: "
                f"'{caption.caption[:20]}...'"  # ⭐ 수정: caption.text -> caption.caption (AttributeError 원인)
            )