from fastapi import FastAPI

from ai.app.quest_recommend.router import router as quest_recommend_router
from ai.app.challenge_recommend.router import router as challenge_recommend_router

app = FastAPI(
    title="Good Deed Quest AI Model Server",
    description="선행퀘스트 플랫폼을 지탱하는 LangGraph 에이전트, RAG 코치, Vision 인증 API 서버",
    version="1.0.0"
)

########################
# 아래처럼 라우터 추가하세요.
#######################

# AI 팀 챌린지 사용자 추천 API를 메인 앱에 등록합니다.
app.include_router(challenge_recommend_router)
# 퀘스트 추천 API (모듈화된 라우터 등록)
app.include_router(quest_recommend_router)

@app.get("/")
def home():
    return {
        "status": "online",
        "service": "Good Deed Quest AI Backend",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    # uvicorn 실행 (개발 시 python -m ai.main 로 기동)
    uvicorn.run("ai.main:app", host="0.0.0.0", port=8001, reload=True)
