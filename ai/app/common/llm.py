from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from .config import settings

def get_openai_model(model_name: str = None, temperature: float = 0.7) -> ChatOpenAI:
    """LangChain의 ChatOpenAI 객체를 반환합니다."""
    if not settings.OPENAI_API_KEY:
        raise ValueError("OpenAI API key is not configured.")
        
    target_model = model_name or settings.DEFAULT_LLM_MODEL
    return ChatOpenAI(
        openai_api_key=settings.OPENAI_API_KEY,
        model=target_model,
        temperature=temperature
    )

def get_gemini_model(model_name: str = None, temperature: float = 0.7) -> ChatGoogleGenerativeAI:
    """LangChain의 ChatGoogleGenerativeAI 객체를 반환합니다."""
    if not settings.GEMINI_API_KEY:
        raise ValueError("Gemini API key is not configured.")
    
    target_model = model_name or settings.DEFAULT_VISION_MODEL
        
    return ChatGoogleGenerativeAI(
        google_api_key=settings.GEMINI_API_KEY,
        model=target_model,
        temperature=temperature
    )