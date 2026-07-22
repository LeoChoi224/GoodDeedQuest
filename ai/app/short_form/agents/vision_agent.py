"""
Vision Agent - 연동 스켈레톤 (이슈 #85)

입력: state["media_keys"] (S3 key 리스트)
출력: (이 단계에서는 State에 파싱된 결과를 반영하지 않음 — 후속 이슈에서 처리)

사용 모델: Google Gemini Vision, LangChain 래퍼(get_gemini_model) 경유
(팀 컨벤션: common/llm.py의 get_openai_model/get_gemini_model을 통해서만 LLM 호출)

이 파일의 범위:
- S3에서 media_keys에 해당하는 미디어를 로드
- LangChain ChatGoogleGenerativeAI로 멀티모달 호출까지만 수행 (raw response 확인)
- 실패 시 예외 처리 뼈대

TODO(후속 이슈 #86 - 파싱): raw response를 VisionAnalysisResult
(scene_description, mood_tags, detected_objects)로 파싱해서
state["vision_results"]에 반영하는 로직 추가
"""
import base64
import os
import tempfile
from pathlib import Path

import boto3
from langchain_core.messages import HumanMessage

from ..state import ShortFormState
from ...common.config import settings
from ...common.llm import get_gemini_model

# TODO: ai/app/common 에 S3 client가 추가되면 그걸 재사용하도록 교체
S3_BUCKET = os.getenv("S3_BUCKET_NAME")
_s3_client = boto3.client("s3", region_name=os.getenv("AWS_REGION"))

# 이미지 확장자만 우선 지원. 영상(mp4 등)은 별도 처리 방식 결정 필요.
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
VIDEO_EXTENSIONS = {".mp4", ".mov"}

_MIME_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}


def _download_media_from_s3(media_key: str) -> str:
    """S3에서 media_key에 해당하는 파일을 로컬 임시 경로로 다운로드하고 경로를 반환"""
    suffix = Path(media_key).suffix
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp_path = tmp_file.name
    tmp_file.close()

    _s3_client.download_file(S3_BUCKET, media_key, tmp_path)
    return tmp_path


def _call_gemini_vision(local_path: str, media_key: str):
    """common/llm.py의 get_gemini_model()을 통해 이미지 분석 요청.
    지금은 raw response만 확인 (파싱은 후속 이슈)."""
    suffix = Path(media_key).suffix.lower()

    if suffix in VIDEO_EXTENSIONS:
        # TODO: 영상 입력 처리 방식 결정 (프레임 추출 후 이미지로 넘길지, 영상 그대로 처리할지)
        print(f"[VisionAgent] 영상 파일 감지({media_key}) - 처리 방식 미정, 스킵")
        return None

    if suffix not in IMAGE_EXTENSIONS:
        print(f"[VisionAgent] 지원하지 않는 확장자({suffix}), 스킵: {media_key}")
        return None

    with open(local_path, "rb") as f:
        image_base64 = base64.b64encode(f.read()).decode("utf-8")
    mime_type = _MIME_TYPES[suffix]

    prompt_text = (
        "이 이미지에 담긴 장면을 설명해줘. "
        "장면 설명, 분위기(감정) 태그, 주요 객체를 알려줘."
    )

    message = HumanMessage(
        content=[
            {"type": "text", "text": prompt_text},
            {"type": "image_url", "image_url": f"data:{mime_type};base64,{image_base64}"},
        ]
    )

    model = get_gemini_model(model_name=settings.DEFAULT_VISION_MODEL)
    response = model.invoke([message])
    return response


def vision_agent(state: ShortFormState) -> ShortFormState:
    print(f"[VisionAgent] media_keys={state['media_keys']}")

    for media_key in state["media_keys"]:
        local_path = None
        try:
            local_path = _download_media_from_s3(media_key)
            response = _call_gemini_vision(local_path, media_key)

            if response is not None:
                # 이 이슈 범위에서는 파싱 없이 raw response만 로그로 확인
                print(f"[VisionAgent] raw response for {media_key}:\n{response.content}")

        except Exception as e:
            # TODO(후속): 실패한 media_key를 모아서 state["error_message"]/status에 반영할지 결정
            print(f"[VisionAgent] {media_key} 처리 중 오류 발생: {e}")

        finally:
            if local_path and os.path.exists(local_path):
                os.remove(local_path)

    # TODO(파싱 이슈 #86): state["vision_results"]에 VisionAnalysisResult 리스트 반영
    return state