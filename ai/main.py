from fastapi import FastAPI, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Optional
from ai.app.quest_recommend.agent import run_recommendation_flow
from ai.app.quest_verification.verifier import verify_quest_image
from ai.app.challenge_recommend.agent import recommend_collaborative_teams
from ai.app.shorts.generator import generate_shorts_boilerplate
from ai.app.quest_recommend.rag import query_rag_coach
from ai.app.local_quest.agent import get_local_shortage_recommendations

app = FastAPI(
    title="Good Deed Quest AI Model Server",
    description="선행퀘스트 플랫폼을 지탱하는 LangGraph 에이전트, RAG 코치, Vision 인증 API 서버",
    version="1.0.0"
)

# 1. 퀘스트 추천 API (LangGraph 연동)
class RecommendRequest(BaseModel):
    user_id: int
    interests: List[str]
    location: str

@app.post("/ai/recommend")
async def ai_recommend(req: RecommendRequest):
    recommended = await run_recommendation_flow(req.user_id, req.interests, req.location)
    return {"success": True, "data": recommended}

# 2. Vision 퀘스트 인증 API (Gemini Vision 연동)
@app.post("/ai/verify")
async def ai_verify(
    quest_id: int = Form(...),
    image: UploadFile = File(...)
):
    image_bytes = await image.read()
    verification_result = verify_quest_image(quest_id, image_bytes)
    return {"success": True, "data": verification_result}

# 3. 협동 챌린지팀 추천 API (LangGraph/Embedding 연동)
class ChallengeRecommendRequest(BaseModel):
    interests: List[str]
    location: str

@app.post("/ai/challenge/recommend")
def ai_challenge_recommend(req: ChallengeRecommendRequest):
    teams = recommend_collaborative_teams(req.interests, req.location)
    return {"success": True, "data": teams}

# 4. 숏폼 생성 트리거 API
class ShortsRequest(BaseModel):
    quest_id: int
    user_name: str
    bg_music_style: str

@app.post("/ai/shorts/generate")
def ai_shorts_generate(req: ShortsRequest):
    shorts_result = generate_shorts_boilerplate(req.quest_id, req.user_name)
    return {"success": True, "data": shorts_result}

# 5. AI 선행 코치 RAG API (추천 폴더 내 통합)
class CoachQueryRequest(BaseModel):
    question: str
    user_id: int

@app.post("/ai/recommend/coach")
def ai_coach_query(req: CoachQueryRequest):
    coach_reply = query_rag_coach(req.question)
    return {"success": True, "data": coach_reply}

# 6. 지역별 부족 봉사 추천 API
class LocalShortageRequest(BaseModel):
    location: str

@app.post("/ai/local-quest/recommend")
def ai_local_quest_recommend(req: LocalShortageRequest):
    recommended = get_local_shortage_recommendations(req.location)
    return {"success": True, "data": recommended}

@app.get("/")
def home():
    return {
        "status": "online",
        "service": "Good Deed Quest AI Backend",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
