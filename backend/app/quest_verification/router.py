from fastapi import APIRouter, Depends, UploadFile, File, Form
import httpx
from backend.app.common.response import APIResponse
from backend.app.common.auth import get_current_user
from backend.app.common.config import get_setting

router = APIRouter(prefix="/quest-verification", tags=["Quest AI Verification"])

@router.post("/verify")
async def verify_quest(
    quest_id: int = Form(...),
    image: UploadFile = File(...),
    user: dict = Depends(get_current_user)
):
    """Vision AI를 통해 사용자가 제출한 퀘스트 인증 사진을 검증합니다."""
    # AI 서버의 Vision 인증 API 호출 시뮬레이션
    try:
        # 파일을 multipart/form-data로 AI 서버에 중계
        file_content = await image.read()
        files = {"image": (image.filename, file_content, image.content_type)}
        data = {"quest_id": str(quest_id)}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{get_setting().AI_SERVICE_URL}/ai/verify",
                data=data,
                files=files,
                timeout=15.0
            )
            if response.status_code == 200:
                ai_result = response.json()
                verified = ai_result.get("data", {}).get("verified", False)
                reason = ai_result.get("data", {}).get("reason", "검증 실패")
                
                if verified:
                    # 여기에 사용자 레벨업, 경험치 지급, 포인트 적립 로직 구현
                    reward_info = {
                        "xp_gained": 100,
                        "points_gained": 20,
                        "current_xp": user["xp"] + 100
                    }
                    return APIResponse.ok(
                        data={"verified": True, "reason": reason, "rewards": reward_info},
                        message="인증이 승인되었습니다!"
                    )
                else:
                    return APIResponse.fail(
                        data={"verified": False, "reason": reason},
                        message="인증이 반려되었습니다. 사진을 다시 확인해주세요."
                    )
    except Exception as e:
        # AI 서버 구동 실패 시 폴백(임시 승인처리 또는 안내)
        pass

    # 임시 개발용 모의 로직 (항상 승인)
    return APIResponse.ok(
        data={
            "verified": True,
            "reason": "[Mock] AI 서버가 비활성화되어 임시 승인 처리 되었습니다.",
            "rewards": {"xp_gained": 50, "points_gained": 10, "current_xp": user["xp"] + 50}
        },
        message="임시 인증 완료"
    )
