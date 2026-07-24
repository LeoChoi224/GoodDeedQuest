from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.common.config import get_setting

# 라우터 임포트
from backend.app.auth.router import router as auth_router
from backend.app.quest.router import router as quest_router
from backend.app.quest_recommend.router import router as recommend_router
from backend.app.quest_verification.router import router as verification_router
from backend.app.challenge.router import router as challenge_router
from backend.app.short_form.router import router as shorts_router
from backend.app.map.router import router as map_router
from backend.app.growth.router import router as growth_router
# from backend.app.notification.router import router as notification_router  # TODO: notification 모듈 아직 없음
# from backend.app.admin.router import router as admin_router  # TODO: auth.dependencies.get_current_admin 미구현
from backend.app.shop.router import router as shop_router
import backend.app.models_registry  # noqa: F401  # 모든 도메인 모델을 한 번에 등록 (relationship/ForeignKey 문자열 참조 해석용)
# TODO router.py 작업할때 short_form, badge 라우터 임포트 예정

app = FastAPI(
    title=get_setting().PROJECT_NAME,
    description="Good Deed Quest (선행퀘스트) 메인 백엔드 API 서버",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발용. 실배포 시 구체적인 프론트엔드 도메인 지정
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API v1 라우터 등록
api_prefix = get_setting().API_V1_STR
app.include_router(auth_router, prefix=api_prefix)
app.include_router(quest_router, prefix=api_prefix)
app.include_router(recommend_router, prefix=api_prefix)
app.include_router(verification_router, prefix=api_prefix)
app.include_router(challenge_router, prefix=api_prefix)
app.include_router(shorts_router, prefix=api_prefix)
app.include_router(map_router, prefix=api_prefix)
app.include_router(growth_router, prefix=api_prefix)
# app.include_router(notification_router, prefix=api_prefix)  # TODO: notification 모듈 아직 없음
# app.include_router(admin_router, prefix=api_prefix)  # TODO: auth.dependencies.get_current_admin 미구현
app.include_router(shop_router, prefix=api_prefix)

@app.get("/")
def home():
    return {
        "status": "online",
        "project": get_setting().PROJECT_NAME,
        "docs": "/docs",
        "description": "작은 선행을 퀘스트로 - AI 기반 공익 플랫폼 Good Deed Quest"
    }

if __name__ == "__main__":
    import uvicorn
    # uvicorn 실행 (개발 시 python -m backend.main 로 기동)
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
