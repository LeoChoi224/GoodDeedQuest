"""
backend/app/short_form/router.py

숏폼 생성 도메인 API 라우터.
service.py 함수들을 실제 엔드포인트로 노출한다.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound  # service.py의 .one() 조회 실패 시 발생 -> 여기서 404로 변환

from backend.app.common.database import get_db  # DB 세션 의존성 (요청마다 세션 열고/커밋/닫음)
from backend.app.auth.router import get_current_db_user  # 토큰 검증 후 현재 로그인한 User 반환
from backend.app.auth.models import User

from backend.app.short_form.schemas import (
    ShortFormCreateRequest,
    ShortFormRead,
    ShortFormGenerateRequest,  # ⭐ schemas.py에서 import
    ScriptGenerateRequest,
    ScriptGenerateResponse,
    ScriptUpdateRequest,
    ShortFormStatusRead,
)
from backend.app.short_form.service import (
    create_shortform,
    generate_ai_script,
    validate_edited_captions,
    queue_shortform_generation,
    get_shortform_status,
)

# prefix="/shortforms" -> 아래 모든 엔드포인트 경로 앞에 자동으로 붙음 (예: POST /shortforms)
# tags=["ShortForm"] -> Swagger(/docs) 문서에서 그룹으로 묶여서 표시됨
router = APIRouter(prefix="/shortforms", tags=["ShortForm"])


@router.post("", response_model=ShortFormRead, status_code=status.HTTP_201_CREATED)
def create_shortform_endpoint(
    request: ShortFormCreateRequest,  # 요청 바디: 선택 미디어, bgm_id(선택), 자동생성 여부 등
    db: Session = Depends(get_db),  # 이 요청 처리 동안만 사용할 DB 세션
    current_user: User = Depends(get_current_db_user),  # 인증 필수 - 토큰 없으면 401
):
    """
    숏폼 생성 시작.

    사용자가 대본 팝업(수동 경로) 또는 자동 생성(⑥) 경로 진입 시 최초로 호출.
    ShortForm row를 PENDING 상태로 만들고, bgm_id가 없으면(자동 경로)
    service.py 내부에서 RAG 매칭으로 채워 넣는다.
    아직 실제 렌더링은 시작하지 않음 — 렌더링 트리거는 /generate 엔드포인트가 담당.
    """
    # current_user.user_id: 토큰에서 뽑아낸 로그인 사용자의 PK (int, BigInteger)
    # -> 요청 바디에 user_id를 안 받고 토큰 기준으로만 신뢰 (다른 사람 이름으로 생성 방지)
    return create_shortform(db, current_user.user_id, request)


@router.post("/{shorts_id}/script", response_model=ScriptGenerateResponse)
def generate_ai_script_endpoint(
    shorts_id: int,  # path parameter - 어떤 ShortForm에 대한 대본 생성인지 식별
    request: ScriptGenerateRequest,  # 요청 바디: 사용자가 선택한 인증 이미지 S3 key 목록
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_db_user),
):
    """
    AI 대본 생성 팝업 - 최초 대본 생성 요청.

    선택된 미디어(selected_media_s3_keys)를 AI 서버로 보내
    Vision → RAG → LLM Story Agent 체인을 거친 캡션/제목을 받아온다.
    결과는 DB에 저장하지 않고 응답으로만 내려주며, 프론트가 팝업 상태로
    들고 있다가 사용자가 직접 수정하는 흐름으로 이어짐.
    shorts_id에 해당하는 ShortForm이 없으면 404 반환.
    """
    try:
        # service.py 내부에서: 1) shorts_id 존재 확인 2) AI 서버 동기 호출
        # 3) 응답을 CaptionItem으로 검증/변환 후 반환
        return generate_ai_script(db, shorts_id, request)
    except NoResultFound:
        # db.query(...).one()이 결과 없을 때 던지는 예외 -> API 응답은 404로 변환
        raise HTTPException(status_code=404, detail="ShortForm을 찾을 수 없습니다.")


@router.put("/{shorts_id}/script", response_model=ScriptGenerateResponse)
def validate_edited_captions_endpoint(
    shorts_id: int,  # path parameter - 응답에 그대로 실어 보내기 위해 필요 (검증 로직 자체엔 안 씀)
    request: ScriptUpdateRequest,  # 요청 바디: 사용자가 수정한 title/captions
    current_user: User = Depends(get_current_db_user),
    # ⚠️ db 세션 의존성 없음: 이 엔드포인트는 DB 조회/쓰기가 전혀 없는 순수 검증(stateless)이라 불필요
):
    """
    AI 대본 생성 팝업 - 사용자 수정 캡션 검증.

    사용자가 팝업에서 AI가 생성한 제목/캡션을 직접 고친 뒤 호출.
    이름 그대로 "검증"만 하며 DB에는 아무것도 저장하지 않는다 (stateless).
    캡션 개수/길이 제약을 어기면 400으로 응답. 최종 반영은 /generate
    엔드포인트를 호출할 때 프론트가 이 수정본을 다시 실어 보내는 시점에 일어남.
    """
    try:
        # shorts_id는 서비스 함수의 첫 번째 파라미터로 별도 전달
        # (ScriptUpdateRequest 스키마 자체엔 shorts_id 필드가 없어서)
        return validate_edited_captions(shorts_id, request)
    except ValueError as exc:
        # _validate_captions()에서 개수/길이 제약 위반 시 발생 -> 400 Bad Request로 변환
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/{shorts_id}/generate", status_code=status.HTTP_202_ACCEPTED)
def queue_shortform_generation_endpoint(
    shorts_id: int,  # path parameter - 어떤 ShortForm을 렌더링할지 식별
    request: ShortFormGenerateRequest,  # 요청 바디: 최종 확정된 media_keys + captions
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_db_user),
):
    """
    영상 생성 큐잉 (실제 렌더링 트리거).

    사용자가 팝업에서 캡션을 최종 확정하고 "생성하기"를 누르면 호출.
    media_keys/captions는 DB에 저장하지 않고 Celery 태스크 파라미터로만
    전달한다. 호출 즉시 ShortForm 상태를 GENERATING으로 바꾸고 202를
    반환하며, 실제 렌더링(Vision/RAG/Story/Validation/FFmpeg)은 Celery
    워커가 백그라운드에서 처리 — 프론트는 /status를 폴링해서 진행 확인.
    shorts_id에 해당하는 ShortForm이 없으면 404 반환.
    """
    try:
        # service.py 내부에서: 1) 상태를 GENERATING으로 즉시 변경 (중복 클릭 방지 신호)
        # 2) render_shortform_task.delay(...)로 Celery 큐에 작업 등록 (비동기, 즉시 리턴)
        queue_shortform_generation(db, shorts_id, request.media_keys, request.captions)
    except NoResultFound:
        raise HTTPException(status_code=404, detail="ShortForm을 찾을 수 없습니다.")
    # 202 Accepted: "요청은 받았고 처리 중이다"는 의미 - 실제 완료 여부는 /status로 확인해야 함
    return {"message": "영상 생성이 큐에 등록되었습니다."}


@router.get("/{shorts_id}/status", response_model=ShortFormStatusRead)
def get_shortform_status_endpoint(
    shorts_id: int,  # path parameter - 상태를 조회할 ShortForm 식별
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_db_user),
):
    """
    영상 생성 진행 상태 폴링.

    프론트가 /generate 호출 이후 주기적으로 호출해서 PENDING/GENERATING/
    COMPLETED/FAILED 상태를 확인. COMPLETED면 video_url(presigned URL)이,
    FAILED면 error_message가 함께 내려간다.
    shorts_id에 해당하는 ShortForm이 없으면 404 반환.
    """
    try:
        # service.py 내부에서: COMPLETED + s3_key 존재 시에만 presigned URL을 즉석 발급
        # (매 폴링마다 불필요한 S3 호출 방지)
        return get_shortform_status(db, shorts_id)
    except NoResultFound:
        raise HTTPException(status_code=404, detail="ShortForm을 찾을 수 없습니다.")