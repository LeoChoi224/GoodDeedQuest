"""커스텀 퀘스트 심사 그래프.

embed(벡터 생성) → evaluate(선행 여부 + 난이도) → finalize(로그)

점수는 계산하지 않는다. 난이도와 intensity만 돌려주고 백엔드가 포인트로 바꾼다.
"""
import json
from typing import TypedDict, Optional

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage

from ai.app.common.llm import get_gemini_model
from ai.app.quest_create.prompts import build_evaluate_prompt, DIFFICULTY_GUIDE
from ai.app.quest_create.similarity import embed_quest

VALID_DIFFICULTIES = set(DIFFICULTY_GUIDE.keys())


class CreateState(TypedDict):
  quest_title: str
  quest_description: str
  category_name: str
  embedding: Optional[list[float]]
  accepted: Optional[bool]
  reason: Optional[str]
  difficulty: Optional[str]
  intensity: Optional[int]


def _reject(reason: str) -> dict:
  """거절로 끝낸다. 결과 칸을 빠짐없이 채워 KeyError를 막는다."""
  return {"accepted": False, "reason": reason, "difficulty": None, "intensity": None}


def embed(state: CreateState) -> dict:
  vector = embed_quest(
    state["quest_title"], state["quest_description"], state["category_name"]
  )
  return {"embedding": vector}


def evaluate(state: CreateState) -> dict:
  prompt = build_evaluate_prompt(
    state["quest_title"], state["quest_description"], state["category_name"]
  )

  model = get_gemini_model(temperature=0.0)
  response = model.invoke([HumanMessage(content=prompt)])

  text = response.content.strip()
  print("퀘스트 심사 원문:", text[:300])

  if text.startswith("```"):
    text = text.split("```")[1].removeprefix("json").strip()

  try:
    result: dict = json.loads(text)
  except json.JSONDecodeError:
    return _reject("AI 응답을 해석하지 못했습니다. 다시 시도해 주세요.")

  if not bool(result.get("accepted")):
    return _reject(result.get("reason") or "퀘스트로 등록하기 어려운 내용입니다.")

  # 모르는 난이도가 오면 NORMAL로 맞춘다 (백엔드도 같은 폴백을 갖고 있다)
  difficulty = result.get("difficulty")
  if difficulty not in VALID_DIFFICULTIES:
    print(f"알 수 없는 난이도 '{difficulty}' → NORMAL로 대체")
    difficulty = "NORMAL"

  # intensity가 숫자가 아니면 중간값으로 둔다
  try:
    intensity = int(result.get("intensity"))
  except (TypeError, ValueError):
    intensity = 50
  intensity = max(0, min(100, intensity))

  return {
    "accepted": True,
    "reason": result.get("reason", ""),
    "difficulty": difficulty,
    "intensity": intensity,
  }


def finalize(state: CreateState) -> dict:
  print(f"퀘스트 심사 결과: accepted={state['accepted']}, "
        f"difficulty={state['difficulty']}, intensity={state['intensity']}")
  return {}


workflow = StateGraph(CreateState)

workflow.add_node("embed", embed)
workflow.add_node("evaluate", evaluate)
workflow.add_node("finalize", finalize)

workflow.set_entry_point("embed")
workflow.add_edge("embed", "evaluate")
workflow.add_edge("evaluate", "finalize")
workflow.add_edge("finalize", END)

quest_create_graph = workflow.compile()


def run_quest_evaluation(quest_title: str, quest_description: str,
                         category_name: str) -> dict:
    result = quest_create_graph.invoke({
        "quest_title": quest_title,
        "quest_description": quest_description,
        "category_name": category_name,
    })
    return {
        "accepted": result["accepted"],
        "reason": result["reason"],
        "difficulty": result.get("difficulty"),
        "intensity": result.get("intensity"),
        "embedding": result.get("embedding") or None,
    }
