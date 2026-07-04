import os
from pydantic_settings import BaseSettings

class AISettings(BaseSettings):
    PROJECT_NAME: str = "Good Deed Quest AI Service"
    
    # OpenAI & Gemini keys
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    # Model configs
    DEFAULT_LLM_MODEL: str = os.getenv("DEFAULT_LLM_MODEL", "gpt-4o")
    DEFAULT_VISION_MODEL: str = os.getenv("DEFAULT_VISION_MODEL", "gemini-1.5-flash")

    class Config:
        case_sensitive = True

settings = AISettings()
