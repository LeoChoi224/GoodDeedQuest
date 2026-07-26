"""
Validation Agent

입력: state["generated_captions"], state["bgm_match"]
출력: state["validation_passed"], state["validation_errors"]

검증 항목 예시: 자막 길이 제한, 부적절 표현 필터링, bgm_id 존재 여부 등.
검증 실패 시 status를 FAILED로 바꾸고 error_message를 채워서
그래프가 FFmpeg Render Agent로 넘어가지 않도록 분기.
(기본 검증 로직은 있지만, 부적절 표현 필터링 등은 #92에서 보완 예정)
"""
from ..state import ShortFormState

# #91에서 값 확정 완료 (씬 1개당 자막 전체 글자수 기준, 변경 없음 - VALIDATION_CRITERIA.md 참고)
MAX_CAPTION_LENGTH = 60


def validation_agent(state: ShortFormState) -> ShortFormState:
    errors: list[str] = []

    for idx, caption in enumerate(state["generated_captions"]):
        if len(caption) > MAX_CAPTION_LENGTH:
            errors.append(
                f"씬 {idx + 1}: 자막 길이 초과 ({len(caption)}자 / 최대 {MAX_CAPTION_LENGTH}자): {caption[:20]}..."
            )

    if not state.get("bgm_match") or not state["bgm_match"].get("bgm_id"):
        errors.append("BGM 매칭 결과 없음 (bgm_id 누락)")

    state["validation_errors"] = errors
    state["validation_passed"] = len(errors) == 0

    if not state["validation_passed"]:
        state["status"] = "FAILED"
        state["error_message"] = "; ".join(errors)
        print(f"[ValidationAgent] 검증 실패: {errors}")
    else:
        print("[ValidationAgent] 검증 통과")

    return state