import google.generativeai as genai
from openai import OpenAI
from ai.app.common.config import settings

# Gemini API 설정
if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)

# OpenAI API 설정
openai_client = None
if settings.OPENAI_API_KEY:
    openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)

def get_gemini_model(model_name: str = "gemini-1.5-flash"):
    """Gemini GenAI 모델을 반환합니다."""
    return genai.GenerativeModel(model_name)

def get_openai_client() -> OpenAI:
    """OpenAI API 클라이언트를 반환합니다."""
    return openai_client
