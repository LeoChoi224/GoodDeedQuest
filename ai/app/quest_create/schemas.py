from typing import Optional

from pydantic import BaseModel


class EvaluateQuestRequest(BaseModel):
    quest_title: str
    quest_description: str
    category_name: str


class EvaluateQuestResponse(BaseModel):
    
    accepted: bool
    reason: str
    difficulty: Optional[str] = None
    intensity: Optional[int] = None
    embedding: Optional[list[float]] = None
