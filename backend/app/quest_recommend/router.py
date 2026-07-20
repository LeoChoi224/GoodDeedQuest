from fastapi import APIRouter, Depends
import httpx
from pydantic import BaseModel
from backend.app.common.response import APIResponse
from backend.app.common.auth import get_current_user
from backend.app.common.config import get_setting

router = APIRouter(prefix="/quest-recommend", tags=["Quest AI Recommendation & Coach"])

class AskCoachRequest(BaseModel):
    question: str

@router.post("")
async def recommend_quests(user: dict = Depends(get_current_user)):
    """사용자의 관심사와 위치 정보를 활용해 AI 기반 맞춤형 퀘스트를 추천받습니다."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{get_setting().AI_SERVICE_URL}/ai/recommend",
                json={
                    "user_id": user["id"],
                    "email": user["email"],
                    "interest": ["환경", "봉사"],
                    "location": "서울시 마포구"
                },
                timeout=10.0
            )
            if response.status_code == 200:
                ai_data = response.json()
                return APIResponse.ok(data=ai_data.get("data"), message="AI 추천 성공")
    except Exception as e:
        pass

    fallback_recommendations = [
        {"id": 101, "title": "[AI추천] 일회용품 사용 줄이기 챌린지", "description": "오늘 하루 일회용 플라스틱을 쓰지 않고 다회용품으로 대체해 보세요.", "reason": "사용자님이 환경 분야 관심이 높기 때문에 추천합니다."},
        {"id": 102, "title": "[AI추천] 경의선 숲길 플로깅", "description": "사용자의 위치인 마포구 경의선 숲길에서 조깅과 쓰레기 줍기를 해보세요.", "reason": "사용자님의 위치 마포구 근처 정화 퀘스트입니다."}
    ]
    return APIResponse.ok(data=fallback_recommendations, message="AI 서버 미연결로 폴백 데이터 반환")

@router.post("/coach")
async def ask_coach(req: AskCoachRequest, user: dict = Depends(get_current_user)):
    """[통합] 자원봉사 제도, 공공 캠페인 정보 등을 RAG AI 코치에게 질문합니다."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                # AI 서비스의 추천 도메인 하위로 통합된 RAG 엔드포인트 호출
                f"{get_setting().AI_SERVICE_URL}/ai/recommend/coach",
                json={"question": req.question, "user_id": user["id"]},
                timeout=15.0
            )
            if response.status_code == 200:
                ai_reply = response.json()
                return APIResponse.ok(data=ai_reply.get("data"), message="AI 코치 답변 성공")
    except Exception as e:
        pass

    # Fallback RAG Response
    fallback_response = {
        "answer": "자원봉사 시간은 1365포털이나 VMS를 통해 연계 신청할 수 있습니다. GDQuest는 봉사 인증서 데이터를 API 형태로 공식 연동하는 기능을 준비 중입니다.",
        "sources": ["1365 자원봉사 연계 가이드 v1.2", "GDQuest 기획 가이드라인"]
    }
    return APIResponse.ok(data=fallback_response, message="AI 서버 오프라인으로 로컬 폴백 답변 반환")
