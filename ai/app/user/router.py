from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

from ai.app.user.embedding import embed_user_profile

router = APIRouter(prefix="/ai/user", tags=["AI User"])


class UserEmbedRequest(BaseModel):
    category: Optional[List[str]] = None
    active_time: Optional[List[str]] = None
    preferred_difficulty: Optional[str] = None
    age: Optional[int] = None


@router.post("/embed")
def ai_user_embed(req: UserEmbedRequest):
    vector = embed_user_profile(
        req.category, req.active_time, req.preferred_difficulty, req.age
    )
    return {"success": True, "data": {"embedding": vector}}