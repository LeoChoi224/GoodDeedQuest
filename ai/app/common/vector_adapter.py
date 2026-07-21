import abc
import logging
from typing import List, Dict, Any

# LangChain 관련 컴포넌트 임포트
from langchain_core.embeddings import Embeddings
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever

from ai.app.common.embedding import get_embeddings, get_embedding

logger = logging.getLogger(__name__)


def get_dummy_volunteer_data() -> List[Dict[str, Any]]:
    """
    시스템 추천 흐름 검증에 사용할 규격화된 봉사 활동 더미 데이터 목록을 반환합니다.
    """
    return [
        {
            "id": 1001,
            "title": "한강 공원 쓰레기 줍기 플로깅 봉사",
            "content": "한강 시민공원 망원지구 일대를 산책하며 방치된 쓰레기를 수거하고 환경 정화 활동을 펼칩니다.",
            "category": "환경",
            "location": "서울시 마포구",
            "url": "https://www.1365.go.kr/nanum/prg/egvh/vnt/vntProgCode=1001",
            "is_volunteer": True
        },
        {
            "id": 1002,
            "title": "유기견 보호소 사료 배급 및 청소 봉사",
            "content": "강남 동물 보호소에서 보호 중인 유기견들의 사료 배식과 견사 물청소 및 사회화 훈련을 돕습니다.",
            "category": "동물",
            "location": "서울시 강남구",
            "url": "https://www.1365.go.kr/nanum/prg/egvh/vnt/vntProgCode=1002",
            "is_volunteer": True
        },
        {
            "id": 1003,
            "title": "독거 어르신 사랑의 반찬 배달 봉사",
            "content": "지역 복지관에서 손수 만든 따뜻한 밑반찬을 인근 취약계층 독거 어르신 댁에 직접 배달하고 안부를 묻습니다.",
            "category": "지역사회",
            "location": "서울시 서대문구",
            "url": "https://www.1365.go.kr/nanum/prg/egvh/vnt/vntProgCode=1003",
            "is_volunteer": True
        },
        {
            "id": 1004,
            "title": "정운이 구호 외치기",
            "content": "(정운)나는 봉사, (희준)나는 환경, (태현)나는 나눔, (민재)나는 동물, (홍묵)나는 지역사회, 우리는 선행 퀘스트!!",
            "category": "기타",
            "location": "서울시 강남구",
            "url": "https://www.1365.go.kr/nanum/prg/egvh/vnt/vntProgCode=1004",
            "is_volunteer": True
        },
        {
            "id": 1005,
            "title": "엄마한테 사과하기",
            "content": "??이가 엄마한테 사과하기.",
            "category": "기타",
            "location": "제주특별자치도 제주시",
            "url": "https://www.1365.go.kr/nanum/prg/egvh/vnt/vntProgCode=1005",
            "is_volunteer": True
        }
    ]


class LangChainEmbeddingsWrapper(Embeddings):
    """
    공통 임베딩 함수(get_embeddings)를 LangChain 규격에 맞춰 감싼 클래스
    """
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return get_embeddings(texts)

    def embed_query(self, text: str) -> List[float]:
        return get_embedding(text)


class VectorStoreAdapter(abc.ABC):
    """
    Vector DB 연결용 추상 어댑터 인터페이스
    """

    @abc.abstractmethod
    def add_documents(self, documents: List[Dict[str, Any]]) -> None:
        """
        문서 리스트 추가 (내부적으로 자동 임베딩 수행)
        """
        pass

    @abc.abstractmethod
    def similarity_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        질문 텍스트 기반 유사도 검색
        """
        pass

    @abc.abstractmethod
    def hybrid_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        벡터 유사도와 키워드 매칭(BM25)을 결합한 하이브리드 검색
        """
        pass

    @abc.abstractmethod
    def clear(self) -> None:
        """
        기존에 구축된 벡터 저장소를 초기화
        """
        pass


class FaissVectorStoreAdapter(VectorStoreAdapter):
    """
    LangChain의 FAISS 모듈을 활용해 컴퓨터 메모리 상에 임베딩 벡터 저장소를 구성하는 어댑터
    """

    def __init__(self, embeddings_model: Embeddings = None):
        # 외부 주입이 없으면 공통 Embedding Wrapper 사용
        self.embeddings_model = embeddings_model or LangChainEmbeddingsWrapper()
        self.db = None
        self.documents_list = [] # BM25 검색기 생성을 위한 원본 데이터 리스트 보관

    def add_documents(self, documents: List[Dict[str, Any]]) -> None:
        # 입력으로 들어온 데이터가 없으면 함수를 즉시 종료합니다.
        if not documents:
            return
        
        # 원본 데이터 복사본 유지
        self.documents_list.extend(documents)

        # Dict 포맷을 LangChain Document 객체로 변환
        lc_docs = []
        for doc in documents:
            lc_docs.append(Document(
                page_content=doc["content"], # 검색 기준이 될 핵심 텍스트
                metadata=doc                 # 전체 원본 데이터 보관
            ))

        # FAISS DB 생성 또는 기존 DB에 문서 추가
        if self.db is None:
            self.db = FAISS.from_documents(lc_docs, self.embeddings_model)
        else:
            self.db.add_documents(lc_docs)
        logger.info(f"FAISS 저장소에 {len(documents)}개 문서 저장 완료")

    def similarity_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        if self.db is None:
            logger.warning("저장된 인덱스가 존재하지 않습니다.")
            return []

        # LangChain FAISS의 검색 기능 실행
        docs = self.db.similarity_search(query, k=top_k)
        
        # Document 객체에서 원본 메타데이터 딕셔너리만 추출하여 반환
        return [doc.metadata for doc in docs]
    
    def hybrid_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        FAISS Dense Vector 검색과 BM25 Sparse Keyword 검색 결과를 융합한 Hybrid Search 수행
        """
        if self.db is None or not self.documents_list:
            logger.warning("저장된 문서 데이터가 존재하지 않습니다.")
            return []
        
        # 1. FAISS 기반 Dense Retriever 생성
        faiss_retriever = self.db.as_retriever(search_kwargs={"k": top_k})

        # 2. BM25 기반 Sparse Retriever 생성
        lc_docs = [
            Document(page_content=doc["content"], metadata=doc)
            for doc in self.documents_list
        ]
        bm25_retriever = BM25Retriever.from_documents(lc_docs)
        bm25_retriever.k = top_k
        
        # 3. 두 검색기를 RRF(Reciprocal Rank Fusion) 가중치 5:5로 융합하는 Ensemble Retriever 구성
        ensemble_retriever = EnsembleRetriever(
            retrievers=[bm25_retriever, faiss_retriever],
            weights=[0.5, 0.5]
        )

        # 4. 검색 수행
        results = ensemble_retriever.invoke(query)
        
        # 5. 검색 결과의 중복을 제거하여 Top-K 추출
        seen_ids = set()
        final_results = []
        for doc in results:
            doc_id = doc.metadata.get("id")
            if doc_id not in seen_ids:
                seen_ids.add(doc_id)
                final_results.append(doc.metadata)
            if len(final_results) >= top_k:
                break
        return final_results

    def clear(self) -> None:
        self.db = None
        self.documents_list = []
        logger.info("FAISS 및 문서 저장소 초기화 완료")


# 싱글톤 인스턴스 전역 관리
_global_vector_store_adapter = None

def get_vector_store_adapter(provider: str = "faiss") -> VectorStoreAdapter:
    """Vector Store 어댑터 팩토리 함수"""
    global _global_vector_store_adapter
    
    if _global_vector_store_adapter is None:
        if provider == "faiss":
            _global_vector_store_adapter = FaissVectorStoreAdapter()
            logger.info("싱글톤 FAISS 어댑터 최초 생성")
        else:
            raise ValueError(f"지원하지 않는 프로바이더: {provider}")
            
    return _global_vector_store_adapter


# 로컬 단독 테스트 기능
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("--- Vector DB 어댑터 로컬 기능 테스트 ---")

    # API Key 없이 실행해보기 위해 테스트 전용 더미 임베딩 클래스 선언
    class DummyTestEmbeddings(Embeddings):
        def embed_documents(self, texts: List[str]) -> List[List[float]]:
            # 가짜 3차원 벡터 생성
            return [[0.1, 0.2, 0.3] for _ in texts]
        def embed_query(self, text: str) -> List[float]:
            return [0.1, 0.2, 0.3]

    # 더미 임베딩을 주입해 어댑터 초기화 (인터넷/API 키 없이 로컬 실행 가능)
    test_adapter = FaissVectorStoreAdapter(embeddings_model=DummyTestEmbeddings())
    dummy_docs = get_dummy_volunteer_data()

    # 인덱싱 테스트
    test_adapter.add_documents(dummy_docs)

    # 검색 테스트
    query_text = "유기견을 위해 할 수 있는 봉사활동을 찾고 싶어요."
    print(f"\n[검색 질문]: {query_text}")
    
    search_results = test_adapter.similarity_search(query_text, top_k=2)
    
    print("\n--- 검색 결과 (Top 2) ---")
    for rank, result in enumerate(search_results, start=1):
        print(f"순위 {rank}: [{result['category']}] {result['title']}")
        print(f"  - 상세: {result['content']}")