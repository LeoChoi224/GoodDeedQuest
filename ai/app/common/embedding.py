import logging
from typing import List

from langchain_openai import OpenAIEmbeddings
from langchain_google_genai import GoogleGenAIEmbeddings

from ai.app.common.config import settings

logger = logging.getLogger(__name__)


def _embed_openai(texts: List[str], model: str) -> List[List[float]]:
    """
    LangChain의 호출하여 입력받은 텍스트 리스트를 임베딩 벡터 리스트로 변환합니다.
    """
    if not settings.OPENAI_API_KEY:
        raise ValueError("OpenAI API key is not configured.")
    
    embeddings_model = OpenAIEmbeddings(
        openai_api_key=settings.OPENAI_API_KEY,
        model=model
    )
    return embeddings_model.embed_documents(texts)


def _embed_gemini(texts: List[str], model: str) -> List[List[float]]:
    """
    LangChain의 GoogleGenAIEmbeddings를 호출하여 입력받은 텍스트 리스트를 임베딩 벡터 리스트로 변환합니다.
    """
    if not settings.GEMINI_API_KEY:
        raise ValueError("Gemini API key is not configured.")
    
    embeddings_model = GoogleGenAIEmbeddings(
        google_api_key=settings.GEMINI_API_KEY,
        model=model
    )
    return embeddings_model.embed_documents(texts)


def get_embeddings(texts: List[str], provider: str = None, model: str = None) -> List[List[float]]:
    """
    여러 텍스트의 임베딩 추출 (실패 시 반대 프로바이더로 자동 Fallback)

    Args:
        texts (List[str]): 임베딩할 텍스트 리스트
        provider (str, optional): 사용할 API 제공자 ("openai" 또는 "gemini")
        model (str, optional): 사용할 임베딩 모델명    
    Returns:
        List[List[float]]: 각 텍스트에 매칭되는 임베딩 벡터 목록
    """
    if not texts:
        return []
        
    provider = provider or settings.DEFAULT_EMBEDDING_PROVIDER
    
    # 1차 시도
    try:
        if provider == "openai":
            target_model = model or settings.DEFAULT_OPENAI_EMBEDDING_MODEL
            return _embed_openai(texts, target_model)
        elif provider == "gemini":
            target_model = model or settings.DEFAULT_GEMINI_EMBEDDING_MODEL
            return _embed_gemini(texts, target_model)
        else:
            raise ValueError(f"Unknown embedding provider: {provider}")
            
    except Exception as e:
        logger.warning(f"Failed using primary '{provider}': {e}. Trying fallback...")
        
        # 폴백 시도 (반대 프로바이더 적용)
        fallback_provider = "gemini" if provider == "openai" else "openai"
        try:
            if fallback_provider == "openai":
                fallback_model = settings.DEFAULT_OPENAI_EMBEDDING_MODEL
                return _embed_openai(texts, fallback_model)
            elif fallback_provider == "gemini":
                fallback_model = settings.DEFAULT_GEMINI_EMBEDDING_MODEL
                return _embed_gemini(texts, fallback_model)
        except Exception as fallback_err:
            logger.error(f"Fallback '{fallback_provider}' also failed: {fallback_err}")
            raise RuntimeError("Both embedding providers failed.") from fallback_err


def get_embedding(text: str, provider: str = None, model: str = None) -> List[float]:
    """
    단일 텍스트의 Embedding Vector를 가져옵니다.
    
    Args:
        text (str): 임베딩할 텍스트
        provider (str, optional): 사용할 API 제공자 ("openai" 또는 "gemini")
        model (str, optional): 사용할 임베딩 모델명 
    Returns:
        List[float]: 임베딩 벡터 (Float 리스트)
    """
    results = get_embeddings([text], provider=provider, model=model)
    return results[0] if results else []


if __name__ == "__main__":
    # 로컬에서 단독 실행 시 동작을 검증하기 위한 간단한 테스트 코드
    import sys
    logging.basicConfig(level=logging.INFO)
    
    test_text = "정운아~ 정운아~ 컴퓨터실에서 뭐 먹지 말랬지!"
    print(f"테스트 문장: {test_text}")
    
    # 1. 기본 프로바이더 테스트
    print(f"\n--- 기본 프로바이더 ({settings.DEFAULT_EMBEDDING_PROVIDER}) 테스트 ---")
    try:
        vec = get_embedding(test_text)
        print(f"성공! 벡터 차원 수: {len(vec)}")
        print(f"벡터 프리뷰 (앞의 5개 값): {vec[:5]}")
    except Exception as ex:
        print(f"실패: {ex}")
        
    # 2. 강제 OpenAI 테스트
    print("\n--- OpenAI 테스트 ---")
    try:
        vec_openai = get_embedding(test_text, provider="openai")
        print(f"성공! 벡터 차원 수: {len(vec_openai)}")
        print(f"벡터 프리뷰 (앞의 5개 값): {vec_openai[:5]}")
    except Exception as ex:
        print(f"실패: {ex}")
    # 3. 강제 Gemini 테스트
    print("\n--- Gemini 테스트 ---")
    try:
        vec_gemini = get_embedding(test_text, provider="gemini")
        print(f"성공! 벡터 차원 수: {len(vec_gemini)}")
        print(f"벡터 프리뷰 (앞의 5개 값): {vec_gemini[:5]}")
    except Exception as ex:
        print(f"실패: {ex}")