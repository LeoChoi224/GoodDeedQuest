import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

ROOT_DIR = Path(__file__).resolve().parents[3]
load_dotenv(ROOT_DIR / ".env")

class AISettings(BaseSettings):
    PROJECT_NAME: str = "Good Deed Quest AI Service"
    
    # OpenAI & Gemini keys
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    # Model configs
    DEFAULT_LLM_MODEL: str = os.getenv("DEFAULT_LLM_MODEL", "gpt-4o")
    DEFAULT_VISION_MODEL: str = os.getenv("DEFAULT_VISION_MODEL", "gemini-2.5-flash")

    # Embedding configs
    DEFAULT_EMBEDDING_PROVIDER: str = os.getenv("DEFAULT_EMBEDDING_PROVIDER", "openai")
    DEFAULT_OPENAI_EMBEDDING_MODEL: str = os.getenv("DEFAULT_OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    DEFAULT_GEMINI_EMBEDDING_MODEL: str = os.getenv("DEFAULT_GEMINI_EMBEDDING_MODEL", "models/text-embedding-004")

    # Pydantic Settings 자동화 설정
    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore" 

settings = AISettings()
