"""퀘스트 인증 판정 그래프.

fetch_media(미디어 수집) → vision_verify(판정) → finalize(로그)

영상 처리는 video.py, 프롬프트는 prompts.py에 분리되어 있다.
"""
import base64
import json
from datetime import datetime, timedelta, timezone
from typing import TypedDict, Optional

import httpx
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage

from ai.app.common.llm import get_gemini_model
from ai.app.common.llm_response import extract_text
from ai.app.quest_verification.video import extract_frames
from ai.app.quest_verification.prompts import build_video_prompt, build_certificate_prompt

# 촬영 후 이 기간이 지난 영상은 거절한다.
MAX_VIDEO_AGE_DAYS = 2
# 기기·서버 시계 오차를 감안한 미래 시각 허용 폭.
CLOCK_SKEW_HOURS = 1
# 동영상에서 뽑을 프레임 수.
VIDEO_FRAME_COUNT = 8


class VerifyState(TypedDict):
  quest_id: int
  quest_title: str
  quest_description: str
  media_urls: list[str]
  is_video: Optional[bool]
  image_bytes_list: Optional[list[bytes]]
  video_created_at: Optional[str]
  primary_count: Optional[int]
  verified: Optional[bool]
  reason: Optional[str]
  related: Optional[list[bool]]
  ai_generated: Optional[bool]
  capture_time_known: Optional[bool]


def _reject(reason: str, related: Optional[list[bool]] = None) -> dict:
  """판정을 거절로 끝낸다. 모든 결과 칸을 빠짐없이 채워 KeyError를 막는다."""
  return {"verified": False, "reason": reason,
          "related": related or [], "ai_generated": False,
          "capture_time_known": False
          }


def fetch_media(state: VerifyState) -> dict:
  urls = state["media_urls"]

  if state.get("is_video"):
    # 첫 URL이 동영상, 나머지는 보조 사진
    frames, created_at = extract_frames(urls[0], count=VIDEO_FRAME_COUNT)
    photos = [httpx.get(url, timeout=30.0).content for url in urls[1:]]
    return {
      "image_bytes_list": frames + photos,
      "primary_count": len(frames),
      "video_created_at": created_at.isoformat() if created_at else None,
    }

  images = []
  for url in urls:
    response = httpx.get(url, timeout=30.0)
    response.raise_for_status()
    images.append(response.content)
  return {"image_bytes_list": images, "primary_count": 1, "video_created_at": None}


def _check_capture_time(created_at_raw: Optional[str]) -> Optional[str]:
  """촬영 시각이 문제면 거절 사유를, 괜찮으면 None을 돌려준다."""
  if not created_at_raw:
    # 촬영 시각이 없는 자료도 있으므로(편집 앱 등) 없다고 막지는 않는다
    return None

  created_at = datetime.fromisoformat(created_at_raw)
  now = datetime.now(timezone.utc)

  if created_at > now + timedelta(hours=CLOCK_SKEW_HOURS):
    print(f"촬영시각 거절: 미래 시각 {created_at}")
    return "영상의 촬영 시각이 올바르지 않습니다. 기기의 날짜·시간 설정을 확인해 주세요."

  if now - created_at > timedelta(days=MAX_VIDEO_AGE_DAYS):
    print(f"촬영시각 거절: {created_at} (기준 {MAX_VIDEO_AGE_DAYS}일)")
    return f"{MAX_VIDEO_AGE_DAYS}일 이내에 촬영한 영상만 인정됩니다. 새로 촬영해 주세요."

  return None


def vision_verify(state: VerifyState) -> dict:
  primary_count = state.get("primary_count") or 0
  total = len(state["image_bytes_list"])
  extra_count = total - primary_count

  if primary_count == 0 or total == 0:
    return _reject("동영상에서 화면을 추출하지 못했습니다. 다시 시도해 주세요.")

  # Gemini를 부르기 전에 무료로 거를 수 있는 검사부터
  time_reject = _check_capture_time(state.get("video_created_at"))
  if time_reject:
    return _reject(time_reject)

  if primary_count > 1:
    prompt = build_video_prompt(state["quest_title"], state["quest_description"],
                                primary_count, extra_count)
  else:
    prompt = build_certificate_prompt(state["quest_title"], state["quest_description"],
                                      extra_count)

  content = [{"type": "text", "text": prompt}]
  for image_bytes in state["image_bytes_list"]:
    img_b64 = base64.b64encode(image_bytes).decode()
    content.append({"type": "image_url", "image_url": f"data:image/jpeg;base64,{img_b64}"})

  model = get_gemini_model(temperature=0.0)
  response = model.invoke([HumanMessage(content=content)])

  text = extract_text(response)
  print("Gemini 원문 응답:", text[:300])

  if text.startswith("```"):
    text = text.split("```")[1].removeprefix("json").strip()

  try:
    result: dict = json.loads(text)
  except json.JSONDecodeError:
    return _reject("AI 응답을 해석하지 못했습니다. 다시 시도해 주세요.")

  related = [bool(r) for r in (result.get("related") or [])[:extra_count]]

  ai_generated = bool(result.get("ai_generated"))
  if ai_generated:
    print("AI 생성 의심 신호")

  return {
    "verified": bool(result.get("verified")),
    "reason": result.get("reason", ""),
    "related": related,
    "ai_generated": ai_generated,
    "capture_time_known": bool(state.get("video_created_at")),
  }


def finalize(state: VerifyState) -> dict:
  print(f"최종 판정: verified={state['verified']}, reason={state['reason']}")
  return {}


workflow = StateGraph(VerifyState)

workflow.add_node("fetch_media", fetch_media)
workflow.add_node("vision_verify", vision_verify)
workflow.add_node("finalize", finalize)

workflow.set_entry_point("fetch_media")
workflow.add_edge("fetch_media", "vision_verify")
workflow.add_edge("vision_verify", "finalize")
workflow.add_edge("finalize", END)

verification_graph = workflow.compile()


def run_verification_flow(quest_id: int, quest_title: str, quest_description: str,
                          media_urls: list[str], is_video: bool = False) -> dict:
    result = verification_graph.invoke({
        "quest_id": quest_id,
        "quest_title": quest_title,
        "quest_description": quest_description,
        "media_urls": media_urls,
        "is_video": is_video,
    })
    return {
        "verified": result["verified"],
        "reason": result["reason"],
        "related": result["related"],
        "ai_generated": result.get("ai_generated", False),
        "capture_time_known": result.get("capture_time_known", False),
    }
