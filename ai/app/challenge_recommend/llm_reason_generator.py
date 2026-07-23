from __future__ import annotations

# =========================================================
# [확인 및 검토할 사항]
#
# 1. 이 파일의 역할
#    - prompts.py가 만든 System/User Prompt를 실제 OpenAI Chat Model에 전달합니다.
#    - LLM의 JSON 응답을 Pydantic Schema로 검증한 뒤 nodes.py 표준 결과로 반환합니다.
#
# 2. 환경변수
#    - OPENAI_API_KEY: 실제 OpenAI API Key
#    - DEFAULT_LLM_MODEL: 사용할 모델명 (기본값: gpt-4o)
#
# 3. Fallback
#    - 이 클래스는 LLM 오류를 숨기지 않고 예외를 발생시킵니다.
#    - 예외를 규칙 기반 추천 이유로 대체하는 책임은 nodes.py에 있습니다.
#
# 4. 테스트
#    - 테스트에서는 chat_model을 주입하여 실제 API를 호출하지 않습니다.
#    - 운영에서는 chat_model을 생략하면 환경변수로 ChatOpenAI를 생성합니다.
#
# 5. 개인정보와 로그
#    - Prompt와 원본 LLM 응답에는 후보 정보가 포함될 수 있습니다.
#    - 운영 로그에 그대로 출력하지 않도록 주의합니다.
# =========================================================

import json
import os
from typing import Any, Protocol, Sequence, runtime_checkable

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, ConfigDict, Field

from .nodes import (
    RecommendationReasonGenerationResult,
)
from .prompts import (
    build_recommendation_reason_prompt,
    combine_prompt_for_debug,
)
from .schemas import (
    CandidateRecommendationReason,
    ScoredRecommendationCandidate,
)
from .state import RecommendationState


DEFAULT_LLM_MODEL = "gpt-4o"
DEFAULT_LLM_TEMPERATURE = 0.0
DEFAULT_LLM_TIMEOUT_SECONDS = 30.0
DEFAULT_LLM_MAX_RETRIES = 1


class RecommendationReasonLLMError(RuntimeError):
    """LLM 추천 이유 생성 또는 응답 파싱 실패를 나타냅니다."""


class RecommendationReasonResponse(BaseModel):
    """LLM이 반환해야 하는 최상위 JSON 구조입니다."""

    model_config = ConfigDict(extra="ignore")

    reasons: list[CandidateRecommendationReason] = Field(
        default_factory=list,
        description="후보별 추천 이유 목록",
    )


@runtime_checkable
class ChatModel(Protocol):
    """실제 Chat Model과 테스트 Fake가 따라야 하는 최소 인터페이스입니다."""

    def invoke(self, input: Any, **kwargs: Any) -> Any:
        """메시지를 전달하고 LLM 응답 객체를 반환합니다."""


def _extract_text_content(response: Any) -> str:
    """LangChain 응답 객체에서 문자열 본문을 추출합니다."""

    content = getattr(response, "content", response)

    if isinstance(content, str):
        normalized = content.strip()

        if normalized:
            return normalized

        raise RecommendationReasonLLMError(
            "LLM이 빈 응답을 반환했습니다."
        )

    # 일부 Chat Model은 content를 텍스트 블록 목록으로 반환할 수 있습니다.
    if isinstance(content, list):
        text_parts: list[str] = []

        for block in content:
            if isinstance(block, str):
                text_parts.append(block)
                continue

            if isinstance(block, dict):
                text = block.get("text")

                if isinstance(text, str):
                    text_parts.append(text)

        normalized = "".join(text_parts).strip()

        if normalized:
            return normalized

    raise RecommendationReasonLLMError(
        "LLM 응답에서 문자열 내용을 읽을 수 없습니다."
    )


def _strip_json_code_fence(raw_response: str) -> str:
    """LLM이 실수로 붙인 JSON Markdown 코드 블록을 제거합니다."""

    normalized = raw_response.strip()

    if not normalized.startswith("```"):
        return normalized

    lines = normalized.splitlines()

    if lines and lines[0].strip().lower() in {
        "```",
        "```json",
    }:
        lines = lines[1:]

    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]

    return "\n".join(lines).strip()


def _parse_reason_response(
    raw_response: str,
) -> RecommendationReasonResponse:
    """LLM JSON 문자열을 검증된 추천 이유 응답으로 변환합니다."""

    normalized = _strip_json_code_fence(raw_response)

    try:
        parsed_json = json.loads(normalized)
    except json.JSONDecodeError as exc:
        raise RecommendationReasonLLMError(
            "LLM 추천 이유 응답이 유효한 JSON이 아닙니다."
        ) from exc

    try:
        return RecommendationReasonResponse.model_validate(
            parsed_json
        )
    except Exception as exc:
        raise RecommendationReasonLLMError(
            "LLM 추천 이유 JSON이 요구된 Schema와 일치하지 않습니다."
        ) from exc


class OpenAIRecommendationReasonGenerator:
    """OpenAI Chat Model을 사용하는 실제 추천 이유 생성기입니다."""

    def __init__(
        self,
        *,
        chat_model: ChatModel | None = None,
        api_key: str | None = None,
        model_name: str | None = None,
        temperature: float = DEFAULT_LLM_TEMPERATURE,
        timeout_seconds: float = DEFAULT_LLM_TIMEOUT_SECONDS,
        max_retries: int = DEFAULT_LLM_MAX_RETRIES,
    ) -> None:
        """주입된 Chat Model 또는 환경변수로 실제 모델을 준비합니다."""

        if chat_model is not None:
            self._chat_model = chat_model
            return

        resolved_api_key = (
            api_key
            or os.getenv("OPENAI_API_KEY", "").strip()
        )

        if not resolved_api_key:
            raise ValueError(
                "OPENAI_API_KEY가 설정되지 않았습니다."
            )

        resolved_model_name = (
            model_name
            or os.getenv(
                "DEFAULT_LLM_MODEL",
                DEFAULT_LLM_MODEL,
            ).strip()
            or DEFAULT_LLM_MODEL
        )

        self._chat_model = ChatOpenAI(
            api_key=resolved_api_key,
            model=resolved_model_name,
            temperature=temperature,
            timeout=timeout_seconds,
            max_retries=max_retries,
        )

    def generate(
        self,
        *,
        state: RecommendationState,
        candidates: Sequence[ScoredRecommendationCandidate],
    ) -> RecommendationReasonGenerationResult:
        """정렬된 후보의 추천 이유를 실제 LLM으로 생성합니다."""

        prompt_bundle = build_recommendation_reason_prompt(
            request=state["request"],
            candidates=candidates,
        )

        messages = [
            SystemMessage(content=prompt_bundle.system_prompt),
            HumanMessage(content=prompt_bundle.user_prompt),
        ]

        try:
            response = self._chat_model.invoke(messages)
        except Exception as exc:
            raise RecommendationReasonLLMError(
                "OpenAI 추천 이유 생성 호출에 실패했습니다."
            ) from exc

        raw_response = _extract_text_content(response)
        parsed_response = _parse_reason_response(raw_response)

        return RecommendationReasonGenerationResult(
            reasons=parsed_response.reasons,
            prompt=combine_prompt_for_debug(prompt_bundle),
            raw_response=raw_response,
        )


def create_default_reason_generator(
) -> OpenAIRecommendationReasonGenerator | None:
    """API Key가 있을 때만 운영용 LLM 생성기를 만듭니다.

    API Key가 없는 테스트·로컬 환경에서는 None을 반환합니다.
    Graph는 None을 전달받으면 기존 규칙 기반 Fallback을 사용합니다.
    """

    api_key = os.getenv("OPENAI_API_KEY", "").strip()

    # .env 예시값을 실제 Key로 오인하지 않습니다.
    if not api_key or api_key.upper() == "YOUR_KEY":
        return None

    return OpenAIRecommendationReasonGenerator(
        api_key=api_key,
    )
