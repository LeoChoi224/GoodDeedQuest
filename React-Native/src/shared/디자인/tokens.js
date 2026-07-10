// tokens.js — 선행퀘스트 RN 공통 디자인 토큰
// CLAUDE.md 컨벤션 반영: #033236(primary)/#FFFFFF(canvas)/#F6F6F6(parchment)/
// #1D1D1F(ink)/#7A7A7A(ink muted)/rgba(0,0,0,0.08)(hairline)/#C9A227,#FDF6E3(gold/gold tint)

export const COLORS = {
  primary: '#033236',
  canvas: '#FFFFFF',
  parchment: '#F6F6F6',
  ink: '#1D1D1F',
  inkMuted48: '#7A7A7A',
  hairline: 'rgba(0,0,0,0.08)',
  hairlineSolid: 'rgba(0,0,0,0.18)',
  gold: '#C9A227',
  goldTint: '#FDF6E3',
  mint: '#8BD19D',
};

export const RADIUS = { sm: 10, lg: 18, xl: 24, pill: 9999 };

export const TYPE = {
  display: { fontSize: 22, fontWeight: '600', letterSpacing: -0.3 },
  body: { fontSize: 17, letterSpacing: -0.37 },
  caption: { fontSize: 14, letterSpacing: -0.22 },
  micro: { fontSize: 10 },
};

export const GREEN_GRADIENT = ['#E8F7EA', '#F3FBF4', '#FFFFFF'];
export const GREEN_GRADIENT_LOCATIONS = [0, 0.45, 1];

export const RANK_BADGE_COLOR = { 1: COLORS.gold, 2: '#B0B0B0', 3: '#D18F7A' };
