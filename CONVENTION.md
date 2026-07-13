# 📝 Good Deed Quest 코딩 컨벤션 & 패키지 구조

이 문서는 선행퀘스트(Good Deed Quest) 팀원들이 코드 가독성을 높이고 협업 시 발생할 수 있는 충돌을 최소화하기 위해 정의한 약속입니다.

---

## 1. 명명 규칙 (Naming Convention)

* **카멜 케이스 (camelCase)**: 첫 단어는 소문자, 이후 단어의 첫 글자는 대문자로 표기
  - 사용처: 변수명, 함수명 (JS/TS)
  - 예: `userName`, `totalAmount`, `getUserName()`
* **파스칼 케이스 (PascalCase)**: 각 단어의 첫 글자를 대문자로 표기
  - 사용처: 클래스명, React Native 컴포넌트명, Context/Enum명
  - 예: `UserService`, `UserController`, `LoginScreen`, `AuthContext`
* **스네이크 케이스 (snake_case)**: 단어 사이를 언더스코어(`_`)로 구분하고 모든 문자를 소문자로 표기
  - 사용처: Python 변수/함수/파일명
  - 예: `user_name`, `phone_number`, `auth_service.py`
* **상수 (UPPER_SNAKE_CASE)**: 모든 문자를 대문자로 표기하고 언더스코어로 구분
  - 예: `API_KEY`, `DEFAULT_TIMEOUT`

---

## 2. 언어 및 프레임워크별 명명 규칙

### 🐍 Python (FastAPI)
* **변수, 함수**: 스네이크 케이스
  - 예: `user_name`, `get_current_user()`
* **파일, 모듈**: 스네이크 케이스
  - 예: `auth_service.py`, `jwt_utils.py`
* **클래스 / Enum**: 파스칼 케이스
  - 예: `UserService`, `UserRole`
* **상수**: 대문자 스네이크 케이스
  - 예: `API_KEY`, `DEFAULT_TIMEOUT`

### 📱 React Native (JavaScript)
* **변수, 함수**: 카멜 케이스
  - 예: `userName`, `getUserName()`
* **컴포넌트**: 파스칼 케이스
  - 예: `LoginScreen`, `VerificationScreen`
* **Hook**: 카멜 케이스 (단, `use` 접두사 필수)
  - 예: `useAuth()`, `useStatus()`
* **Context**: 파스칼 케이스
  - 예: `AuthContext`, `UserStatus`
* **파일(컴포넌트)**: 파스칼 케이스 + **.js 확장자**
  - 예: `LoginScreen.js`, `MainScreen.js`
* **파일(기능/API)**: 카멜 케이스 + **.js 확장자**
  - 예: `loginService.js`, `authService.js`
* **상수**: 대문자 스네이크 케이스
  - 예: `API_KEY`, `DEFAULT_TIMEOUT`

---

## 3. 주석 작성 규칙

### Python
* 함수와 클래스 정의 직후 Google Style Docstring을 작성합니다.
```python
class UserService:
    """사용자 관련 비즈니스 로직"""

    def get_user(self, user_id: int):
        """
        사용자 조회
        Args:
            user_id (int): 사용자 ID
        Returns:
            User: 사용자 정보
        """
```
* 해결이 필요한 작업에는 `# TODO`, 급한 버그 수정 지점에는 `# FIXME` 주석을 활용합니다.
```python
# TODO: JWT Refresh Token 적용
# FIXME: 간헐적으로 None이 반환되는 문제 수정
```

### React Native (JS)
* 필요한 경우에 주석을 작성하며 TODO/FIXME 및 JSDoc을 지원합니다.
```javascript
/**
 * 로그인 API 호출
 * @param {Object} data
 * @returns {Promise}
 */
const login = async (data) => {
  // ...
};
```
```javascript
// TODO: 소셜 로그인 추가
// FIXME: Android에서 키보드 올라오는 버그 수정
```

---

## 4. 브랜치 전략 (Git Flow)

```text
main   (배포용 최종 브랜치)
 └── dev   (개발용 통합 브랜치)
      ├── feature/*   (기능 개발 브랜치)
      ├── release/*   (배포 준비 브랜치)
      └── hotfix/*    (긴급 버그 수정 브랜치)
```

### 🏷️ 브랜치 명명 규칙
* **이슈가 있는 경우**: `feature/이슈번호-기능명` (예: `feature/23-login-api`, `feature/45-quest-recommend`)
* **이슈가 없는 경우**: `feature/기능명` (예: `feature/login-api`, `feature/auth`)

---

## 5. 커밋 메시지 규칙 (Commit Message)

형식: `<type>: <설명>`

### 주요 커밋 태그 (Type)
1. **feat**: 새로운 기능 추가
2. **fix**: 버그 수정
3. **chore**: 빌드 설정 변경, 패키지 업데이트 등 기능 외 수정
4. **refactor**: 기능 변경 없는 코드 구조 정리/리팩토링
5. **docs**: 문서(README 등) 작성 및 수정
6. **style**: 코드 포맷팅, 세미콜론 누락 수정 등 (동작에 영향 없는 스타일 수정)
7. **test**: 테스트 코드 추가/수정
8. **perf**: 성능 개선 목적의 코드 변경
9. **ci**: CI 설정 파일 및 스크립트 수정

### 예시
```text
feat: 로그인 API 구현
feat: AI 퀘스트 추천 기능 추가
fix: JWT 인증 오류 수정
docs: README 업데이트
refactor: QuestService 분리
```

---

## 📂 6. 전체 패키지 구조 (복사 가능)

```text
good-deed-quest/
├── .github/
│   └── PULL_REQUEST_TEMPLATE.md
├── backend/
│   ├── app/
│   │   ├── admin/
│   │   │   └── router.py
│   │   ├── auth/
│   │   │   └── router.py
│   │   ├── challenge/
│   │   │   └── router.py
│   │   ├── common/
│   │   │   ├── auth.py
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   └── response.py
│   │   ├── growth/
│   │   │   └── router.py
│   │   ├── map/
│   │   │   └── router.py
│   │   ├── notification/
│   │   │   └── router.py
│   │   ├── quest/
│   │   │   └── router.py
│   │   ├── quest_recommend/
│   │   │   ├── router.py (AI 코칭 API 통합)
│   │   │   └── router.py
│   │   ├── quest_verification/
│   │   │   └── router.py
│   │   ├── shop/
│   │   │   └── router.py
│   │   └── shorts/
│   │       └── router.py
│   ├── main.py
│   ├── README.md
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── admin/
│   │   │   └── AdminScreen.js
│   │   ├── auth/
│   │   │   └── AuthScreen.js
│   │   ├── challenge/
│   │   │   └── ChallengeScreen.js
│   │   ├── common/
│   │   │   └── api.js
│   │   ├── growth/
│   │   │   └── GrowthScreen.js
│   │   ├── map/
│   │   │   └── MapScreen.js
│   │   ├── quest_recommend/
│   │   │   ├── RecommendScreen.js

│   │   │   └── CoachScreen.js (AI 코치 채팅 화면 통합)
│   │   ├── quest_verification/
│   │   │   └── VerificationScreen.js
│   │   ├── shop/
│   │   │   └── ShopScreen.js
│   │   └── shorts/
│   │       └── ShortsScreen.js
│   ├── App.js
│   ├── package.json
│   └── README.md
└── ai/
    ├── app/
    │   ├── challenge_recommend/
    │   │   └── agent.py
    │   ├── common/
    │   │   ├── config.py
    │   │   └── llm.py
    │   ├── local_quest/
    │   │   └── agent.py
    │   ├── quest_recommend/
    │   │   ├── agent.py
    │   │   └── rag.py (AI 코치 RAG 통합)
    │   ├── quest_verification/
    │   │   └── verifier.py
    │   └── shorts/
    │       └── generator.py
    ├── main.py
    ├── README.md
    └── requirements.txt
```
