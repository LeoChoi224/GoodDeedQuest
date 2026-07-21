"""
FFmpeg Render Agent

입력: state["media_keys"], state["generated_captions"], state["bgm_match"]
출력: state["rendered_video_key"] (렌더링된 최종 영상의 S3 key)

실제 구현 시:
1. S3에서 media_keys, BGM 파일 다운로드 (또는 presigned URL 스트리밍)
2. FFmpeg으로 이미지/영상 + 텍스트 오버레이(자막) + BGM 합성
3. 결과 파일을 S3에 업로드하고 key를 반환
TTS/나레이션 음성 트랙 없음 -- 오디오 트랙은 BGM만 사용.
"""
import subprocess  # noqa: F401  (이슈 5에서 실제 사용)
from ..state import ShortFormState


def render_agent(state: ShortFormState) -> ShortFormState:
    if state["status"] == "FAILED":
        print("[RenderAgent] 이전 단계 실패로 렌더링 스킵")
        return state

    print(
        f"[RenderAgent] media_keys={state['media_keys']}, "
        f"captions={state['generated_captions']}, bgm_id={state['bgm_match']['bgm_id']}"
    )

    # TODO: 실제 FFmpeg subprocess 호출 + S3 업로드로 교체 (이슈 5에서 작업)
    dummy_video_key = f"shortform/{state['shorts_id']}/render_result.mp4"

    state["rendered_video_key"] = dummy_video_key
    state["status"] = "COMPLETED"
    return state