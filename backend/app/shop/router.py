from fastapi import APIRouter, Depends
from pydantic import BaseModel
from backend.app.common.response import APIResponse
from backend.app.common.auth import get_current_user

router = APIRouter(prefix="/shop", tags=["Dedicated Shop & Donation System"])

class PurchaseRequest(BaseModel):
    item_id: int

@router.post("/purchase")
def purchase_item(req: PurchaseRequest, user: dict = Depends(get_current_user)):
    """독립 상점 API: 기부 굿즈 교환 또는 탄소 저감 나무 기부를 신청합니다."""
    # 포인트 차감 비즈니스 로직 및 기부 스키마 히스토리 추가 로직 작성 지점
    return APIResponse.ok(
        data={"user_id": user["id"], "item_id": req.item_id, "remaining_points": 240},
        message=f"상점 상품 {req.item_id} 처리가 완료되었습니다."
    )
