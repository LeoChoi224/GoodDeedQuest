/**
 * 선행퀘스트 GLOBAL DESIGN SYSTEM — tokens
 * Extracted verbatim from README.md / design_files/CLAUDE.md / 01_login_flow.dc.html.
 * Do not invent new colors — reuse these.
 */

export const colors = {
  primaryDark: '#033236', // Primary dark teal (header, buttons, active)
  heroTop: '#033236',
  heroMid: '#022A2D',
  heroBottom: '#021E20',
  parchment: '#FFF8E7', // 카드 bg / celebration flash
  gold: '#D4A017', // accent / active
  xpGreen: '#4CAF50',
  screenBg: '#EEF6F0',
  pixelBorder: '#5C3D1E',
  danger: '#E53935',
  textPrimary: '#1A1A1A',
  textSecondary: '#6B7280',
  textMuted: '#9CA3AF',
  white: '#FFFFFF',
  inputBorder: '#E5E7EB',
  divider: '#E5E7EB',
  disabled: '#9CA3AF',
  kakao: '#FEE500',
  kakaoText: '#191919',
  googleBg: '#F6F6F6',
  cellHeader: '#EEF6F0',
  hairline: '#EFF1F0',
} as const;

// 공통 배경 — "뿌연 그린 그라데이션" (CLAUDE.md). Approximated in RN with a base
// linear gradient + soft radial-ish blobs (see HazeBackground.tsx).
export const hazeBase = {
  // linear-gradient(165deg, #EDF7F0 0%, #F5FBF6 100%)
  colors: ['#EDF7F0', '#F5FBF6'] as [string, string],
  start: { x: 0.15, y: 0 },
  end: { x: 0.85, y: 1 },
};

export const hazeBlobs = [
  { size: 260, color: '#9FD8B4', opacity: 0.55, top: -50, left: -70 },
  { size: 310, color: '#BFE8CC', opacity: 0.5, bottom: 90, right: -100 },
  { size: 230, color: '#7FCBA0', opacity: 0.3, top: '44%', left: '28%' },
] as const;

export const heroGradient = {
  // linear-gradient(180deg,#033236 0%,#022A2D 55%,#021E20 100%)
  colors: [colors.heroTop, colors.heroMid, colors.heroBottom] as [string, string, string],
  locations: [0, 0.55, 1] as [number, number, number],
};

export const radii = {
  phone: 44,
  card: 16,
  cardLg: 28,
  input: 12,
  button: 14,
  chip: 12,
  pill: 999,
} as const;

export const spacing = {
  screenX: 20, // 화면 좌우 마진 (signup screens use 20; login card 24)
  base: 8,
} as const;

export const shadow = {
  // 0 4px 14px rgba(3,50,54,.28) — primary button
  button: {
    shadowColor: '#033236',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.28,
    shadowRadius: 14,
    elevation: 6,
  },
  // 0 4px 16px rgba(0,0,0,.06) — parchment card
  card: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.06,
    shadowRadius: 16,
    elevation: 3,
  },
  // 0 24px 70px rgba(3,50,54,.28) — phone frame (n/a on real device)
  header: {
    shadowColor: '#033236',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 10,
    elevation: 2,
  },
} as const;

// Font families — loaded in App.tsx.
// Body = Pretendard (local OTF, assets/fonts). Pixel titles = DotGothic16 (google font).
export const fonts = {
  pixel: 'DotGothic16_400Regular', // 퀘스트 제목·픽셀 버튼·타이틀
  bodyR: 'Pretendard-Regular',
  bodyM: 'Pretendard-Medium',
  bodyB: 'Pretendard-Bold',
} as const;

/**
 * Reanimated motion vocabulary (CLAUDE.md 모션 규칙).
 * withTiming → cubic-bezier(.4,0,.2,1) standard ease
 * withSpring → overshoot cubic-bezier(.34,1.56,.64,1) pop/bounce
 */
export const easing = {
  standardBezier: [0.4, 0, 0.2, 1] as [number, number, number, number],
  overshootBezier: [0.34, 1.56, 0.64, 1] as [number, number, number, number],
};

export const spring = {
  // subtle pop — a little life, but no strong bounce/overshoot
  pop: { damping: 17, stiffness: 210, mass: 0.8 },
  // near-critical settle — press release barely overshoots
  press: { damping: 22, stiffness: 300, mass: 0.6 },
};

// Category accent/deep palette — from questcard.dc.html CATS map. Used by quest cards,
// spring category buttons (interaction gallery #3), map, shop, etc.
export const CATEGORY_COLORS: Record<string, { accent: string; deep: string }> = {
  volunteer: { accent: '#5B9BD5', deep: '#2E5A9B' },
  environment: { accent: '#57C878', deep: '#2E7D46' },
  sharing: { accent: '#EF8A8A', deep: '#B04A4A' },
  animal: { accent: '#FF9E5A', deep: '#B96A28' },
  community: { accent: '#B27BD0', deep: '#7A4A9B' },
  other: { accent: '#A7AEB8', deep: '#5E6670' },
};

// Dark "game popup" surface (딥틸 그라데이션 + 골드 테두리/이너 링 + 크림 텍스트).
export const gamePopup = {
  gradient: ['#0A4F55', '#033236', '#022528'] as [string, string, string],
  border: '#F2D783',
  innerRing: 'rgba(242,215,131,0.4)',
  cream: '#F5EFD8',
  goldFrame: ['#F8E6A6', '#C9A44C', '#9A7526'] as [string, string, string],
};

// Bottom nav (COMPONENT B): height 83, bg #033236, top border #5C3D1E 2px.
export const bottomNav = {
  height: 83,
  bg: '#033236',
  topBorder: '#5C3D1E',
  active: '#D4A017',
  inactive: 'rgba(255,255,255,0.6)',
};

export const NAV_ICONS: Record<string, any> = {
  community: require('../assets/nav/community.png'),
  map: require('../assets/nav/map.png'),
  home: require('../assets/nav/home.png'),
  shop: require('../assets/nav/shop.png'),
  my: require('../assets/nav/my.png'),
};

export const CATEGORY_GLYPHS: Record<string, any> = {
  volunteer: require('../assets/icons-glyph/volunteer.png'),
  environment: require('../assets/icons-glyph/environment.png'),
  sharing: require('../assets/icons-glyph/sharing.png'),
  animal: require('../assets/icons-glyph/animal.png'),
  community: require('../assets/icons-glyph/community.png'),
  other: require('../assets/icons-glyph/other.png'),
};

export const CATEGORY_DEFS = [
  { key: 'volunteer', label: '봉사' },
  { key: 'environment', label: '환경' },
  { key: 'sharing', label: '나눔' },
  { key: 'animal', label: '동물' },
  { key: 'community', label: '지역사회' },
  { key: 'other', label: '기타' },
] as const;

export const CATEGORY_ICONS: Record<string, any> = {
  volunteer: require('../assets/icons/volunteer.png'),
  environment: require('../assets/icons/environment.png'),
  sharing: require('../assets/icons/sharing.png'),
  animal: require('../assets/icons/animal.png'),
  community: require('../assets/icons/community.png'),
  other: require('../assets/icons/other.png'),
};

export const TIME_DEFS = ['0시~06시', '06시~12시', '12시~18시', '18시~24시'] as const;

export const brand = {
  appIcon: require('../assets/brand/app-icon.png'),
  appIconCheck: require('../assets/brand/app-icon-check.png'),
};
