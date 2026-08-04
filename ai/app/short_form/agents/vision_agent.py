"""
Vision Agent - Gemini 연동 + 응답 파싱 (이슈 #85, #86)

입력: state["media_keys"] (S3 key 리스트)
출력: state["vision_results"] (VisionAnalysisResult 리스트)

사용 모델: Google Gemini Vision, LangChain 래퍼(get_gemini_model) 경유
(팀 컨벤션: common/llm.py의 get_openai_model/get_gemini_model을 통해서만 LLM 호출)

이 파일의 범위:
- S3에서 media_keys에 해당하는 미디어를 로드
- LangChain ChatGoogleGenerativeAI로 멀티모달 호출 (JSON 형식 응답 요청)
- raw response를 VisionAnalysisResult로 파싱해 state["vision_results"]에 반영
- 실패 시 예외 처리 (파싱 실패/API 실패 모두 해당 media_key는 스킵, 로그만 남김)
"""
import base64
import json
import os
import re
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import boto3
from langchain_core.messages import HumanMessage

from ..state import ShortFormState, VisionAnalysisResult
from ...common.vision_fallback import invoke_vision_with_fallback  # ⭐ 수정

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

# 추가: mood_tags 어휘 체계 고정 (RAG Agent의 BGM 매칭에서 그대로 사용됨)
MOOD_TAG_VOCAB = [
    "신나는", "조용한", "시끄러운", "잔잔한", "우울한", "웅장한",
    "발랄한", "포근한", "긴장되는", "몽환적인", "경쾌한", "차분한",
]


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
    JSON 형식으로만 답변하도록 프롬프트에 명시."""
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

    # 추가 허용된 mood_tegs 목록을 프롬프트에 문자열로 삽입
    mood_tag_options = ", ".join(MOOD_TAG_VOCAB)

    # 수정: prompt_text에 mood_tags 제한 지시문 추가 (기존엔 자유 태그 허용)
    prompt_text = (
        "이 이미지에 담긴 장면을 분석해서 아래 JSON 형식으로만 답변해줘. "
        "다른 설명, 마크다운, 코드블록 표시 없이 순수 JSON 객체 하나만 출력해.\n\n"
        f"mood_tags는 반드시 다음 목록 중에서만 1~2개 골라야 해 (목록 밖의 단어는 절대 사용 금지): "
        f"{mood_tag_options}\n\n"
        "{\n"
        '  "scene_description": "장면을 한두 문장으로 설명",\n'
        '  "mood_tags": ["위 목록 중에서 1~2개 선택"],\n'
        '  "detected_objects": ["감지된 주요 객체나 활동", "..."]\n'
        "}"
    )

    message = HumanMessage(
        content=[
            {"type": "text", "text": prompt_text},
            {"type": "image_url", "image_url": f"data:{mime_type};base64,{image_base64}"},
        ]
    )

    return invoke_vision_with_fallback(message.content)  # ⭐ 수정: Gemini 할당량 초과 시 OpenAI로 폴백, 정규화된 텍스트 반환


def _parse_vision_response(raw_content: str, media_key: str) -> VisionAnalysisResult | None:
    """Gemini의 raw response(문자열)를 VisionAnalysisResult로 파싱.

    Gemini가 가끔 ```json ... ``` 코드펜스로 감싸서 응답하는 경우가 있어
    그 부분을 먼저 제거한 뒤 json.loads를 시도한다.
    파싱 실패 시 None을 반환하고 호출부에서 로그만 남기고 스킵하게 함.
    """
    text = raw_content.strip()

    # ```json ... ``` 또는 ``` ... ``` 코드펜스 제거
    fence_match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    if fence_match:
        text = fence_match.group(1).strip()

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as e:
        print(f"[VisionAgent] {media_key} JSON 파싱 실패: {e}\n원본 응답: {raw_content}")
        return None

    # 필수 필드 존재 여부 확인 (없으면 빈 값으로 기본 처리)
    scene_description = parsed.get("scene_description", "")
    mood_tags = parsed.get("mood_tags", [])
    detected_objects = parsed.get("detected_objects", [])

    if not isinstance(mood_tags, list):
        mood_tags = [str(mood_tags)]

    # 추가 허용된 어휘 목록(MOOD_TAG_VOCAB) 밖의 태그는 걸러냄 (Gemini가 지시 무시할 경우 대비)
    mood_tags = [tag for tag in mood_tags if tag in MOOD_TAG_VOCAB]

    if not isinstance(detected_objects, list):
        detected_objects = [str(detected_objects)]

    return VisionAnalysisResult(
        media_key=media_key,
        scene_description=scene_description,
        mood_tags=mood_tags,
        detected_objects=detected_objects,
    )


# 이미지 1장당 S3 다운로드 + Gemini(폴백 시 OpenAI) 호출 시간이 그대로 더해지는 구조라,
# 사진 선택 화면에서 고를 수 있는 이미지가 늘수록(보조 사진·동영상 대표 프레임 포함) 대본
# 생성 전체 시간이 그만큼 늘어나 백엔드/프론트 타임아웃까지 넘기던 문제가 있었다.
# 이미지마다 서로 독립적인 작업이라 스레드풀로 동시에 처리한다. 값을 너무 크게 잡으면
# Gemini 할당량(429)을 오히려 더 자주 유발할 수 있어 보수적으로 4로 제한한다.
MAX_CONCURRENT_VISION_CALLS = 4


def _analyze_one_media(media_key: str) -> VisionAnalysisResult | None:
    """미디어 1건을 다운로드 -> Vision 호출 -> 파싱까지 처리. 실패해도 예외를 올리지
    않고 None을 돌려줘서(로그만 남김) 한 장이 실패해도 나머지 장은 계속 처리되게 한다."""
    local_path = None
    try:
        local_path = _download_media_from_s3(media_key)
        response_text = _call_gemini_vision(local_path, media_key)  # ⭐ 수정: 이미 정규화된 텍스트 반환

        if response_text is None:
            return None

        print(f"[VisionAgent] raw response for {media_key}:\n{response_text}")  # ⭐ 수정
        return _parse_vision_response(response_text, media_key)  # ⭐ 수정: _extract_text_from_content 제거(정규화가 헬퍼 내부로 이동)

    except Exception as e:
        # TODO(후속): 실패한 media_key를 모아서 state["error_message"]/status에 반영할지 결정
        print(f"[VisionAgent] {media_key} 처리 중 오류 발생: {e}")
        return None

    finally:
        if local_path and os.path.exists(local_path):
            os.remove(local_path)


def vision_agent(state: ShortFormState) -> ShortFormState:

    media_keys = state["media_keys"]
    print(f"[VisionAgent] media_keys={media_keys}")

    if not media_keys:
        state["vision_results"] = []
        return state

    # futures 리스트를 media_keys와 같은 순서로 만들어두면, 실행은 동시에 되더라도
    # .result()를 그 순서대로 모으므로 씬 순서(자막/렌더링이 의존)가 그대로 유지된다.
    with ThreadPoolExecutor(max_workers=min(MAX_CONCURRENT_VISION_CALLS, len(media_keys))) as executor:
        futures = [executor.submit(_analyze_one_media, media_key) for media_key in media_keys]
        vision_results = [result for future in futures if (result := future.result()) is not None]

    state["vision_results"] = vision_results
    return state