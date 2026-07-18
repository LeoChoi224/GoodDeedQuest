# 선행퀘스트 (Good Deed Quest) — React Native 앱

`design_files/*.dc.html` 디자인 핸드오프의 **9개 플로우 전체**를 하나의 실행 가능한
**Expo React Native** 앱으로 재구현하고 서로 연결한 결과물입니다.
모션은 `design_files/CLAUDE.md`의 Reanimated 매핑과 `10_interaction_gallery.dc.html`
이펙트를 따릅니다. (React Native + Reanimated + React Navigation)

## 스택

**Expo SDK 54** · React 19.1 · React Native 0.81.5 · Reanimated 4.1 (+ react-native-worklets) ·
React Navigation 7 (native-stack · bottom-tabs · drawer) · react-native-svg · New Architecture.

## 실행

```bash
cd seonhaeng-quest-rn
npm install            # 프로젝트에 .npmrc(legacy-peer-deps=true) 포함
npx expo start         # i(iOS) / a(Android) / w(web)
```

> Reanimated 4는 New Architecture 전용입니다. `app.json`의 `newArchEnabled: true` 유지.
> Babel 플러그인은 `react-native-worklets/plugin` (Reanimated 4에서 이전됨).

## 검증 상태 (evidence, SDK 54)

- `npx tsc --noEmit` → **0 errors** (React 19 타입, 전체 70개 소스 파일)
- `npx expo export --platform ios` → **성공** (4.18MB Hermes 번들; Reanimated 4 + worklets 플러그인 포함 모든 import/asset/babel 변환 통과)
- 모든 `navigate()` 대상 라우트가 실제로 존재함(정적 감사), 모든 asset `require` 경로 확인.
- 각 플로우는 담당 에이전트가 해당 `.dc.html` 대비 **5회 검증**을 수행.

## 연결 구조 (전 플로우 연결)

```
RootStack
├─ Login ─(로그인하기)→ Main       ─(회원가입)→ 회원가입 위저드
│    └ Terms → Account → Profile → Complete ─→ Login (순환)
└─ Main = AppDrawer (우측 햄버거 드로어)
     ├─ Main = BottomTabs  ← 하단 네비 (커뮤니티·지도·홈·상점·마이)
     │    ├─ Community: Feed → NewPost                         (03)
     │    ├─ Map:       Map → Ranking → Nearby → VolunteerDetail (05)
     │    ├─ Home:      QuestHome → QuestDetail → QuestVerify → QuestComplete → QuestRegister → AiRecommend (02)
     │    ├─ Shop:      Shop → ItemDetail → PurchaseHistory → Inventory (04)
     │    └─ My:        MyPage → Level → Rank                  (06)
     ├─ TeamChallenge:  TeamHome → RoomFind → TeamDetail → TeamList (07)
     ├─ Shortform:      PhotoSelect → Generating → Player      (08)
     └─ Admin:          Dashboard → UserList → ReportList → ReportDetail (09)
```

- **하단 네비게이션** (커스텀 tabBar `BottomNav`): 골드 활성 타일 + 스프링, 픽셀 아이콘.
- **햄버거 드로어** (우측): 탭 전환 + 팀챌린지/숏폼/관리자 진입 + 로그아웃(→ 로그인 리셋).
- **크로스 플로우**: 마이페이지 → 상점 보유아이템 / 숏폼 등 (React Navigation 부모 버블링).

## 플로우별 하이라이트

- **01 로그인/회원가입** — 다크 히어로(별·파티클·스카이라인), 약관 게이팅, 이메일/닉네임 중복확인, 완료 컨페티.
- **02 퀘스트** — 진행중 캐러셀, RPG 퀘스트 카드, 퀘스트 시작 아이리스 와이프, 인증 팝업(AI 승인/반려 shake), 완료 컨페티+카운트업, 퀘스트 등록, AI 추천 챗봇(타이핑).
- **03 커뮤니티** — 피드(하트 바운스), 댓글/좋아요/더보기 바텀시트, 신고 팝업(글자수·검증), 새 피드 작성.
- **04 상점** — 등급 프레임 아이템, 3D 틸트 상세, 구매 확인 팝업, 구매내역, 아이템/칭호 탭·장착 토스트.
- **05 지도** — 스타일라이즈 전국/시군구 SVG 지도, 지역 랭킹 바, AI 부족봉사 판단, 핀 팝업, 봉사 상세.
- **06 마이페이지** — 콘틱 링 프로필, 달성 타임라인, 경험치 바+주간 라인차트, 레벨/랭킹 탭·sticky 내 랭킹.
- **07 팀챌린지** — 방 찾기(자물쇠), 비밀번호 팝업(error shake), 방장/팀원 RBAC, 초대/추천 팝업, 팀 생성.
- **08 숏폼** — 사진 3열 선택, AI 대본 팝업, 음악 바텀시트(미리듣기), 생성 로더, 완료 플레이어+다운로드 토스트.
- **09 관리자** — 대시보드(2×2 스탯·7일 라인차트), 유저/신고 무한스크롤, 차단/삭제 확인 팝업.

## 공용 컴포넌트 (`src/components/`) & 인터랙션 갤러리 매핑

`MainHeader`·`BottomNav`·`DrawerContent`(chrome) · `SpringButton`(스프링 프레스) ·
`GdqInput`(포커스 링) · `Checkbox` · `Shake`(에러) · `Confetti` · `GamePopup`+`PopupButtons`(다크 게임 팝업) ·
`BottomSheet` · `Toast`(useToast) · `Shimmer`(스켈레톤) · `SegmentedTabs`(골드 필) ·
`PixelProgress` · `QuestCard`(RPG 카드) · `HazeBackground`·`Starfield`·`Skyline` · `PixelIcons`.

## 구조

```
App.tsx                       폰트 로드 + Providers
src/theme.ts                  디자인 토큰 (색·타이포·radius·shadow·모션·카테고리·게임팝업·nav)
src/navigation/               RootNavigator · AppDrawer · MainTabs · flowStacks
src/context/SignupContext     회원가입 위저드 상태·검증
src/components/               공용 컴포넌트 21개
src/screens/                  01 signup(5) + 02~09 플로우 화면 43개 (+각 폴더 _parts.tsx)
assets/                       brand · icons · icons-glyph · nav · maps (디자인 번들에서 복사)
CONTRACT.md                   (플로우 구현 시 사용한 공용 API·규약 문서)
```

## 재구현 시 감안 사항

- 상태바(9:41) 미표시 → SafeArea + 실제 OS 상태바 사용.
- CSS blur 블롭 배경 → RN 반투명 원형으로 근사(더 정확히는 `expo-blur`).
- 실제 SGIS 지도 SVG는 대용량/미지원 → react-native-svg로 단순화한 행정구역 도형으로 렌더.
- 피드/아이템/영상 이미지는 중립 플레이스홀더(신규 아트 미제작 규칙 준수).
- RBAC·AI 판정·비밀번호(데모 '1234') 등은 목업/로컬 상태로 시연.
