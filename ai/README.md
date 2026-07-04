# 🤖 Good Deed Quest AI Service

선행퀘스트 플랫폼에서 작동하는 모든 AI 기술(LangGraph 추천, Gemini Vision 인증 검증, Whisper/TTS 숏폼 렌더링, FAISS RAG 코칭 봇)을 통합 관리하는 AI 서빙 서버입니다.

## 📂 디렉토리 구조 (Feature-based)

```text
ai/
├── app/
│   ├── challenge_recommend/ # 협동 챌린지 및 유사 관심사 팀 매칭 에이전트
│   ├── coach/               # FAISS 기반 RAG (문서 탐색 및 답변 생성) 코치
│   ├── common/              # OpenAI & Gemini API 연동 설정 및 모델 팩토리
│   ├── quest_recommend/     # LangGraph State Graph 기반 퀘스트 추천 에이전트
│   ├── quest_verification/  # Gemini Vision을 활용한 업로드 사진 검증 모듈
│   └── shorts/              # Whisper/TTS 및 FFmpeg 영상 병합 렌더러
├── main.py                  # FastAPI 서빙 진입점 (HTTP API 엔드포인트 제공)
└── requirements.txt         # AI 에이전트 전용 의존성 패키지
```

## 🛠️ 개발 시작하기

### 1. 가상환경 설정 및 실행 (Python 3.9+)

터미널을 열고 `ai/` 폴더로 이동한 뒤 가상환경을 만듭니다. (백엔드 가상환경과 충돌하지 않도록 분리해 줍니다)

```bash
# 가상환경 생성
python -m venv venv

# 가상환경 활성화 (macOS/Linux)
source venv/bin/activate

# 가상환경 활성화 (Windows CMD)
venv\Scripts\activate
```

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. API 키 설정 (환경변수)

에이전트 구동 및 이미지 분석을 위해 API 키가 필요합니다. 터미널 혹은 `.env`에 설정하세요.

```bash
# macOS/Linux
export OPENAI_API_KEY="your-openai-key"
export GEMINI_API_KEY="your-gemini-key"

# Windows CMD
set OPENAI_API_KEY="your-openai-key"
set GEMINI_API_KEY="your-gemini-key"
```

### 4. AI 개발 서버 구동

```bash
# 디렉토리 루트(ai/)에서 실행해야 함을 주의하세요!
python main.py
```

- **AI API 서버 홈**: [http://localhost:8001/](http://localhost:8001/)
- **자동 완성 Swagger API 문서**: [http://localhost:8001/docs](http://localhost:8001/docs)

## 🤝 AI 파트 개발 팁

1. **LangGraph 수정하기 (`app/quest_recommend/agent.py`)**:
   - `RecommendState`에 상태값을 보관하며 `retrieve_candidates` -> `rank_and_personalize` 노드로 데이터가 흘러갑니다.
   - 필터링 로직을 다각화하거나 엣지에 분기(Conditional Edge)를 추가하려면 이 파일을 수정하세요.
2. **Vision 인증 모델 튜닝 (`app/quest_verification/verifier.py`)**:
   - Gemini Vision 프롬프트를 추가 수정하여 인증의 정밀도(중복 인증 감지, 봉사 완료 판정 등)를 개선할 수 있습니다.
3. **RAG 코칭 지식 베이스 확장 (`app/coach/rag.py`)**:
   - 공익 캠페인 가이드라인, 1365 봉사 시간 혜택 등의 데이터를 `.txt` 또는 `.pdf`로 읽어와 FAISS 인덱스를 빌드하도록 `SimpleRAGCoach` 클래스를 확장하세요.
