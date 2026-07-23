from typing import List, Optional
from pydantic import BaseModel, Field

class BackendQuestRecommendRequest(BaseModel):
    """프론트엔드 -> 백엔드 추천 요청 DTO"""
    interests: Optional[List[str]] = Field(
        None,
        # "관심 분야 목록"
        description="List of user interest categories (e.g. VULNERABLE_GROUP, ENVIRONMENT)"
    )
    latitude: Optional[float] = Field(
        None,
        # "현재 위도"
        description="Current latitude coordinate"
    )
    longitude: Optional[float] = Field(
        None,
        # "현재 경도"
        description="Current longitude coordinate"
    )
    request_message: Optional[str] = Field(
        None,
        # "유저 추가 요청 문구"
        description="Additional user request or prompt message"
    )