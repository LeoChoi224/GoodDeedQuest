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
  