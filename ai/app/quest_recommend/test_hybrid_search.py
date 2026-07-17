import logging
from ai.app.common.vector_adapter import get_vector_store_adapter, get_dummy_volunteer_data

# 로그 출력 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_hybrid_search():
    print("=== Hybrid Search (Vector + BM25) 통합 테스트 ===")

    # 1. 싱글톤 벡터 스토어 어댑터 획득 및 데이터 초기화
    adapter = get_vector_store_adapter()
    adapter.clear()

    # 2. 더미 봉사 데이터 적재 및 인덱싱 실행
    dummy_data = get_dummy_volunteer_data()
    print(f"\n더미 데이터 {len(dummy_data)}개를 로드하여 벡터 DB에 인덱싱합니다...")
    adapter.add_documents(dummy_data)

    # 3. 다양한 검색 키워드로 하이브리드 검색 검증
    test_queries = [
        "망원지구 쓰레기 수거 환경 정화",  # 환경 카테고리 데이터 매칭
        "동물 보호소 견사 청소",           # 동물 카테고리 데이터 매칭
        "정운 봉사 우리는 선행",        # 정운이 구호 데이터 매칭
        "제주도 엄마 사과하기"            # 엄마에게 사과하기 매칭
    ]

    for idx, query in enumerate(test_queries, start=1):
        print(f"\n테스트 {idx}. [검색 질의]: '{query}'")
        
        # 하이브리드 검색 수행 (Top 2 검색)
        results = adapter.hybrid_search(query, top_k=2)

        print("결과:")
        if not results:
            print("  - 일치하는 검색 결과가 없습니다.")
        for rank, res in enumerate(results, start=1):
            print(f"  [{rank}위] ID: {res.get('id')} | [{res.get('category')}] {res.get('title')}")
            print(f"        내용: {res.get('content')}")


if __name__ == "__main__":
    test_hybrid_search()