from functools import lru_cache
from pathlib import Path
from pydantic import PostgresDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[3]
ENV_FILE = ROOT_DIR / ".env"


class Settings(BaseSettings):
    
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )
    
    PROJECT_NAME: str = "Good Deed Quest API"
    API_V1_STR: str = "/api/v1"

    # Security
    SECRET_KEY: SecretStr #env 파일에 있고 5행부터 16번 행이 환경변수 가져오는 코드리 이게 더 안전함 노출 x
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    # Database
    DATABASE_URL: PostgresDsn #env 파일에 있고 5행부터 16번 행이 환경변수 가져오는 코드리 이게 더 안전함 노출 x

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0" # 보안상 문제없어서 안바꿈 비번 드가면 나중에 환경변수에 넣고 명시한거 지우세요

    # AI Service URL
    AI_SERVICE_URL: str = "http://localhost:8001" # 보안상 문제없어서 안바꿈

    # AWS S3
    AWS_REGION: str = "ap-northeast-2"
    AWS_ACCESS_KEY_ID: SecretStr # 위와같은 이유로 바꿈 .env 파일에 적으세요
    AWS_SECRET_ACCESS_KEY: SecretStr # 위와같은 이유로 바꿈 .env 파일에 적으세요
    S3_BUCKET_NAME: str = ""

    
    DEBUG: bool = False #환경변수에 True로 바꾸면 개발시 편함
    JWT_ALGORITHM: str = "HS256"
    CORS_ORIGINS: list[str] = ["http://localhost:8081"]
    

@lru_cache # 같은요청 캐시해놔서 속도 빠름 Depend 안에 넣을 수 있고 import 시 자동실행 막음 기존에는 그냥 자동시행 시도임
def get_setting() -> Settings:
    return Settings()