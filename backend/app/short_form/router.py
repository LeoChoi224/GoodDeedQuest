from fastapi import APIRouter, Depends, BackgroundTasks
from pydantic import BaseModel
import httpx
from backend.app.common.response import APIResponse
from backend.app.common.auth import get_current_user
from backend.app.common.config import get_setting

router = APIRouter(prefix="/shorts", tags=["AI Short-form Videos"])

class CreateShortsRequest(BaseModel):
    quest_id: int
    user_name: str
    bg_music_style: str = "acoustic"

async def generate_shorts_task(quest_id: int, user_name: str, bg_music_style: str):
    """비동기적으로 AI 서버를 호출하여 숏폼 비디오 생성을 시작합니다."""
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{get_setting().AI_SERVICE_URL}/ai/shorts/generate",
                json={"quest_id": quest_id, "user_name": user_name, "bg_music_style": bg_music_style},
                timeout=30.0
            )
            # 완료 시 알림 등을 WebSocket으로 쏠 수 있습니다.
    except Exception as e:
        print(f"Error requesting shorts generation: {e}")

@router.post("/generate")
def request_shorts_generation(
    req: CreateShortsRequest,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user)
):
    """사용자가 수행한 퀘스트를 기반으로 AI 숏폼 영상 제작을 요청합니다."""
    # 시간이 걸리는 작업이므로 백그라운드 태스크로 넘겨줍니다.
    background_tasks.add_task(generate_shorts_task, req.quest_id, user["name"], req.bg_music_style)
    
    return APIResponse.ok(
        message="숏폼 생성이 시작되었습니다. 완료 시 알림이 발송됩니다.",
        data={"status": "PROCESSING", "quest_id": req.quest_id}
    )
