"""
LLM Story Agent

입력: state["vision_results"], state["quest_title"], state["user_name"],
      state["edited_captions"] (프론트에서 이미 편집한 캡션이 있으면 그걸 우선 사용)
출력: state["generated_captions"] (온스크린 자막 텍스트, 씬별)

주의: TTS 없음. 나레이션 음성이 아니라 화면에 얹을 텍스트 자막을 생성.
"""
import re

from langchain_core.messages import HumanMessage

from ..state import ShortFormState
from ...common.llm import get_openai_model
from ...common.config import settings

# "1. "내용"" 또는 "1. 내용" 형태의 번호 매김 패턴
_NUMBERED_LINE_PATTERN = re.compile(r'^\s*\d+\.\s*"?(.+?)"?\s*$', re.MULTILINE)


def _parse_story_response(raw_text: str, scene_count: int, user_name: str, quest_title: str) -> list[str]:
    """LLM raw response(자유 형식 텍스트)를 씬별 캡션 리스트로 파싱.

    1차: 번호 매김 패턴("1. "내용"" / "1. 내용")으로 추출
    2차(1차 실패 시): 개행 또는 마침표(". ") 기준 단순 split
    최종 fallback(2차도 실패 시): 기본 문구로 scene_count개 채움
    """
    captions = [c.strip() for c in _NUMBERED_LINE_PATTERN.findall(raw_text) if c.strip()]

    if not captions:
        parts = re.split(r'\n+|\.\s+', raw_text)
        captions = [p.strip() for p in parts if p.strip()]

    if not captions:
        # TODO: 아래 기본 문구는 임시 예시이며 추후 조정 가능
        captions = [f"{user_name}님의 '{quest_title}' 완수!" for _ in range(scene_count)]

    return captions


def _fit_caption_count(captions: list[str], scene_count: int) -> list[str]:
    """캡션 리스트 길이를 scene_count에 맞춤 (많으면 앞에서부터 자르고, 적으면 마지막 캡션을 반복해서 채움)"""
    if len(captions) > scene_count:
        return captions[:scene_count]
    if len(captions) < scene_count:
        captions = captions + [captions[-1]] * (scene_count - len(captions))
    return captions


def _build_story_prompt(state: ShortFormState) -> str:
    scene_descriptions = "\n".join(
        f"- {r['scene_description']}" for r in state.get("vision_results", [])
    )
    return f"""당신은 선행 인증 숏폼 영상의 온스크린 자막을 작성하는 작가입니다.

사용자 이름: {state['user_name']}
퀘스트 제목: {state['quest_title']}
장면 설명:
{scene_descriptions}

위 정보를 바탕으로, 영상에 표시할 짧고 임팩트 있는 온스크린 자막 문구들을 작성해주세요.
나레이션 음성이 아니라 화면에 텍스트로 얹는 자막입니다. 간결하고 감동적인 톤으로 작성하세요.
"""


def llm_story_agent(state: ShortFormState) -> ShortFormState:
    # 프론트에서 이미 편집한 캡션을 넘겨받았으면 재생성 없이 그대로 사용
    if state.get("edited_captions"):
        print("[LlmStoryAgent] edited_captions 존재 -> 재생성 스킵")
        state["generated_captions"] = state["edited_captions"]
        return state

    print(f"[LlmStoryAgent] quest_title={state['quest_title']}, user_name={state['user_name']}")

    prompt = _build_story_prompt(state)

    try:
        model = get_openai_model(model_name=settings.DEFAULT_STORY_MODEL)
        response = model.invoke([HumanMessage(content=prompt)])
        print(f"[LlmStoryAgent] raw response: {response.content}")

        scene_count = len(state.get("vision_results", [])) or 1
        captions = _parse_story_response(
            str(response.content), scene_count, state["user_name"], state["quest_title"]
        )
        captions = _fit_caption_count(captions, scene_count)
        captions = [c[:settings.MAX_CAPTION_LENGTH] for c in captions]

        state["generated_captions"] = captions

    except Exception as e:
        print(f"[LlmStoryAgent] LLM 호출 실패: {e}")
        state["error_message"] = f"LLM Story Agent 호출 실패: {e}"
        state["status"] = "FAILED"

    return state