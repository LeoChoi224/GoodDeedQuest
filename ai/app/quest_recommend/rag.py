import numpy as np

class SimpleRAGCoach:
    def __init__(self):
        self.documents = [
            "자원봉사 활동 시간은 1365포털이나 VMS를 통해 공식 인증됩니다.",
            "Good Deed Quest에서 적립한 포인트는 매월 말 기부 단체로 자동 연계 기부 신청이 가능합니다.",
            "환경 정화 플로깅 퀘스트 진행 시, 안전을 위해 밝은 옷을 입고 인도가 확보된 곳에서만 진행하셔야 합니다.",
            "부정 인증(인터넷 무단 펌 이미지 제출 등) 적발 시 패널티로 포인트 회수 및 스트릭 초기화 조치가 내려집니다."
        ]
        
    def retrieve_relevant_documents(self, query: str) -> list:
        results = []
        for doc in self.documents:
            words = query.split()
            if any(word in doc for word in words) or len(results) < 2:
                results.append(doc)
        return list(set(results[:2]))

    def answer_question(self, query: str) -> dict:
        contexts = self.retrieve_relevant_documents(query)
        answer = f"찾아본 정보에 따르면 다음과 같습니다. {contexts[0]} 추가적으로 안전 수칙이나 기부 규정을 꼭 확인하시기 바랍니다."
        return {
            "answer": answer,
            "sources": contexts
        }

rag_coach = SimpleRAGCoach()

def query_rag_coach(question: str) -> dict:
    return rag_coach.answer_question(question)
