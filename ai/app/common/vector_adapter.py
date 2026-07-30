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
        lc_docs = [
            Document(
                page_content=doc["content"], # 검색 기준이 될 핵심 텍스트
                metadata=doc                 # 전체 원본 데이터 보관
            )
            for doc in documents
        ]

        # FAISS DB 생성 또는 기존 DB에 문서 추가
        if self.db is None:
            self.db = FAISS.from_documents(lc_docs, self.embeddings_model)
        else:
            self.db.add_documents(lc_docs)

        logger.info(f"FAISS 동적 저장소에 {len(documents)}개 문서 인덱싱 완료")

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

