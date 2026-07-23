from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from typing import Annotated
import httpx
import uuid
import hashlib
from backend.app.common.response import APIResponse
from backend.app.common.auth import get_current_user
from backend.app.common.config import get_setting
from backend.app.common.deps import get_repository
from backend.app.common.repository import DatabaseRepository
from backend.app.quest.models import Quest
from backend.app.quest.enums import QuestType
from backend.app.quest_verification.schemas import PresignRequest, PresignResponse, SubmitRequest, SubmitResponse
from backend.app.quest_verification.models import QuestSubmission
from backend.app.quest_verification.enums import MediaType, SubmissionStatus
from backend.app.common.s3_client import generate_upload_presigned_url, generate_download_presigned_url
from backend.app.auth.router import get_current_db_user
from backend.app.auth.models import User

QuestRepository = Annotated[
    DatabaseRepository[Quest],
    Depends(get_repository(Quest))
]

SubmissionRepository = Annotated[
    DatabaseRepository[QuestSubmission],
    Depends(get_repository(QuestSubmission))
]


router = APIRouter(prefix="/quest-verification", tags=["Quest AI Verification"])



@router.post("/presign", response_model=PresignResponse)
def get_upload_url(req: PresignRequest, current_user: User = Depends(get_current_db_user)):
    ext = "mp4" if req.content_type.startswith("video/") else "jpg"
    s3_key = f"submission/{current_user.user_id}/{req.quest_id}/{uuid.uuid4()}.{ext}"
    upload_url =  generate_upload_presigned_url(s3_key, req.content_type)
    return PresignResponse(upload_url=upload_url, s3_key=s3_key)

@router.post('/submit', response_model=SubmitResponse)
def submit_verification(
    req: SubmitRequest,
    quest_repository: QuestRepository,
    submission_respository: SubmissionRepository,
    current_user: User = Depends(get_current_db_user)
):
    quest = quest_repository.get(req.quest_id)
    if quest is None:
        raise HTTPException(status_code=404, detail="Quest not found")
    
    media_url = generate_download_presigned_url(req.s3_key)
    
    image_bytes = httpx.get(media_url, timeout=30.0).content
    media_hash = hashlib.sha256(image_bytes).hexdigest()
    
    duplicate = submission_respository.get_by(media_hash = media_hash)
    if duplicate is not None:
        submission_respository.create({
            "user_id": current_user.user_id,
            "quest_id": quest.quest_id,
            "media_url": req.s3_key,
            "media_hash": media_hash,
            "final_status": SubmissionStatus.REJECTED,
            "ai_verdict": {"verified": False, "reason": "duplicate"},
        })
        return SubmitResponse(
            verified=False,
            reason="이미 제출된 적이 있는 사진입니다. 새로 촬영한 사진을 올려 주세요.",
        )
    try: 
        response = httpx.post(
            f"{get_setting().AI_SERVICE_URL}/ai/verify-quest",
            json={
                "quest_id": quest.quest_id,
                "quest_title": quest.quest_title,
                "quest_description": quest.quest_description,
                "media_url": media_url
                },
            timeout=60.0
        )
        response.raise_for_status()
        result = response.json()['data']
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="AI 검증 서버 호출에 실패했습니다.")
    
    media_type = MediaType.PHOTO if quest.quest_type == QuestType.VOLUNTEER else MediaType.VIDEO
    
    submission_respository.create({
        "user_id": current_user.user_id,
        "quest_id": quest.quest_id,
        "media_url": req.s3_key,
        "extra_media_urls": req.extra_media_keys,
        "media_type": media_type,
        "media_hash": media_hash,
        "ai_verdict": result,
        "final_status": SubmissionStatus.ACCEPTED if result["verified"] else SubmissionStatus.REJECTED,
        })
        
    xp_gained = 0
    points_gained = 0
    if result['verified']:
        xp_gained = quest.reward_exp or 0
        points_gained = quest.reward_point or 0
        current_user.current_xp += xp_gained
        current_user.point_balance += points_gained
        submission_respository.session.commit()
    
    return SubmitResponse(
        verified=result["verified"],
        reason=result["reason"],
        xp_gained=xp_gained,
        points_gained=points_gained,
    )