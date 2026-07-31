from backend.app.auth.models import User

TRUST_DEFAULT = 50

# 하한을 기본값(50)과 같게 두면 50점인 사람은 깎여도 곧바로 50으로 되돌아가
# 감점이 아예 일어나지 않는다. 바닥은 0이어야 한다.
TRUST_MIN = 0
TRUST_MAX = 1000

TRUST_ON_COMPLETE = +1     # 퀘스트 완료
TRUST_ON_CHALLENGE = -1    # AI는 통과시켰지만 의심 신호가 겹쳐 챌린지가 발급됨
TRUST_ON_REJECT = -1       # 거절 (AI 판정 실패 / 재탕 적발 / 챌린지 실패)

def adjust_trust(user: User, delta: int) -> int:
  current = user.trust_score if user.trust_score is not None else TRUST_DEFAULT
  user.trust_score = max(TRUST_MIN, min(TRUST_MAX, current + delta))
  return user.trust_score
  