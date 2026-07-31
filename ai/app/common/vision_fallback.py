"""Vision 모델 호출 공용 헬퍼 (Gemini 우선 시도, 실패 시 OpenAI로 폴백).

Gemini API 오류(할당량 초과 429, 서버 과부하 503, 타임아웃 504 등) 발생 시
OpenAI로 재시도한다. 그 외 예외(예: API 키 미설정)는 fallback 대상이 아니므로
그대로 raise한다.
"""
import logging

from google.genai.errors import APIError  # ⭐ 수정: 실제로 발생하는 예외 타입
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
    """Gemini Vision 모델로 먼저 시도하고, API 오류(할당량 초과/과부하/타임아웃 등) 시
    OpenAI Vision 모델로 재시도한다. 두 경우 모두 정규화된 텍스트를 반환한다."""
    try:
        gemini_model = get_gemini_model(temperature=temperature)
        response = gemini_model.invoke([HumanMessage(content=content)])
        logger.info("Vision response from: gemini")
        return _normalize_response_content(response.content)
    except (APIError, ChatGoogleGenerativeAIError) as e:
        # ⭐ 수정: langchain_google_genai가 google.genai의 4xx ClientError(예: 429
        # RESOURCE_EXHAUSTED)는 자체적으로 감싸서 ChatGoogleGenerativeAIError로 다시 던지지만,
        # 5xx ServerError(예: 503 UNAVAILABLE, 504 DEADLINE_EXCEEDED)는 감싸지 않고 원본
        # google.genai.errors.APIError를 그대로 던진다 - 두 타입이 서로 다른 클래스 계층이라
        # 기존엔 (ChatGoogleGenerativeAIError만 잡거나 / APIError만 잡거나) 둘 중 하나만
        # 잡으면 나머지 절반은 여전히 vision_agent의 바깥 try/except로 새어나가 폴백 없이
        # 스킵됐다. 두 예외 타입을 모두 잡아야 429/503/504 전부 OpenAI로 폴백된다.
        logger.warning(f"Gemini vision 호출 실패, OpenAI로 폴백합니다: {e}")
        openai_model = get_openai_model(temperature=temperature)
        openai_content = _adapt_content_for_openai(content)
        response = openai_model.invoke([HumanMessage(content=openai_content)])
        logger.info("Vision response from: openai")
        return _normalize_response_content(response.content)
