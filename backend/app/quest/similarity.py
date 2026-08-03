import math
from typing import Optional
from backend.app.quest.models import Quest
SIMILARITY_THRESHOLD = 0.93

def cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    
    dot = sum(x * y for x, y in zip(a, b))
    size_a = math.sqrt(sum(x * x for x in a))
    size_b = math.sqrt(sum(y * y for y in b))

    if size_a == 0 or size_b == 0:
        return 0.0

    return dot / (size_a * size_b)

def find_similar_quest(
    quest_repository, embedding: Optional[list[float]],
) -> tuple[Optional[Quest], float]:

    if not embedding:
        return None, 0.0
    
    best: Optional[Quest] = None
    best_score = 0.0
    
    for quest in quest_repository.filter(Quest.is_deleted == False):
        if not quest.quest_embedding:
            continue
        score = cosine_similarity(embedding, quest.quest_embedding)
        if score > best_score:
            best, best_score = quest, score
            
    if best is not None and best_score >= SIMILARITY_THRESHOLD:
        return best, best_score

    return None, best_score