from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List
from backend.app.common.response import APIResponse
from backend.app.common.auth import get_current_user

router = APIRouter(prefix="/growth", tags=["Growth & Rewards System"])

class UserGrowthStatus(BaseModel):
    level: int
    xp: int
    next_level_xp: int
    streak_days: int
    badges: List[str]
    points: int

@router.get("/status", response_model=APIResponse[UserGrowthStatus])
def get_growth_status(user: dict = Depends(get_current_user)):
    """현재 사용자의 레벨, 경험치, 스트릭, 보유 배지 및 포인트 정보를 가져옵니다."""
    # Mock 데이터 반환
    status_data = {
        "level": user.get("level", 1),
        "xp": user.get("xp", 100),
        "next_level_xp": user.get("level", 1) * 500,
        "streak_days": 5,
        "badges": ["에코 히어로", "첫걸음", "이웃 사촌"],
        "points": 340
    }
    return APIResponse.ok(data=status_data)

class PurchaseRequest(BaseModel):
    item_id: int

@router.post("/shop/purchase")
def purchase_item(req: PurchaseRequest, user: dict = Depends(get_current_user)):
    """포인트를 활용하여 기부 또는 굿즈를 구매/교환합니다."""
    # 포인트 차감 및 결제/교환 비즈니스 로직
    return APIResponse.ok(message=f"아이템 {req.item_id} 구매 완료! 포인트가 차감되었습니다.")
