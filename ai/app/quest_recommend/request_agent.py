from pydantic import BaseModel, Field
import logging
from typing import Dict, Any, Optional, List

from ai.app.quest_recommend.state import RecommendState
from ai.app.common.llm import get_openai_model

from langchain_core.prompts import ChatPromptTemplate

logger = logging.getLogger(__name__)

class RequestAnalysis(BaseModel):
    """사용자 요청 메시지 분석결과(선호 시간, 소요 시간, 실내외 선호, 키워드)를 구조화하는 Pydantic 스키마"""
    time_preference: Optional[str] = Field(
        default="any",
        # "사용자 메시지에서 아침, 저녁, 퇴근길, 주말 등 시간 관련 선호도를 추출합니다. 없으면 'any'로 지정합니다."
        description="Time preference extracted from the user message, e.g. morning, afternoon, evening, night, weekend, weekday. Default is 'any'."
    )
    duration_preference: Optional[str] = Field(
        default="any",
        # "사용자 메시지에서 선호하는 소요 시간을 추출합니다. 30분 내외는 'short', 30분~2시간은 'medium', 2시간 이상은 'long', 명시되지 않으면 'any'로 지정합니다."
        description="Preferred duration of the quest: 'short' (under 30 mins), 'medium' (30 mins to 2 hours), 'long' (over 2 hours). Default is 'any'."
    )
    indoor_outdoor_preference: Optional[str] = Field(
        default="any",
        # "사용자가 실내를 선호하면 'indoor', 실외를 선호하면 'outdoor'를 추출합니다. 없으면 'any'로 지정합니다."
        description="Location preference: 'indoor', 'outdoor'. Default is 'any'."
    )
    additional_keywords: List[str] = Field(
        default_factory=list,
        # "사용자 메시지에서 퀘스트 추천에 유용한 1~3개의 핵심 토픽 키워드들을 추출합니다. 가급적 영어 단어로 번역하여 추출합니다 (예: '환경', '쓰레기 줍기' -> ['environment', 'trash_cleanup'])."
        description="1 to 3 key topic keywords from the message, translated to English if possible (e.g. 'trash' or 'cleanup' for 쓰레기 줍기)."
    )
    
def analyze_request(state: RecommendState) -> Dict[str, Any]:
    """
    사용자의 요청 메시지(request_message)를 분석하여
    구조화된 조건 데이터(request_context)를 생성하는 LangGraph 노드 함수입니다.
    """
    request_message = state.get("request_message")

    if not request_message or not request_message.strip():
        return {"request_context": {}}
    
    try:
        llm = get_openai_model(model_name="gpt-4o-mini", temperature=0.0)  # 일관성 있는 분석을 위해 온도=0.0
        structured_llm = llm.with_structured_output(RequestAnalysis)

        """
        ("system", "사용자의 퀘스트 추천 요청을 분석하고 구조화된 제약 조건을 추출하십시오."),
        ("human", "{request_message}")
        """
        request_prompt = ChatPromptTemplate.from_messages([
            ("system", "Analyze the user's quest recommendation request and extract structured constraints."),
            ("human", "{request_message}")
        ])
        
        request_chain = request_prompt | structured_llm

        response = request_chain.invoke({"request_message": request_message})
        analysis_dict = response.model_dump()
        
        return {"request_context": analysis_dict}
    
    except Exception as e:
        logger.warning(f"OpenAI를 통한 요청 메시지 분석 실패: {e}. 빈 request_context로 폴백합니다.")
        # 외부 API 호출 에러 시 추천 흐름이 깨지지 않도록 빈 딕셔너리로 안전하게 Fallback
        return {"request_context": {}}
