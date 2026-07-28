# backend/app/short_form/tasks.py

"""
숏폼 생성 Celery task 본체.

전체 흐름:
  1. 사용자가 숏폼생성페이지에서 "생성하기"를 누름
  2. service.py의 queue_shortform_generation()이 상태를 GENERATING으로 바꾸고
     render_shortform_task.delay()로 이 task를 큐에 등록
  3. Celery 워커가 큐에서 꺼내서 아래 render_shortform_task를 실행
  4. AI서버에 영상 렌더링을 요청하고, 결과에 따라 DB 상태를 COMPLETED/FAILED로 갱신

이 파일이 담당하는 범위는 "AI서버 호출 + 결과에 따른 상태 갱신"까지이며,
실제 Vision/RAG/LLM/FFmpeg 파이프라인은 별도의 AI 서버가 처리한다.
"""

from sqlalchemy.orm import Session
import httpx

from backend.app.short_form.celery_app import celery_app
from backend.app.short_form.models import ShortForm, BackgroundMusic
from backend.app.short_form.enums import ShortFormStatus
from backend.app.common.database import SessionLocal
from backend.app.common.config import get_setting

# get_setting()은 @lru_cache가 걸려있어서 매번 새로 만들지 않고
# 캐싱된 Settings 인스턴스를 반환한다. 모듈 로드 시 한 번만 호출해서 재사용.
settings = get_setting()


@celery_app.task(name="short_form.render_shortform_task")
def render_shortform_task(
    shorts_id: int,
    media_keys: list[str],
    captions: list[dict],
) -> None:
    """
    AI서버에 영상 렌더링을 요청하고, 결과에 따라 ShortForm 상태를 업데이트한다.

    Args:
        shorts_id: 대상 ShortForm의 PK
        media_keys: 사용자가 선택한 미디어 파일들의 S3 key 리스트
        captions: 최종 확정된 캡션 리스트 (프론트에서 편집 완료된 상태,
                  CaptionItem.model_dump() 결과라 이미 dict 형태)

    참고: GENERATING 상태 전환은 이 task가 아니라 service.py의
    queue_shortform_generation()에서 큐잉 시점에 이미 처리한다.
    그래서 이 task는 최종 결과인 COMPLETED / FAILED 전환만 담당한다.
    """

    # ⚠️ service를 파일 최상단이 아니라 함수 안에서 import하는 이유:
    # service.py가 "from backend.app.short_form.tasks import render_shortform_task"로
    # 이 파일을 가져다 쓰고 있어서, 이 파일도 최상단에서 service.py를 가져오면
    # 서로가 서로를 부르는 순환 참조(circular import)가 발생해 임포트 에러가 난다.
    # 함수 호출 시점(task가 실제로 실행될 때)에만 import하면 이 문제가 생기지 않는다.
    from backend.app.short_form import service

    # Celery task는 FastAPI 요청 스코프 밖(별도 워커 프로세스)에서 실행되기 때문에
    # Depends(get_db)를 쓸 수 없다. 그래서 세션을 직접 열고, 끝나면 직접 닫아야 한다.
    db: Session = SessionLocal()
    try:
        # shorts_id로 ShortForm을 다시 조회하는 이유:
        # .delay()로 큐잉할 때 bgm_id 관련 정보는 파라미터로 넘기지 않았기 때문에
        # (media_keys, captions만 전달됨) 여기서 DB를 다시 읽어와야 한다.
        shortform = (
            db.query(ShortForm)
            .filter(ShortForm.shorts_id == shorts_id)
            .one()
        )

        # ShortForm에는 bgm_id(FK)만 있고 실제 파일 경로는 없으므로,
        # BackgroundMusic 테이블에서 s3_key를 따로 가져와야 AI서버에 전달 가능하다.
        bgm = (
            db.query(BackgroundMusic)
            .filter(BackgroundMusic.bgm_id == shortform.bgm_id)
            .one()
        )

        # AI서버에 영상 생성을 동기(sync) 방식으로 요청한다.
        # 이 코드는 Celery 워커 프로세스 안에서 실행되므로, 여기서 몇 분씩
        # 기다려도 API 서버(FastAPI)의 다른 요청 처리에는 영향을 주지 않는다.
        # → 그래서 비동기+폴링 대신 훨씬 단순한 동기 호출을 선택했다.
        response = httpx.post(
            f"{settings.AI_SERVICE_URL}/generate-video",
            json={
                "shorts_id": shorts_id,
                "media_keys": media_keys,
                "captions": captions,
                "bgm_s3_key": bgm.s3_key,
            },
            timeout=600.0,  # 영상 렌더링은 수 분 이상 걸릴 수 있어 넉넉하게 설정
        )
        response.raise_for_status()  # AI서버가 4xx/5xx를 주면 여기서 예외 발생 → 아래 except로 이동

        # AI서버는 렌더링된 영상을 직접 S3에 업로드하고, 그 결과물의 s3_key만
        # 응답으로 돌려준다. 우리 백엔드가 별도로 영상 파일을 받아 업로드하지 않는다.
        result = response.json()

        # 성공: 상태를 COMPLETED로 바꾸고 최종 영상 s3_key를 저장
        service.update_shortform_status(
            db,
            shorts_id,
            ShortFormStatus.COMPLETED,
            final_video_s3_key=result["s3_key"],
        )
    # ⭐ 수정: AI서버가 4xx/5xx로 응답할 때(response.raise_for_status()가 던지는 예외)는
    # 응답 바디의 detail(예: "씬 1: 부적절한 표현이 포함되어 있습니다.")이 실제 실패 사유인데,
    # 기존에는 이 분기가 없어서 일반 HTTPStatusError 문자열("Client error '422 ...'")만
    # error_message에 남고 detail은 버려지고 있었다.
    except httpx.HTTPStatusError as exc:
        try:
            detail = exc.response.json().get("detail")
        except ValueError:
            detail = None  # 응답이 JSON이 아니면 detail을 못 꺼내니 아래 fallback으로
        message = detail or str(exc)
        service.update_shortform_status(
            db,
            shorts_id,
            ShortFormStatus.FAILED,
            error_message=f"영상 생성 실패: {message}",
        )
    except Exception as exc:
        # AI서버 호출 실패, DB 조회 실패, 응답 파싱 실패 등 어떤 이유로든
        # 여기까지 오면 실패로 간주하고 FAILED 처리한다.
        # 예외 메시지를 error_message에 그대로 남겨서, 프론트가 폴링 시
        # 사용자에게 실패 사유를 보여줄 수 있게 한다.
        service.update_shortform_status(
            db,
            shorts_id,
            ShortFormStatus.FAILED,
            error_message=f"영상 생성 실패: {exc}",
        )
    finally:
        # 성공하든 실패하든 세션은 반드시 닫아서 커넥션 누수를 막는다.
        db.close()