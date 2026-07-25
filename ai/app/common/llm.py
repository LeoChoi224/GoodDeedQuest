import logging
from typing import Dict, Any, Type
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

logger = logging.getLogger(__name__)

from ai.app.common.config import settings

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

def invoke_gemini_fallback(
    prompt: ChatPromptTemplate,
    input_data: Dict[str, Any],
    structured_schema: Type[BaseModel],
    temperature: float = 0.7
) -> BaseModel:
    """
    OpenAI 통신/인프라 장애(RateLimit, Timeout, 500/503 에러 등) 발생 시 
    except 구문 내부에서 호출되어 Google Gemini 모델로 자동 페일오버(Model Failover)를 수행하는 백업 전용 함수입니다.
    """
    logger.warning("OpenAI 통신 장애로 인해 2순위 Google Gemini 백업 모델로 페일오버를 수행합니다.")
    try:
        gemini_llm = get_gemini_model(model_name="gemini-1.5-flash", temperature=temperature)
        structured_gemini_chain = prompt | gemini_llm.with_structured_output(structured_schema)
        
        response = structured_gemini_chain.invoke(input_data)
        logger.info("Google Gemini 백업 모델을 통한 진성 AI 데이터 연산 완료.")
        return response
    except Exception as gemini_err:
        logger.error(f"Google Gemini 백업 모델 통신마저 실패: {gemini_err}")
        return None