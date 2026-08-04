from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate

from ai.app.vol_category.schemas import RecommendedFacility

SYSTEM_PROMPT = (
    "당신은 지역 봉사활동 플랫폼 '선행퀘스트'의 안내 도우미입니다. "
    "주어진 지역의 부족한 봉사 카테고리와, 다른 지역의 추천 시설 정보를 바탕으로 "
    "사용자에게 보여줄 안내 문구를 한국어로 1~2문장 작성하세요. "
    "친근하고 자연스러운 말투를 사용하되, 과장하지 말고 제공된 정보만 사용하세요. "
    "이모지는 사용하지 마세요."
)

USER_PROMPT_TEMPLATE = (
    "지역명: {region_name}\n"
    "부족한 봉사 카테고리: {lacking_category}\n"
    "다른 지역의 추천 시설:\n{facilities_text}\n\n"
    "위 정보를 바탕으로 '{region_name}'에는 '{lacking_category}' 관련 봉사가 상대적으로 부족하다는 점을 "
    "알려주고, 추천 시설이 있다면 참고용으로 자연스럽게 언급하는 안내 문구를 작성하세요. "
    "추천 시설이 없다면 시설 언급 없이 부족하다는 점만 안내하세요."
)


def format_facilities_text(facilities: list[RecommendedFacility]) -> str:
    if not facilities:
        return "(참고할 만한 다른 지역 시설 없음)"
    lines = [f"- {f.vol_name} ({f.region_name})" for f in facilities]
    return "\n".join(lines)


def build_lacking_category_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            ("human", USER_PROMPT_TEMPLATE),
        ]
    )