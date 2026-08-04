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

# ⭐ 추가: LLM이 지시를 무시하고 **굵게**/*기울임*/__밑줄__/`코드` 같은 마크다운 서식을
# 섞어 보내는 경우가 있어, 자막(온스크린 텍스트)에 별표/밑줄 기호가 그대로 노출됐다 -
# 서식 기호만 벗겨내고 안의 텍스트는 남긴다.
_MARKDOWN_EMPHASIS_PATTERN = re.compile(r'\*\*(.+?)\*\*|__(.+?)__|\*(.+?)\*|_(.+?)_|`(.+?)`')


def _strip_markdown(text: str) -> str:
    def _unwrap(match: "re.Match[str]") -> str:
        return next(g for g in match.groups() if g is not None)

    return _MARKDOWN_EMPHASIS_PATTERN.sub(_unwrap, text).strip()


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
    vision_results = state.get("vision_results", [])
    scene_count = len(vision_results) or 1
    # ⭐ 수정: 예전엔 장면 설명을 번호 없이 그냥 나열해서, LLM이 각 자막을 특정 장면과
    # 대응시키지 않고 퀘스트 제목만 보고 뭉뚱그린 일반적인 문구를 쓰는 경우가 있었다
    # ("이미지랑 자막이랑 전혀 상관없다"는 피드백). 장면에 번호를 매겨 그 순서에 맞는
    # 자막을 쓰도록 명시적으로 지시한다.
    scene_lines = "\n".join(
        f"{i + 1}. {r['scene_description']}" for i, r in enumerate(vision_results)
    ) or "1. (장면 설명 없음)"

    return f"""당신은 선행 인증 숏폼 영상의 온스크린 자막을 작성하는 작가입니다.

사용자 이름: {state['user_name']}
퀘스트 제목: {state['quest_title']}

영상은 아래 순서의 장면(총 {scene_count}개)으로 구성됩니다. 각 번호의 설명은 그 장면
사진을 AI가 분석한 내용입니다:
{scene_lines}

각 장면마다 정확히 1줄씩, 총 {scene_count}줄의 온스크린 자막을 작성해주세요.

규칙:
1. 반드시 "1. ", "2. "처럼 번호를 붙이고, 그 번호에 해당하는 장면 설명 내용과 직접
   연결되는 문구를 쓰세요. 장면 설명과 무관한 뭉뚱그린 문구는 쓰지 마세요.
2. 나레이션 음성이 아니라 화면에 얹는 짧은 텍스트 자막입니다 - 한 줄은 20자 내외로
   간결하게 쓰세요.
3. 감동적이고 진솔한 톤으로 쓰되 과장하지 마세요.
4. **굵게**, *기울임*, `코드` 같은 마크다운 서식이나 별표(*)·밑줄(_)·해시(#) 등의
   특수기호는 절대 쓰지 말고 순수 텍스트로만 답하세요.
5. 번호와 문구 외에 다른 설명이나 인사말은 쓰지 마세요.
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
        # ⭐ 추가: 프롬프트에서 마크다운 서식을 쓰지 말라고 지시해도 LLM이 가끔
        # **강조** 같은 서식을 섞어 보내서, 자막에 별표가 글자 양옆에 그대로 노출되던
        # 문제 - 안전망으로 한 번 더 벗겨낸다.
        captions = [_strip_markdown(c) for c in captions]
        captions = [c[:settings.MAX_CAPTION_LENGTH] for c in captions]

        state["generated_captions"] = captions

    except Exception as e:
        print(f"[LlmStoryAgent] LLM 호출 실패: {e}")
        state["error_message"] = f"LLM Story Agent 호출 실패: {e}"
        state["status"] = "FAILED"

    return state