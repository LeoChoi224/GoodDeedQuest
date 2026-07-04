# 🛡️ Good Deed Quest Backend

선행퀘스트(Good Deed Quest)의 메인 API 서버입니다. **FastAPI** 프레임워크를 기반으로 하며, 기능별로 폴더가 분리되어 있어 각 팀원이 영역을 나누어 개발하기 용이합니다.

## 📂 디렉토리 구조 (Feature-based)

```text
backend/
├── app/
│   ├── admin/             # 관리자 페이지 및 신고 관리 API
│   ├── auth/              # JWT 회원가입 및 OAuth2 소셜 로그인 API
│   ├── challenge/         # 협동 챌린지팀 및 활동 공유 API
│   ├── coach/             # RAG 기반 AI 코칭 API (AI 서비스 연계)
│   ├── common/            # 데이터베이스 설정, 환경설정, 공통 응답 포맷
│   ├── growth/            # 레벨, XP, 배지, 포인트 획득 및 상점 API
│   ├── map/               # 카카오맵 연동, 위치 기반 퀘스트 조회 API
│   ├── notification/      # WebSocket 기반 실시간 알림 API
│   ├── quest/             # 일반 퀘스트 CRUD API
│   ├── quest_recommend/   # 맞춤형 AI 퀘스트 추천 API (AI 서비스 연계)
│   ├── quest_verification/# AI Vision 기반 이미지 인증 API (AI 서비스 연계)
│   └── shorts/            # AI 숏폼 영상 제작 API (AI 서비스 연계)
├── main.py                # FastAPI 서버 시작 및 라우터 등록 진입점
└── requirements.txt       # 의존성 패키지 목록
```

## 🛠️ 개발 시작하기

### 1. 가상환경 설정 및 실행 (Python 3.9+)

터미널을 열고 `backend/` 폴더로 이동한 뒤 가상환경을 만듭니다.

```bash
# 가상환경 생성
python -m venv venv

# 가상환경 활성화 (macOS/Linux)
source venv/bin/activate

# 가상환경 활성화 (Windows CMD)
venv\Scripts\activate

# 가상환경 활성화 (Windows PowerShell)
.\venv\Scripts\Activate.ps1
```

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. 개발 서버 구동

```bash
# 디렉토리 루트(backend/)에서 실행해야 함을 주의하세요!
python main.py
```

서버가 켜지면 브라우저에서 아래 링크에 접속할 수 있습니다.
- **API 서버 홈**: [http://localhost:8000/](http://localhost:8000/)
- **자동 완성 Swagger API 문서**: [http://localhost:8000/docs](http://localhost:8000/docs) (프론트엔드 팀원과 API 맞춰볼 때 활용)

## 🤝 협업 가이드 (팀원을 위한 팁)

1. **본인이 맡은 기능만 수정하기**: 
   - 예: "퀘스트 인증" 개발자라면 `app/quest_verification/` 폴더 안의 파일만 수정하고, 프론트엔드가 연동할 API를 구현합니다.
   - 이렇게 하면 Git Merge 시 충돌(Conflict)이 거의 발생하지 않습니다!
2. **API 응답 표준 준수**:
   - 프론트엔드와의 협업을 원활히 하기 위해 응답 포맷은 `app/common/response.py`에 정의된 `APIResponse`를 사용하여 반환하세요.
   ```python
   from backend.app.common.response import APIResponse
   
   return APIResponse.ok(data=your_data, message="조회 성공")
   ```
3. **데이터베이스 연결**:
   - `app/common/database.py`의 `get_db` 의존성을 주입하여 DB 세션을 사용할 수 있습니다.
   ```python
   from sqlalchemy.orm import Session
   from fastapi import Depends
   from backend.app.common.database import get_db
   
   @router.get("/")
   def test_db(db: Session = Depends(get_db)):
       # db.query(...) 로직 수행
       pass
   ```
