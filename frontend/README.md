# 📱 Good Deed Quest Frontend (React Native Mobile App)

선행퀘스트(Good Deed Quest)의 모바일 앱 프로젝트입니다. **React Native + TypeScript**를 기반으로 설계되었습니다.

## 📂 디렉토리 구조 (Feature-based)

```text
frontend/
├── src/
│   ├── admin/             # 관리자 기능 화면 [AdminScreen.tsx]
│   ├── auth/              # 로그인 및 회원가입 화면 [AuthScreen.tsx]
│   ├── challenge/         # 협동 챌린지 및 팀원 관리 화면 [ChallengeScreen.tsx]
│   ├── coach/             # RAG 기반 AI 코칭 채팅방 화면 [CoachScreen.tsx]
│   ├── common/            # 공통 API 클라이언트 [api.ts]
│   ├── growth/            # 레벨, XP, 연속 스트릭 현황 대시보드 [GrowthScreen.tsx]
│   ├── map/               # 카카오맵 연동 및 GPS 스팟 탐색 화면 [MapScreen.tsx]
│   ├── quest_recommend/   # AI 퀘스트 추천 리스트 화면 [RecommendScreen.tsx]
│   ├── quest_verification/# Vision AI 카메라 찰영 및 인증 화면 [VerificationScreen.tsx]
│   ├── shop/              # [NEW] 독립 기부 및 굿즈 포인트 상점 화면 [ShopScreen.tsx]
│   └── shorts/            # AI 요약 나레이션 숏폼 생성 요청 화면 [ShortsScreen.tsx]
├── App.tsx                # 모바일 앱 메인 탭바 네비게이션 및 진입점
├── package.json           # 앱 패키지 및 의존성
└── tsconfig.json          # TypeScript 컴파일 설정
```

## 🛠️ 개발 시작하기

### 1. 패키지 설치

`frontend/` 폴더로 이동한 뒤 패키지를 설치합니다.

```bash
npm install
```

### 2. 메트로 번들러 실행 (Metro Start)

React Native 번들러를 띄웁니다:

```bash
npm run start
```

### 3. 디바이스 빌드 및 실행

동작을 확인할 기기에 따라 에뮬레이터 또는 실기기를 준비하고 실행합니다.

* **Android**: `npm run android`
* **iOS (macOS만 지원)**: `npm run ios`

---

## 🎨 UI 및 협업 가이드

1. **StyleSheet 공통 디자인**:
   - 모바일 환경에 대응하기 위해 스타일은 React Native의 `StyleSheet` API를 이용해 작성합니다.
   - 다크 테마 배경색(`#0b0f19`)과 글래스모피즘 분위기를 내는 반투명 카드 배경색(`rgba(255, 255, 255, 0.03)` 및 얇은 테두리 `rgba(255, 255, 255, 0.08)`)이 구현되어 있어 복사해서 디자인에 활용할 수 있습니다.
2. **API 연동 (`src/common/api.ts`)**:
   - 로컬 테스트 환경을 위해 Platform별 기본 주소 분기 처리가 탑재되어 있습니다:
     - Android 에뮬레이터 기동 시: `http://10.0.2.2:8000/api/v1` 로 자동 변환
     - iOS 시뮬레이터 기동 시: `http://localhost:8000/api/v1` 로 자동 변환
   - `FormData` 전송 시 React Native 특유의 `{ uri, name, type }` 포맷을 준수하여 작성해야 합니다. (`src/quest_verification/VerificationScreen.tsx` 파일의 보일러플레이트를 참고하세요)
3. **아이콘 리소스**:
   - `lucide-react-native` 라이브러리를 이용하여 React Native Native 요소들과 매치되는 경량 벡터 아이콘을 편리하게 로드할 수 있습니다.
