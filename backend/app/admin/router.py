# 관리자 API
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from pydantic import BaseModel
from backend.app.common.response import APIResponse
from backend.app.common.auth import get_current_user

router = APIRouter(prefix="/admin", tags=["Admin Control Panel"])

class ReportSchema(BaseModel):
    id: int
    reporter_id: int
    target_quest_id: int
    reason: str
    status: str

# TODO: 관리자 신고 목록 API 구현 후 서버 데이터로 교체
MOCK_REPORTS = [
    {"id": 1, "reporter_id": 4, "target_quest_id": 2, "reason": "부정인증 사진 업로드 의심 (인터넷 펌 이미지)", "status": "대기중"},
    {"id": 2, "reporter_id": 7, "target_quest_id": 1, "reason": "퀘스트 목적과 맞지 않는 위치 정보 제공", "status": "해결됨"}
]

@router.get("/reports", response_model=APIResponse[List[ReportSchema]])
def get_reports(user: dict = Depends(get_current_user)):
    """관리자 기능: 접수된 신고 목록을 조회합니다."""
    # 실제 구현에서는 user["role"] == "admin" 검증 필요
    return APIResponse.ok(data=MOCK_REPORTS)

# post_status_update = "/reports/{report_id}/resolve"

@router.post("/reports/{report_id}/resolve")
def resolve_report(report_id: int, user: dict = Depends(get_current_user)):
    """관리자 기능: 신고를 처리 완료 상태로 변경합니다."""
    return APIResponse.ok(message=f"신고 {report_id}가 처리 완료되었습니다.")
