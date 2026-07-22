"""
short_form AI 파이프라인 State 스키마

5-Agent LangGraph 파이프라인:
Vision Agent -> RAG Agent -> LLM Story Agent -> Validation Agent -> FFmpeg Render Agent

주의:
- TTS/Whisper 없음. 영상 나레이션은 온스크린 자막 + 배경음악(BGM)만 사용.
- BGM은 RAG 기반 자동 매칭 (ShortForm.bgm_id NOT NULL 이므로 반드시 채워져야 함).
- caption 수정은 DB/캐시에 저장되지 않음. 프론트가 최종 caption을 파라미터로 넘김.
"""
from typing import TypedDict, Optional, List, Literal
# TypedDict: dict인데 키/값 타입을 미리 정해두는 것. LangGraph의 State는
#            보통 TypedDict로 정의해서 각 노드(Agent)가 같은 "모양"의 데이터를 주고받게 함.
# Optional[X]: X 타입이거나 None일 수 있다는 뜻 (Optional[str] = str 또는 None)
# List[X]: X 타입 원소들을 가진 리스트
# Literal[...]: 정해진 문자열 값들 중 하나만 허용 (오타 방지 + 자동완성 지원)


class VisionAnalysisResult(TypedDict):
    """Vision Agent 출력: 업로드된 미디어(이미지/영상) 분석 결과 1건

    media_keys 리스트의 항목 하나당 이 결과가 하나씩 생김.
    즉 사진 3장을 넣으면 vision_results 리스트 안에 이 타입이 3개 들어감.
    """
    media_key: str                  # 이 분석 결과가 어떤 미디어(S3 key)에 대한 것인지 식별용
    scene_description: str          # 장면 설명 (예: "공원에서 쓰레기를 줍는 모습")
                                     # -> LLM Story Agent가 자막 만들 때 이 텍스트를 재료로 씀
    mood_tags: List[str]            # 분위기/감정 태그 (예: ["활기찬", "밝은", "역동적"])
                                     # -> RAG Agent가 이 태그로 BGM을 검색함 (핵심 연결고리)
    detected_objects: List[str]     # 감지된 주요 객체/활동 (예: ["사람", "쓰레기봉투"])
                                     # -> 참고용 정보, 필요하면 자막/검증에서 활용 가능


class BgmMatchResult(TypedDict):
    """RAG Agent 출력: BGM 매칭 결과 (미디어 전체에 대해 1건만 생김)"""
    bgm_id: int                     # DB의 BackgroundMusic PK. ShortForm.bgm_id에 그대로 들어갈 값
                                     # (NOT NULL 제약이라 여기 값이 무조건 채워져야 다음 단계로 못 감)
    bgm_title: str                  # 화면 표시나 로그용 BGM 제목
    match_score: float              # RAG 유사도 점수 (0~1 사이 정도로 예상, 값이 낮으면 fallback 고려)
    match_reason: str               # 왜 이 BGM이 선택됐는지 근거 (디버깅/로그용, RAG 결과 설명)


class ShortFormState(TypedDict):
    """LangGraph 전체 파이프라인이 공유하는 State.
    각 노드(Agent 함수)는 이 State를 통째로 받아서, 자기 담당 필드만 채운 뒤
    State 전체를 리턴함. 그러면 다음 노드가 이어받아서 또 자기 필드를 채움.
    """

    # ── 입력 (파이프라인 시작 시 service.py/tasks.py에서 채워서 넣어줌) ──
    shorts_id: int                  # ShortForm 테이블의 PK. 렌더링 결과 저장 시 이 id로 DB 업데이트
    user_name: str                  # 자막에 들어갈 사용자 이름
    quest_title: str                # 자막에 들어갈 퀘스트 제목
    media_keys: List[str]           # 사용자가 업로드한 원본 이미지/영상의 S3 key 리스트 (Vision Agent 입력)
    edited_captions: Optional[List[str]]
        # 프론트에서 사용자가 미리 자막을 편집했다면 그 결과가 여기 들어옴.
        # None이면 LLM Story Agent가 새로 생성하고,
        # 값이 있으면 LLM Story Agent는 재생성 없이 이 값을 그대로 씀.

    # ── Vision Agent가 채우는 필드 ─────────────────────────────
    vision_results: List[VisionAnalysisResult]
        # media_keys 각각에 대한 분석 결과 리스트. 시작 시엔 빈 리스트 []

    # ── RAG Agent가 채우는 필드 ────────────────────────────────
    bgm_match: BgmMatchResult
        # 시작 시엔 값이 없는 상태(None)로 두고 RAG 단계에서 채워짐

    # ── LLM Story Agent가 채우는 필드 ─────────────────────────
    generated_captions: List[str]
        # 화면에 표시될 온스크린 자막 텍스트 리스트 (씬/미디어 개수만큼)

    # ── Validation Agent가 채우는 필드 ────────────────────────
    validation_passed: bool         # 검증 통과 여부 (True면 render로, False면 종료)
    validation_errors: List[str]    # 검증 실패 사유들 (여러 개 쌓일 수 있음)

    # ── FFmpeg Render Agent가 채우는 필드 ─────────────────────
    rendered_video_key: Optional[str]
        # 최종 렌더링된 영상의 S3 key. 렌더링 전에는 None, 완료되면 값이 채워짐

    # ── 파이프라인 전체가 공유하는 상태값 ──────────────────────
    status: Literal["PENDING", "GENERATING", "COMPLETED", "FAILED"]
        # DB의 ShortForm.status와 동일한 개념. 파이프라인 끝나면 이 값을 DB에 반영
    error_message: Optional[str]
        # 실패했을 때 사유 텍스트. DB의 ShortForm.error_message 컬럼에 그대로 저장될 값