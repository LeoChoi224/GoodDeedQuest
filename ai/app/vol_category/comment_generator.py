from __future__ import annotations

import logging

from ai.app.common.llm import get_openai_model, invoke_gemini_fallback
from ai.app.vol_category.prompts import build_lacking_category_prompt, format_facilities_text
from ai.app.vol_category.schemas import LackingCategoryComment, LackingCategoryCommentRequest

logger = logging.getLogger(__name__)


def _build_fallback_comment(request: LackingCategoryCommentRequest) -> str:
    if request.recommended_facilities:
        facility_name = request.recommended_facilities[0].vol_name
        return (
            f"{request.region_name}은(는) 다른 지역에 비해 '{request.lacking_category}' 관련 봉사가 부족해요. "
            f"'{facility_name}' 같은 다른 지역 시설을 참고해보세요."
        )
    return f"{request.region_name}은(는) 다른 지역에 비해 '{request.lacking_category}' 관련 봉사가 부족해요."


def generate_lacking_category_comment(request: LackingCategoryCommentRequest) -> str:
    prompt = build_lacking_category_prompt()
    input_data = {
        "region_name": request.region_name,
        "lacking_category": request.lacking_category,
        "facilities_text": format_facilities_text(request.recommended_facilities),
    }

    try:
        llm = get_openai_model()
        structured_chain = prompt | llm.with_structured_output(LackingCategoryComment)
        result: LackingCategoryComment = structured_chain.invoke(input_data)

        if result is not None and result.comment and result.comment.strip():
            return result.comment.strip()

        raise ValueError("OpenAI가 빈 문구를 반환했습니다.")

    except Exception as exc:
        logger.warning(f"OpenAI 문구 생성 실패, Gemini 백업 모델로 페일오버 시도: {exc}")

    gemini_result = invoke_gemini_fallback(
        prompt=prompt,
        input_data=input_data,
        structured_schema=LackingCategoryComment,
    )

    if gemini_result is not None and getattr(gemini_result, "comment", "").strip():
        return gemini_result.comment.strip()

    logger.error("OpenAI/Gemini 모두 실패하여 규칙 기반 문구로 대체합니다.")
    return _build_fallback_comment(request)