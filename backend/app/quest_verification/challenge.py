import secrets
import base64
import json
import httpx
from langchain.messages import HumanMessage

from ai.app.common.llm import get_gemini_model
from ai.app.quest_verification.prompts import build_challenge_prompt

SUSPICION_AI_GENERATED = 3 
SUSPICION_PHASH_GRAY = 2        # 차단 기준은 아니지만 과거 제출과 꽤 비슷함
SUSPICION_NO_CAPTURE_TIME = 1   # 촬영 시각이 지워졌거나 없음
CHALLENGE_THRESHOLD = 3

PHASH_GRAY_MAX = 12

def generate_challenge_code() -> str:
    return f"{secrets.randbelow(10000):04d}"

def build_challenge_message(code: str) -> str:
    return (
        f"자료의 진위를 확인하기 위해 추가 인증이 필요합니다.\n"
        f"종이에 {code} 를 손으로 적고, 그 종이가 잘 보이도록 사진을 찍어 올려 주세요."
    )

def calculate_suspicion(ai_generated: bool, capture_time_known: bool,
                        phash_distance: int | None) -> int:
  score = 0
  if ai_generated:
      score += SUSPICION_AI_GENERATED
  if not capture_time_known:
      score += SUSPICION_NO_CAPTURE_TIME
  if phash_distance is not None and phash_distance <= PHASH_GRAY_MAX:
      score += SUSPICION_PHASH_GRAY
  return score

def needs_challenge(score: int) -> bool:
    return score >= CHALLENGE_THRESHOLD

def verifiy_challange(media_url: str, code: str) -> dict:
    image_bytes = httpx.get(media_url, timeout=30.0).content
    img_b64 = base64.b64encode(image_bytes).decode()
    
    content = [
        {"type": "text", "text": build_challenge_prompt(code)},
        {"type": "image_url", "image_url": f"data:image/jpeg;base64,{img_b64}"},
    ]

    model = get_gemini_model(temperature=0.0)
    response = model.invoke([HumanMessage(content=content)])
    
    text = response.content.strip()
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