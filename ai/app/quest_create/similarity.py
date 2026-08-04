"""퀘스트 임베딩 생성.

같은 활동을 조금씩 바꿔 여러 번 등록해 보상을 반복 수령하는 것을 막기 위해,
퀘스트를 벡터로 바꿔 둔다. 실제 비교(코사인 유사도)는 사용자의 기존 퀘스트를
들고 있는 백엔드에서 한다.
"""
from ai.app.common.embedding import get_embedding


def build_quest_text(quest_title: str, quest_description: str, category_name: str) -> str:
    return f"[{category_name}] {quest_title}\n{quest_description}"


def embed_quest(quest_title: str, quest_description: str, category_name: str) -> list[float]:
    text = build_quest_text(quest_title, quest_description, category_name)
    try:
        return get_embedding(text)
    except Exception as err:
        # 임베딩이 실패해도 등록 자체를 막지는 않는다 (중복 검사만 건너뜀)
        print(f"임베딩 실패: {type(err).__name__}: {err}")
        return []
