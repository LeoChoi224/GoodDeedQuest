"""
Vision Agent

입력: state["media_keys"] (S3 key 리스트)
출력: state["vision_results"] (씬 설명, 분위기 태그 등)

실제 구현 시 S3에서 이미지/영상을 받아 Vision LLM(예: Claude, GPT-4V)에
전달해 장면을 분석. 지금은 더미 응답으로 그래프 흐름만 검증.
"""
from ..state import ShortFormState, VisionAnalysisResult


def vision_agent(state: ShortFormState) -> ShortFormState:
    print(f"[VisionAgent] media_keys={state['media_keys']}")

    # TODO: 실제 Vision LLM 호출로 교체 (이슈 1에서 작업)
    dummy_results: list[VisionAnalysisResult] = [
        {
            "media_key": key,
            "scene_description": "더미 장면 설명입니다.",
            "mood_tags": ["활기찬", "밝은"],
            "detected_objects": ["사람", "쓰레기봉투"],
        }
        for key in state["media_keys"]
    ]

    state["vision_results"] = dummy_results
    return state