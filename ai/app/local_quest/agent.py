from typing import List

class LocalQuestAgent:
    def __init__(self):
        # 지역별로 부족한 봉사 분야에 대한 Mock 데이터베이스
        # 실제 프로덕션에서는 공공 API나 통계 DB 적재 데이터를 크롤링해와 매핑
        self.local_shortage_statistics = {
            "마포구": ["유기동물 보호", "독거노인 반찬 배달"],
            "서대문구": ["장애인 학습 지도", "한강 정화"],
            "강남구": ["재활용 분리수거 교육", "환경 정화"]
        }

    def recommend_local_shortage_quests(self, location: str) -> List[dict]:
        """사용자가 속한 지역에 인력이 부족한 봉사 분야를 필터링하여 맞춤형 퀘스트를 추천합니다."""
        # 기본 부족 분야
        shortage_domains = self.local_shortage_statistics.get(location, ["환경 정화", "급식 도우미"])
        
        recommendations = []
        
        # 부족 분야별 Mock 퀘스트 매칭
        for idx, domain in enumerate(shortage_domains):
            recommendations.append({
                "id": 501 + idx,
                "title": f"[{location} 긴급] {domain} 퀘스트",
                "description": f"현재 {location} 지역은 {domain} 일손이 매우 부족한 상황입니다. 이웃들을 위해 힘을 보태주세요!",
                "domain": domain,
                "urgency_level": "HIGH",
                "bonus_points": 50 # 부족 퀘스트 참여 시 보너스 포인트 지급 유도
            })
            
        return recommendations

agent = LocalQuestAgent()

def get_local_shortage_recommendations(location: str) -> List[dict]:
    return agent.recommend_local_shortage_quests(location)
