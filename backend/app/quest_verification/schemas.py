from pydantic import BaseModel
from typing import Optional

class PresignRequest(BaseModel):
    quest_id: int
    content_type: str 

class SubmitRequest(BaseModel):
  quest_id: int
  s3_key: str
  extra_media_keys: Optional[list[str]] = None

class PresignResponse(BaseModel):
    upload_url: str
    s3_key: str

class SubmitResponse(BaseModel):
  verified: bool
  reason: str
  xp_gained: int = 0
  points_gained: int = 0
  # 랜덤 챌린지 — 진위가 의심스러울 때만 채워진다
  challenge_required: bool = False
  challenge_code: Optional[str] = None
  submission_id: Optional[int] = None

class ChallengeRequest(BaseModel):
  submission_id: int
  s3_key: str
