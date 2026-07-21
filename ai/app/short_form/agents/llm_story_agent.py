"""
LLM Story Agent

입력: state["vision_results"], state["quest_title"], state["user_name"],
      state["edited_captions"] (프론트에서 이미 편집한 캡션이 있으면 그걸 우선 사용)
출력: state["generated_captions"] (온스크린 자막 텍스트, 씬별)

주의: TTS 없음. 나레이션 음성이 아니라 화면에 얹을 텍스트 자막을 생성.
"""
from ..state import ShortFormState


def llm_story_agent(state: ShortFormState) -> ShortFormState:
    # 프론트에서 이미 편집한 캡션을 넘겨받았으면 재생성 없이 그대로 사용
    if state.get("edited_captions"):
        print("[LlmStoryAgent] edited_captions 존재 -> 재생성 스킵")
        state["generated_captions"] = state["edited_captions"]
        return state

    print(f"[LlmStoryAgent] quest_title={state['quest_title']}, user_name={state['user_name']}")

    # TODO: 실제 LLM 호출로 교체 (이슈 3에서 작업, vision_results의 scene_description 활용)
    dummy_captions = [
        f"{state['user_name']}님의 '{state['quest_title']}' 완수!",
        "작은 선행이 큰 변화를 만듭니다.",
    ]

    state["generated_captions"] = dummy_captions
    return state