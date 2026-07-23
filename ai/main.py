from fastapi import FastAPI, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Optional
from ai.app.quest_recommend.agent import run_recommendation_flow
from ai.app.challenge_recommend.router import router as challenge_recommend_router
from ai.app.short_form.generator import generate_shorts_boilerplate
from ai.app.quest_recommend.rag import query_rag_coach
from ai.app.local_quest.agent import get_local_shortage_recommendations
from ai.app.user.embedding import embed_user_profile
from ai.app.quest_verification.graph import run_verification_flow
from ai.app.quest_verification.schemas import VerifyQuestRequest

app = FastAPI(
    title="Good Deed Quest AI Model Server",
    description="선행퀘스트 플랫폼을 지탱하는 LangGraph 에이전트, RAG 코치, Vision 인증 API 서버",
    version="1.0.0"
)

# AI 팀 챌린지 사용자 추천 API를 메인 앱에 등록합니다.
app.include_router(challenge_recommend_router)

# 퀘스트 추천 API (LangGraph 연동)
class RecommendRequest(BaseModel):
    user_id: int
    interests: List[str]
    location: str

@app.post("/ai/recommend")
async def ai_recommend(req: RecommendRequest):
    recommended = await run_recommendation_flow(req.user_id, req.interests, req.location)
    return {"success": True, "data": recommended}

# 숏폼 생성 트리거 API
class ShortsRequest(BaseModel):
    quest_id: int
    user_name: str
    bg_music_style: str

@app.post("/ai/shorts/generate")
def ai_shorts_generate(req: ShortsRequest):
    shorts_result = generate_shorts_boilerplate(req.quest_id, req.user_name)
    return {"success": True, "data": shorts_result}

# AI 선행 코치 RAG API (추천 폴더 내 통합)
class CoachQueryRequest(BaseModel):
    question: str
    user_id: int

@app.post("/ai/recommend/coach")
def ai_coach_query(req: CoachQueryRequest):
    coach_reply = query_rag_coach(req.question)
    return {"success": True, "data": coach_reply}

# 지역별 부족 봉사 추천 API
class LocalShortageRequest(BaseModel):
    location: str

@app.post("/ai/local-quest/recommend")
def ai_local_quest_recommend(req: LocalShortageRequest):
    recommended = get_local_shortage_recommendations(req.location)
    return {"success": True, "data": recommended}

class UserEmbedRequest(BaseModel):
    category: Optional[List[str]] = None
    active_time: Optional[List[str]] = None
    preferred_difficulty: Optional[str] = None
    age: Optional[int] = None

@app.post("/ai/user/embed")
def ai_user_embed(req: UserEmbedRequest):
    vector = embed_user_profile(req.category, req.active_time, req.preferred_difficulty, req.age)
    return { "success":True, "data": { "embedding": vector } }

@app.get("/")
def home():
    return {
        "status": "online",
        "service": "Good Deed Quest AI Backend",
        "docs": "/docs"
    }

@app.post("/ai/verify-quest")
def ai_verify_quest(req: VerifyQuestRequest):
    result = run_verification_flow(
        quest_id=req.quest_id,
        quest_title=req.quest_title,
        quest_description=req.quest_description,
        media_url=req.media_url,
    )
    return{"success": True, "data": result}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
