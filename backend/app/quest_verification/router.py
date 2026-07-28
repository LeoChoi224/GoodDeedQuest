from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from typing import Annotated
import httpx
import uuid
from backend.app.common.response import APIResponse
from backend.app.common.auth import get_current_user
from backend.app.common.config import get_setting
from backend.app.common.deps import get_repository
from backend.app.common.repository import DatabaseRepository
from backend.app.quest.models import Quest
from backend.app.quest.enums import QuestType
from backend.app.quest_verification.schemas import (
    PresignRequest, PresignResponse, SubmitRequest, SubmitResponse, ChallengeRequest,
)
from backend.app.quest_verification.models import QuestSubmission
from backend.app.quest_verification.enums import MediaType, SubmissionStatus
from backend.app.common.s3_client import generate_upload_presigned_url, generate_download_presigned_url
from backend.app.quest_verification.media import (compute_sha256, compute_media_phash, find_nearest_submission, is_duplicate)
from backend.app.quest_verification.challenge import (
    generate_challenge_code, build_challenge_message, calculate_suspicion, needs_challenge,
)
from backend.app.badge.service import check_and_award_badges
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
    
    extra_keys = req.extra_media_keys or []
    if len(extra_keys) > 4:
        raise HTTPException(status_code=400, detail="추가 사진은 최대 4장까지 가능합니다.")
    
    all_keys = [req.s3_key] + extra_keys
    media_urls = [generate_download_presigned_url(key) for key in all_keys]
    is_video = quest.quest_type != QuestType.VOLUNTEER

    media_hash = None
    primary_phash = None
    for url in media_urls:
        image_bytes = httpx.get(url, timeout=30.0).content
        photo_hash = compute_sha256(image_bytes)
        if media_hash is None:
            media_hash = photo_hash
            # 판정 근거가 되는 대표 증빙만 pHash를 계산한다
            primary_phash = compute_media_phash(image_bytes, is_video)

        duplicate = submission_respository.get_by(media_hash = photo_hash)
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

    # 편집해서 파일 해시만 바꾼 재탕 검사 (Gemini 호출 전이라 비용이 들지 않는다)
    phash_distance = None
    if primary_phash:
        nearest, phash_distance = find_nearest_submission(submission_respository, primary_phash)
        if is_duplicate(phash_distance):
            print(f"pHash 재탕 거절: submission_id={nearest.submission_id} 과 거리 {phash_distance}")
            submission_respository.create({
                "user_id": current_user.user_id,
                "quest_id": quest.quest_id,
                "media_url": req.s3_key,
                "media_hash": media_hash,
                "media_embedding": [primary_phash],
                "final_status": SubmissionStatus.REJECTED,
                "ai_verdict": {"verified": False, "reason": "similar_to_past_submission"},
            })
            return SubmitResponse(
                verified=False,
                reason="이전에 제출된 자료와 너무 비슷합니다. 새로 촬영한 자료를 올려 주세요.",
            )

    try:
        response = httpx.post(
            f"{get_setting().AI_SERVICE_URL}/ai/verify-quest",
            json={
                "quest_id": quest.quest_id,
                "quest_title": quest.quest_title,
                "quest_description": quest.quest_description,
                "media_urls": media_urls,
                "is_video": is_video
                },
            timeout=90.0
        )
        response.raise_for_status()
        result: dict = response.json()['data']
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="AI 검증 서버 호출에 실패했습니다.")
    
    media_type = MediaType.PHOTO if quest.quest_type == QuestType.VOLUNTEER else MediaType.VIDEO
    
    related = result.get("related", [])
    stored_extras = [key for key, ok in zip(extra_keys, related) if ok]
    
    suspicion = calculate_suspicion(
        ai_generated=result.get("ai_generated", False),
        capture_time_known=result.get("capture_time_known", False),
        phash_distance=phash_distance,
    )
    challenge = result["verified"] and needs_challenge(suspicion)
    challenge_code = generate_challenge_code() if challenge else None

    if challenge:
        final_status = SubmissionStatus.PENDING
    elif result["verified"]:
        final_status = SubmissionStatus.ACCEPTED
    else:
        final_status = SubmissionStatus.REJECTED

    submission = submission_respository.create({
        "user_id": current_user.user_id,
        "quest_id": quest.quest_id,
        "media_url": req.s3_key,
        "extra_media_urls": stored_extras,
        "media_type": media_type,
        "media_hash": media_hash,
        "media_embedding": [primary_phash] if primary_phash else None,
        "ai_verdict": {**result, "suspicion_score": suspicion},
        "ai_generated_suspicion": result.get("ai_generated", False),
        "challenge_code": challenge_code,
        "attempt_number": 1,
        "final_status": final_status,
        })
    
    if challenge:
        print(f"챌린지 발급: submission_id={submission.submission_id} 점수={suspicion}")
        return SubmitResponse(
            verified=False,
            reason=build_challenge_message(challenge_code),
            challenge_required=True,
            challenge_code=challenge_code,
            submission_id=submission.submission_id,
        )
        
    xp_gained = 0
    points_gained = 0
    if result['verified']:
        xp_gained = quest.reward_exp or 0
        points_gained = quest.reward_point or 0
        current_user.current_xp += xp_gained
        current_user.point_balance += points_gained
        submission_respository.session.commit()
        # ⭐ 수정: final_status가 ACCEPTED로 확정된 직후 카테고리 기반 배지 자동 지급
        check_and_award_badges(
            db=submission_respository.session,
            user_id=current_user.user_id,
            category_code=quest.category.code,
        )

    return SubmitResponse(
        verified=result["verified"],
        reason=result["reason"],
        xp_gained=xp_gained,
        points_gained=points_gained,
    )


@router.post('/challenge', response_model=SubmitResponse)
def submit_challenge(
    req: ChallengeRequest,
    quest_repository: QuestRepository,
    submission_respository: SubmissionRepository,
    current_user: User = Depends(get_current_db_user)
):
    submission = submission_respository.get(req.submission_id)
    if submission is None:
        raise HTTPException(status_code=404, detail="Submission not found")
    # 남의 제출에 답하지 못하게 막는다
    if submission.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="본인의 인증만 처리할 수 있습니다.")
    if submission.final_status != SubmissionStatus.PENDING or not submission.challenge_code:
        raise HTTPException(status_code=400, detail="추가 인증이 필요한 제출이 아닙니다.")

    media_url = generate_download_presigned_url(req.s3_key)
    try:
        response = httpx.post(
            f"{get_setting().AI_SERVICE_URL}/ai/verify-challenge",
            json={"media_url": media_url, "code": submission.challenge_code},
            timeout=60.0,
        )
        response.raise_for_status()
        result: dict = response.json()['data']
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="AI 검증 서버 호출에 실패했습니다.")

    matched = result.get("matched", False)
    submission.challenge_media_url = req.s3_key
    submission.attempt_number = (submission.attempt_number or 1) + 1
    submission.final_status = SubmissionStatus.ACCEPTED if matched else SubmissionStatus.REJECTED

    xp_gained = 0
    points_gained = 0
    if matched:
        quest = quest_repository.get(submission.quest_id)
        xp_gained = quest.reward_exp or 0
        points_gained = quest.reward_point or 0
        current_user.current_xp += xp_gained
        current_user.point_balance += points_gained

    # 상태 변경과 보상 지급이 함께 저장되도록 마지막에 한 번만 커밋한다
    submission_respository.session.commit()

    if matched:
        # ⭐ 수정: final_status가 ACCEPTED로 확정된 직후 카테고리 기반 배지 자동 지급
        check_and_award_badges(
            db=submission_respository.session,
            user_id=submission.user_id,
            category_code=quest.category.code,
        )

    return SubmitResponse(
        verified=matched,
        reason=result.get("reason", "") if matched
               else "손으로 쓴 인증 번호를 확인하지 못했습니다. 다시 시도해 주세요.",
        xp_gained=xp_gained,
        points_gained=points_gained,
    )