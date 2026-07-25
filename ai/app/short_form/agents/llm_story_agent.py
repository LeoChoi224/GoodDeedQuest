"""
LLM Story Agent

입력: state["vision_results"], state["quest_title"], state["user_name"],
      state["edited_captions"] (프론트에서 이미 편집한 캡션이 있으면 그걸 우선 사용)
출력: state["generated_captions"] (온스크린 자막 텍스트, 씬별)

주의: TTS 없음. 나레이션 음성이 아니라 화면에 얹을 텍스트 자막을 생성.
"""
from langchain_core.messages import HumanMessage

from ..state import ShortFormState
from ...common.llm import get_openai_model
from ...common.config import settings


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

        # TODO(#90): raw response를 씬별 자막 리스트로 파싱
        state["generated_captions"] = [str(response.content)]

    except Exception as e:
        print(f"[LlmStoryAgent] LLM 호출 실패: {e}")
        state["error_message"] = f"LLM Story Agent 호출 실패: {e}"
        state["status"] = "FAILED"

    return state