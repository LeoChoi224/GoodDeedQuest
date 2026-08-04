from pydantic import BaseModel

class VerifyQuestRequest(BaseModel):
    quest_id: int
    quest_title: str
    quest_description: str
    media_urls: list[str]
    is_video: bool = False


class VerifyChallengeRequest(BaseModel):
    media_url: str
    code: str
    