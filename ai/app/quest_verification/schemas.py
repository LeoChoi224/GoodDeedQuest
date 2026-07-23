from pydantic import BaseModel

class VerifyQuestRequest(BaseModel):
    quest_id: int
    quest_title: str
    quest_description: str
    media_url: str