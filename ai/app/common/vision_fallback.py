"""Vision 모델 호출 공용 헬퍼 (Gemini 우선 시도, 할당량 초과 시 OpenAI로 폴백).

Gemini Free tier 일일 한도 초과(429 RESOURCE_EXHAUSTED) 발생 시에만 OpenAI로
재시도한다. 그 외 예외는 fallback 대상이 아니므로 그대로 raise한다.
"""
import logging

from langchain_core.messages import HumanMessage
from langchain_google_genai.chat_models import ChatGoogleGenerativeAIError

from ai.app.common.llm import get_gemini_model, get_openai_model

logger = logging.getLogger(__name__)


def _adapt_content_for_openai(content: list[dict]) -> list[dict]:
    """Gemini 스타일 image_url 블록(문자열)을 OpenAI 스타일(dict)로 변환한다.

    Gemini: {"type": "image_url", "image_url": "data:image/jpeg;base64,..."}
    OpenAI: {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}}
    """
    adapted = []
    for block in content:
        if isinstance(block, dict) and block.get("type") == "image_url" and isinstance(block.get("image_url"), str):
            adapted.append({"type": "image_url", "image_url": {"url": block["image_url"]}})
        else:
            adapted.append(block)
    return adapted


def _normalize_response_content(content) -> str:
    """response.content가 str이거나 [{'type': 'text', 'text': '...'}] 형태의 리스트일 수 있음.
    두 경우 모두 처리해서 순수 텍스트만 반환."""
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        texts = [
            block.get("text", "")
            for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        ]
        return "\n".join(texts)

    return str(content)


def invoke_vision_with_fallback(content: list[dict], temperature: float = 0.7) -> str:
    """Gemini Vision 모델로 먼저 시도하고, 할당량 초과(429/RESOURCE_EXHAUSTED) 시
    OpenAI Vision 모델로 재시도한다. 두 경우 모두 정규화된 텍스트를 반환한다."""
    try:
        gemini_model = get_gemini_model(temperature=temperature)
        response = gemini_model.invoke([HumanMessage(content=content)])
        logger.info("Vision response from: gemini")
        return _normalize_response_content(response.content)
    except ChatGoogleGenerativeAIError as e:
        error_str = str(e)
        if "RESOURCE_EXHAUSTED" not in error_str and "429" not in error_str:
            raise

        logger.warning(f"Gemini vision 할당량 초과, OpenAI로 폴백합니다: {error_str}")
        openai_model = get_openai_model(temperature=temperature)
        openai_content = _adapt_content_for_openai(content)
        response = openai_model.invoke([HumanMessage(content=openai_content)])
        logger.info("Vision response from: openai")
        return _normalize_response_content(response.content)
