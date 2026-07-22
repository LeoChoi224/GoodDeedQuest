"""
RAG Agent (BGM 매칭)

입력: state["vision_results"] (씬 분위기/태그)
출력: state["bgm_match"] (매칭된 bgm_id)

실제 구현 시 pgvector에 저장된 BackgroundMusic 임베딩과
vision_results의 mood_tags를 벡터 유사도 검색으로 매칭.
ShortForm.bgm_id는 NOT NULL 이므로 이 단계에서 반드시 값이 채워져야 함.
"""
from ..state import ShortFormState, BgmMatchResult


def rag_agent(state: ShortFormState) -> ShortFormState:
    mood_tags = [tag for r in state["vision_results"] for tag in r["mood_tags"]]
    print(f"[RagAgent] mood_tags={mood_tags}")

    # TODO: pgvector 유사도 검색으로 교체 (이슈 2에서 작업)
    dummy_match: BgmMatchResult = {
        "bgm_id": 1,
        "bgm_title": "더미 BGM",
        "match_score": 0.0,
        "match_reason": "더미 매칭 결과 (RAG 미구현)",
    }

    state["bgm_match"] = dummy_match
    return state