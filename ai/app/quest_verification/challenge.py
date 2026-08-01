"""챌린지 응답 판정 — 손글씨 인증 코드가 사진에 있는지 확인한다.

활동 내용은 이미 1차 판정에서 확인했으므로, 여기서는 코드 일치만 본다.
판정 단계가 하나뿐이라 LangGraph를 쓰지 않는다.
"""
import base64
import json

import httpx
from langchain_core.messages import HumanMessage

from ai.app.common.llm import get_gemini_model
from ai.app.common.llm_response import extract_text
from ai.app.quest_verification.prompts import build_challenge_prompt


def verify_challenge(media_url: str, code: str) -> dict:
    """사진에 손글씨 code가 있으면 matched=True."""
    image_bytes = httpx.get(media_url, timeout=30.0).content
    img_b64 = base64.b64encode(image_bytes).decode()

    content = [
        {"type": "text", "text": build_challenge_prompt(code)},
        {"type": "image_url", "image_url": f"data:image/jpeg;base64,{img_b64}"},
    ]

    model = get_gemini_model(temperature=0.0)
    response = model.invoke([HumanMessage(content=content)])

    text = extract_text(response)
    print("챌린지 판정 원문:", text[:200])

    if text.startswith("```"):
        text = text.split("```")[1].removeprefix("json").strip()

    try:
        result: dict = json.loads(text)
    except json.JSONDecodeError:
        return {"matched": False, "reason": "AI 응답을 해석하지 못했습니다. 다시 시도해 주세요."}

    return {
        "matched": bool(result.get("matched")),
        "reason": result.get("reason", ""),
    }
