"""
ai/app/short_form/router.py

백엔드(backend/app/short_form/tasks.py, service.py)가 호출하는 AI 서버 엔드포인트.

⚠️ 다른 도메인 라우터들(quest_verification 등)은 prefix="/ai"를 쓰지만, 이 라우터는
   prefix를 붙이지 않는다. backend/app/short_form/tasks.py, service.py가 실제로
   호출하는 경로가 f"{AI_SERVICE_URL}/generate-video", f"{AI_SERVICE_URL}/generate-script"
   (접두사 없음)이기 때문 — 백엔드 코드에 맞춰야 하므로 그대로 둠.
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from .agents.vision_agent import vision_agent
from .agents.rag_agent import rag_agent  # ⭐ 수정: 자동생성 BGM 매칭용
from .agents.llm_story_agent import llm_story_agent
from .graph import run_shortform_pipeline
from .models import BackgroundMusic
from .state import ShortFormState, BgmMatchResult
from ..common.database import SessionLocal

logger = logging.getLogger(__name__)

router = APIRouter(tags=["AI ShortForm"])


# ⭐ 신규: bgm_s3_key -> bgm_id 역조회 (BGM 재매칭 덮어쓰기 버그 수정용)
def _resolve_bgm_match_by_s3_key(bgm_s3_key: str) -> Optional[BgmMatchResult]:
    """
    backend가 이미 확정한 BGM의 s3_key로 BackgroundMusic을 조회해서 bgm_match를 만든다.
    render_agent._download_bgm()이 bgm_id로만 재조회하기 때문에 s3_key 그대로는 못 쓰고
    bgm_id가 필요해서 여기서 미리 변환해둔다.

    조회에 실패하면(삭제되었거나 s3_key 불일치 등) None을 반환 -> 호출부에서 bgm_match를
    비워둔 채로 넘겨서 graph.py의 route_after_vision이 기존처럼 rag_agent 자동 매칭으로
    폴백하게 한다 (rag_agent의 _hard_fallback()과 동일한 최후 안전장치 경로).
    """
    with SessionLocal() as session:
        bgm = session.scalars(
            select(BackgroundMusic).where(BackgroundMusic.s3_key == bgm_s3_key)
        ).first()

    if bgm is None:
        logger.warning(
            f"[ShortFormRouter] bgm_s3_key={bgm_s3_key!r}에 해당하는 BackgroundMusic을 찾을 수 "
            "없어 RAG 자동 매칭으로 폴백합니다."
        )
        return None

    return {
        "bgm_id": bgm.bgm_id,
        "bgm_title": bgm.title,
        "match_score": 1.0,
        "match_reason": "backend가 이미 확정한 BGM(bgm_s3_key)을 그대로 사용",
    }


# ---------------------------------------------------------------------------
# POST /generate-video  (backend/app/short_form/tasks.py: render_shortform_task)
# ---------------------------------------------------------------------------

class CaptionItemRequest(BaseModel):
    media_s3_key: str
    order: int
    caption: str


class GenerateVideoRequest(BaseModel):
    shorts_id: int
    media_keys: List[str] = Field(..., min_length=1)
    captions: List[CaptionItemRequest] = Field(..., min_length=1)
    bgm_s3_key: str


class GenerateVideoResponse(BaseModel):
    s3_key: str


@router.post("/generate-video", response_model=GenerateVideoResponse)
def generate_video(req: GenerateVideoRequest):
    """
    Celery task(render_shortform_task)가 호출하는 렌더링 트리거 엔드포인트.
    Vision -> RAG -> LLM Story -> Validation -> FFmpeg Render 5-Agent 파이프라인을 동기 실행한다.

    ⭐ 수정: bgm_s3_key는 backend가 이미 확정한 BGM의 s3_key다. bgm_id로 역조회해
    bgm_match를 미리 채워 넣으면 graph.py의 route_after_vision이 rag_agent(자동 매칭)를
    건너뛰고 이 값을 그대로 쓴다 (BGM 재매칭 덮어쓰기 버그 수정). 역조회 실패 시에는
    bgm_match를 비워 기존처럼 rag_agent 자동 매칭으로 폴백한다.
    """
    # media_s3_key로 정확히 매칭해서 media_keys 순서(=씬 순서)에 맞는 캡션 리스트를 만든다.
    # (order 필드로 단순 정렬 후 media_keys와 인덱스로만 맞추면, 두 리스트의 순서가
    #  어긋났을 때 이미지-자막이 잘못 매칭될 수 있어 media_s3_key 기준으로 명시적으로 정렬)
    caption_by_key = {c.media_s3_key: c.caption for c in req.captions}
    ordered_captions = [caption_by_key.get(key, "") for key in req.media_keys]

    initial_state: ShortFormState = {
        "shorts_id": req.shorts_id,
        "user_name": "",
        "quest_title": "",
        "media_keys": req.media_keys,
        "edited_captions": ordered_captions,
        "vision_results": [],
        "bgm_match": _resolve_bgm_match_by_s3_key(req.bgm_s3_key),  # ⭐ 수정: BGM 재매칭 방지
        "generated_captions": [],
        "validation_passed": False,
        "validation_errors": [],
        "rendered_video_key": None,
        "status": "GENERATING",
        "error_message": None,
    }

    final_state = run_shortform_pipeline(initial_state)

    if final_state["status"] != "COMPLETED" or not final_state.get("rendered_video_key"):
        logger.error(
            f"[ShortFormRouter] 렌더링 실패: shorts_id={req.shorts_id}, "
            f"error={final_state.get('error_message')}"
        )
        raise HTTPException(
            status_code=422,
            detail=final_state.get("error_message") or "영상 생성 파이프라인이 실패했습니다.",
        )

    return GenerateVideoResponse(s3_key=final_state["rendered_video_key"])


# ---------------------------------------------------------------------------
# POST /generate-script  (backend/app/short_form/service.py: generate_ai_script)
# ---------------------------------------------------------------------------

class GenerateScriptRequest(BaseModel):
    shorts_id: int
    media_keys: List[str] = Field(..., min_length=1)
    # ⭐ 수정: llm_story_agent 프롬프트가 쓰는 user_name/quest_title을 backend가 실어 보냄
    user_name: str
    quest_title: str


class GenerateScriptCaptionResponse(BaseModel):
    media_s3_key: str
    order: int
    caption: str


class GenerateScriptResponse(BaseModel):
    title: str = ""
    captions: List[GenerateScriptCaptionResponse]
    # ⭐ 수정: 사진 선택 화면의 "자동생성"이 대본과 함께 분위기 기반 BGM도 한 번에
    # 받아쓸 수 있도록 추가. RAG 매칭 자체가 실패해도(예: BGM 시딩 문제) 대본 생성까지
    # 막을 이유는 없어서 매칭 실패 시 None으로 내려간다 - 호출부(backend)가 그 경우엔
    # 기존처럼 자체 fallback으로 bgm_id를 채운다.
    bgm_id: int | None = None
    bgm_title: str | None = None


@router.post("/generate-script", response_model=GenerateScriptResponse)
def generate_script(req: GenerateScriptRequest):
    """
    AI 대본 생성 팝업 최초 진입 시 backend/app/short_form/service.py:generate_ai_script()가 호출.
    Vision Agent로 이미지를 분석하고 LLM Story Agent로 온스크린 캡션을 생성한다.

    ⭐ 수정: RAG(BGM 매칭)도 함께 실행한다. 원래는 "ShortForm 생성 시점에 bgm_id가 이미
    확정되어 있어 여기서 다시 실행할 이유가 없다"는 전제였지만, 그 확정 로직 자체가
    사진 분석 없이 그냥 최근 등록된 BGM을 고르는 더미 fallback이었다. 사진 선택 화면의
    "자동생성"이 실제로 사진 분위기에 맞는 BGM을 고르려면, vision_agent 결과가 나온
    이 시점에 RAG를 돌려서 bgm_id를 응답에 실어 보내야 backend가 그 값으로 ShortForm을
    다시 만들 수 있다. Validation/Render는 여전히 호출하지 않는다(캡션 생성과 무관).
    RAG 실패는 대본 생성 자체를 막을 이유가 없으므로 여기서만 잡고 bgm_id=None으로 내려보낸다.
    ⚠️ 현재 어떤 Agent도 영상 "제목(title)"을 생성하지 않으므로 title은 항상 빈 문자열.
    """
    state: ShortFormState = {
        "shorts_id": req.shorts_id,
        "user_name": req.user_name,  # ⭐ 수정: backend가 조회해서 실어 보낸 값 사용
        "quest_title": req.quest_title,  # ⭐ 수정: backend가 프론트에서 받아 실어 보낸 값 사용
        "media_keys": req.media_keys,
        "edited_captions": None,
        "vision_results": [],
        "bgm_match": None,
        "generated_captions": [],
        "validation_passed": False,
        "validation_errors": [],
        "rendered_video_key": None,
        "status": "GENERATING",
        "error_message": None,
    }

    state = vision_agent(state)
    state = llm_story_agent(state)

    if state.get("status") == "FAILED":
        raise HTTPException(
            status_code=422,
            detail=state.get("error_message") or "대본 생성에 실패했습니다.",
        )

    bgm_id: int | None = None
    bgm_title: str | None = None
    try:
        state = rag_agent(state)
        bgm_match = state.get("bgm_match")
        if bgm_match:
            bgm_id = bgm_match["bgm_id"]
            bgm_title = bgm_match["bgm_title"]
    except Exception:
        logger.exception("[ShortFormRouter] BGM 자동 매칭 실패, bgm_id 없이 대본만 반환합니다.")

    # vision_results[i]는 generated_captions[i]와 1:1 대응한다 (llm_story_agent가
    # vision_results 순서 그대로 캡션을 만들기 때문). req.media_keys로 매칭하면 Vision
    # Agent가 스킵한 영상 때문에 캡션이 한 칸씩 밀려 엉뚱한 미디어에 붙는 버그가 있었음
    # (media_keys=[사진1, 영상, 사진2] → 캡션이 [사진1, 영상]에 붙고 사진2는 누락).
    # 실제로 분석된 media_key 기준으로 짝지어야 정확하다.
    if state["vision_results"]:
        captions = [
            GenerateScriptCaptionResponse(
                media_s3_key=vision_result["media_key"], order=idx, caption=caption
            )
            for idx, (vision_result, caption) in enumerate(
                zip(state["vision_results"], state["generated_captions"])
            )
        ]
    else:
        # 분석된 미디어가 하나도 없을 때(전부 영상이거나 Vision 전부 실패) fallback -
        # llm_story_agent가 만든 기본 캡션(scene_count=1)을 첫 번째 선택 미디어에 붙인다.
        captions = [
            GenerateScriptCaptionResponse(media_s3_key=req.media_keys[0], order=0, caption=caption)
            for caption in state["generated_captions"]
        ]

    return GenerateScriptResponse(title="", captions=captions, bgm_id=bgm_id, bgm_title=bgm_title)
