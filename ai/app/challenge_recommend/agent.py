# LangGraph 실행 시작점
from typing import List

class TeamRecommendationAgent:
    def __init__(self):
        # 개발 시 임베딩이나 Vector Search 로직 탑재 예정
        pass

    def recommend_team_challenges(self, user_interests: List[str], user_location: str) -> List[dict]:
        """사용자의 흥미 도메인과 지리적 위치 정보를 받아 적합한 협동 챌린지 팀을 매칭합니다."""
        # 임시 추천 알고리즘 뼈대
        # DB 생성 후: 사용자 프로필 및 후보 DB 기반으로 변경
        suggested_teams = []
        
        if "환경" in user_interests:
            suggested_teams.append({
                "challenge_id": 401,
                "team_name": "에코-플로깅 크루",
                "matching_reason": "사용자님의 주 관심사가 '환경'이고 위치인 '마포구' 근처의 플로깅 챌린지 팀입니다.",
                "members_count": 4
            })
            
        if "봉사" in user_interests:
            suggested_teams.append({
                "challenge_id": 402,
                "team_name": "따뜻한 이웃 봉사단",
                "matching_reason": "사용자님의 봉사 도메인 관심사와 최근 활동 내역을 토대로 매칭된 주말 봉사 팀입니다.",
                "members_count": 6
            })
            
        return suggested_teams

agent = TeamRecommendationAgent()

def recommend_collaborative_teams(interests: List[str], location: str) -> List[dict]:
    return agent.recommend_team_challenges(interests, location)
