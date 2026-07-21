from ai.app.common.embedding import get_embedding

def embed_user_profile(category, active_time, preferred_difficulty, age) -> list[float]:
  parts = []
  if category:
    parts.append("관심사" + ",".join(category))
  if active_time:
    parts.append("활동 시간대" + ",".join(active_time))
  if preferred_difficulty:
    parts.append("선호 난이도: " + preferred_difficulty)
  if age:
    parts.append("나이: " + str(age))
  text = "/".join(parts)
  return get_embedding(text)