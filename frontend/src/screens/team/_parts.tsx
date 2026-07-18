/**
 * 팀챌린지 플로우 (07) — screen-local building blocks, data, icons & popup buttons.
 * Ported 1:1 from 07_team_challenge_flow.dc.html. Only used inside src/screens/team/.
 * Reuses global tokens (theme.ts) + shared components; adds a few small SVG glyphs
 * the shared PixelIcons set doesn't include (search / chevrons / lock / megaphone / star).
 */
import React, { useEffect } from 'react';
import { View, Text, Image, Pressable, StyleSheet, StyleProp, ViewStyle, TextStyle } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Svg, { Path, Rect, Circle } from 'react-native-svg';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withRepeat,
  withTiming,
  interpolate,
  Easing,
} from 'react-native-reanimated';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { colors, fonts, gamePopup, CATEGORY_ICONS } from '../../theme';

const AnimatedPressable = Animated.createAnimatedComponent(Pressable);

/* ------------------------------------------------------------------ *
 * design-specific colors not present in theme (do NOT re-declare theme hexes)
 * ------------------------------------------------------------------ */
export const INFO = '#888888'; // 카드 보조 텍스트 (design #888)
export const CARD_DIVIDER = '#E0E0E0';
export const POPUP_CREAM = '#F5ECCB'; // popup pixel text (design)
export const ERR_TEXT = '#FF8A8A'; // popup 오류 문구
export const ERR_BORDER = '#FF4444'; // 오류 시 입력 테두리
export const OUTLINE_BORDER = '#5C6B60'; // 아니오 버튼 테두리
export const CHEV_GOLD = '#C7B48A';

/* ------------------------------------------------------------------ *
 * SVG glyphs (react-native-svg) — ported from renderVals()
 * ------------------------------------------------------------------ */
type IconProps = { size?: number; color?: string };

export const IconSearch = ({ size = 18, color = colors.primaryDark }: IconProps) => (
  <Svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={2} strokeLinecap="round">
    <Circle cx={11} cy={11} r={7} />
    <Path d="M21 21l-4-4" />
  </Svg>
);

export const IconChevDown = ({ size = 15, color = colors.primaryDark }: IconProps) => (
  <Svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
    <Path d="M6 9l6 6 6-6" />
  </Svg>
);

export const IconChevRight = ({ size = 20, color = CHEV_GOLD }: IconProps) => (
  <Svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
    <Path d="M9 5l7 7-7 7" />
  </Svg>
);

export const IconLock = ({ size = 18, color = colors.pixelBorder }: IconProps) => (
  <Svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
    <Rect x={5} y={11} width={14} height={9} rx={2} />
    <Path d="M8 11V8a4 4 0 0 1 8 0v3" />
  </Svg>
);

export const IconMega = ({ size = 20, color = colors.gold }: IconProps) => (
  <Svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
    <Path d="M3 11v2l13 5V6L3 11z" />
    <Path d="M16 8a4 4 0 0 1 0 8" />
  </Svg>
);

const StarSvg = ({ size = 26 }: { size?: number }) => (
  <Svg width={size} height={size} viewBox="0 0 24 24" fill={colors.gold} stroke="#A97D10" strokeWidth={1}>
    <Path d="M12 2l2.9 6.3 6.9.7-5.1 4.6 1.4 6.8L12 17.8 5.9 20.4l1.4-6.8L2.2 9l6.9-.7z" />
  </Svg>
);

/** 방장 별 — pulse/tilt (design tc-star: rotate ±8°, scale 1→1.12, 2s ease-in-out infinite). */
export function StarPulse({ size = 26 }: { size?: number }) {
  const p = useSharedValue(0);
  useEffect(() => {
    p.value = withRepeat(
      withTiming(1, { duration: 1000, easing: Easing.inOut(Easing.ease) }),
      -1,
      true,
    );
  }, []);
  const style = useAnimatedStyle(() => ({
    transform: [
      { rotate: `${interpolate(p.value, [0, 1], [-8, 8])}deg` },
      { scale: interpolate(p.value, [0, 1], [1, 1.12]) },
    ],
  }));
  return (
    <Animated.View style={style}>
      <StarSvg size={size} />
    </Animated.View>
  );
}

/* ------------------------------------------------------------------ *
 * Avatar — neutral gradient placeholder circle (no new art per contract).
 * ------------------------------------------------------------------ */
export const AVATARS: [string, string][] = [
  ['#4CAF50', '#2E7D32'],
  ['#5B9BD5', '#2E5A9B'],
  ['#E57373', '#B04A4A'],
  ['#FF9E5A', '#B96A28'],
];

export function Avatar({
  grad,
  size = 48,
  child,
}: {
  grad: [string, string];
  size?: number;
  child?: React.ReactNode;
}) {
  return (
    <LinearGradient
      colors={grad}
      start={{ x: 0, y: 0 }}
      end={{ x: 1, y: 1 }}
      style={{ width: size, height: size, borderRadius: size / 2, overflow: 'hidden', alignItems: 'center', justifyContent: 'center' }}
    >
      {child}
    </LinearGradient>
  );
}

/* ------------------------------------------------------------------ *
 * Demo data (verbatim from renderVals())
 * ------------------------------------------------------------------ */
export type Room = {
  name: string;
  info: string;
  count: string;
  category: string;
  locked: boolean;
};

export const ROOMS: Room[] = [
  { name: '지구지킴이 원정대', info: '환경 · 매주 플로깅', count: '(3/8)', category: 'environment', locked: false },
  { name: '따뜻한 손길 봉사단', info: '봉사 · 주말 활동', count: '(5/10)', category: 'volunteer', locked: true },
  { name: '댕댕이 지킴이', info: '동물 · 유기견 보호', count: '(1/4)', category: 'animal', locked: false },
  { name: '나눔한스푼', info: '나눔 · 무료급식', count: '(6/8)', category: 'sharing', locked: true },
];

export const MEMBERS = [
  { name: '에코리', lv: 8 },
  { name: '초록마음', lv: 6 },
  { name: '봉사왕', lv: 11 },
].map((m, i) => ({ ...m, grad: AVATARS[(i + 1) % AVATARS.length] }));

export const RECOMMEND_USERS = [
  { name: 'sunny_day', info: 'AI 성향: 환경·봉사 활발' },
  { name: 'green_soul', info: 'AI 성향: 나눔 관심 높음' },
  { name: 'kind_kim', info: 'AI 성향: 지역사회 적극' },
  { name: 'eco_lee', info: 'AI 성향: 동물 보호 선호' },
].map((u, i) => ({ ...u, grad: AVATARS[i % AVATARS.length] }));

export const TEAMS = [
  { name: '지구지킴이 원정대', info: '환경 · 8인 팀', category: 'environment' },
  { name: '따뜻한 손길 봉사단', info: '봉사 · 10인 팀', category: 'volunteer' },
  { name: '마을 이야기꾼', info: '지역사회 · 6인 팀', category: 'community' },
  { name: '댕댕이 지킴이', info: '동물 · 4인 팀', category: 'animal' },
];

/** stagger delay per design: 0.05 + i*0.07s → ms */
export const staggerDelay = (i: number) => 50 + i * 70;

/* ------------------------------------------------------------------ *
 * Search + sort bar (방 찾기 / 유저 추천 공통)
 * ------------------------------------------------------------------ */
export function SearchSortBar({ placeholder, sortLabel }: { placeholder: string; sortLabel: string }) {
  return (
    <View style={sb.row}>
      <View style={sb.search}>
        <IconSearch />
        <Text style={sb.searchPh}>{placeholder}</Text>
      </View>
      <View style={sb.sort}>
        <Text style={sb.sortText}>{sortLabel}</Text>
        <IconChevDown />
      </View>
    </View>
  );
}

const sb = StyleSheet.create({
  row: { flexDirection: 'row', gap: 8, marginBottom: 14 },
  search: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: colors.white,
    borderWidth: 1,
    borderColor: colors.pixelBorder,
    borderRadius: 24,
    paddingHorizontal: 14,
    paddingVertical: 10,
  },
  searchPh: { fontSize: 13, color: colors.textMuted, fontFamily: fonts.bodyR },
  sort: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: colors.white,
    borderWidth: 1,
    borderColor: colors.pixelBorder,
    borderRadius: 8,
    paddingHorizontal: 10,
  },
  sortText: { fontSize: 12, fontWeight: '700', color: colors.primaryDark, fontFamily: fonts.bodyB },
});

/* ------------------------------------------------------------------ *
 * Pixel section title (DotGothic16)
 * ------------------------------------------------------------------ */
export function PixelTitle({
  children,
  size = 18,
  color = colors.primaryDark,
  style,
}: {
  children: React.ReactNode;
  size?: number;
  color?: string;
  style?: StyleProp<TextStyle>;
}) {
  return <Text style={[{ fontFamily: fonts.pixel, fontSize: size, color }, style]}>{children}</Text>;
}

/* ------------------------------------------------------------------ *
 * Category tile icon (48, pixelated)
 * ------------------------------------------------------------------ */
export function CatIcon({ category, size = 48 }: { category: string; size?: number }) {
  return (
    <Image
      source={CATEGORY_ICONS[category] ?? CATEGORY_ICONS.other}
      style={{ width: size, height: size, borderRadius: 10 }}
    />
  );
}

/* ------------------------------------------------------------------ *
 * Sticky bottom footer (gradient fade → screenBg), pinned above safe area.
 * ------------------------------------------------------------------ */
export function StickyFooter({ children, style }: { children: React.ReactNode; style?: StyleProp<ViewStyle> }) {
  const insets = useSafeAreaInsets();
  return (
    <LinearGradient
      colors={['rgba(238,246,240,0)', colors.screenBg]}
      locations={[0, 0.4]}
      style={[ft.footer, { paddingBottom: insets.bottom + 12 }, style]}
    >
      {children}
    </LinearGradient>
  );
}

const ft = StyleSheet.create({
  footer: { position: 'absolute', left: 0, right: 0, bottom: 0, paddingHorizontal: 16, paddingTop: 14 },
});

/* ------------------------------------------------------------------ *
 * Popup buttons (DotGothic16) — three variants matching the .dc.html popups.
 * Kept local (not shared PopupButtons) to preserve the pixel/teal/gold look 1:1.
 * ------------------------------------------------------------------ */
type BtnProps = { label: string; onPress?: () => void; style?: StyleProp<ViewStyle> };

/** 딥틸 bg + 골드 테두리 + 파치먼트 텍스트 (방 찾기 / 입력완료 / 돌아가기 / 예) */
export function PopupTealBtn({ label, onPress, style }: BtnProps) {
  return (
    <PressBtn onPress={onPress} style={[pbtn.base, pbtn.teal, style]}>
      <Text style={[pbtn.text, { color: colors.parchment }]}>{label}</Text>
    </PressBtn>
  );
}

/** 골드 bg + 다크 텍스트 (방 만들기) */
export function PopupGoldBtn({ label, onPress, style }: BtnProps) {
  return (
    <PressBtn onPress={onPress} style={[pbtn.base, pbtn.gold, style]}>
      <Text style={[pbtn.text, { color: colors.primaryDark }]}>{label}</Text>
    </PressBtn>
  );
}

/** 투명 + 미묘한 테두리 + 크림 텍스트 (아니오) */
export function PopupOutlineBtn({ label, onPress, style }: BtnProps) {
  return (
    <PressBtn onPress={onPress} style={[pbtn.base, pbtn.outline, style]}>
      <Text style={[pbtn.text, { color: POPUP_CREAM }]}>{label}</Text>
    </PressBtn>
  );
}

/** tiny spring-press wrapper (transform only) shared by popup buttons.
 *  Style is applied to the Pressable itself so `flex:1` distributes inside a row. */
function PressBtn({ children, onPress, style }: { children: React.ReactNode; onPress?: () => void; style?: StyleProp<ViewStyle> }) {
  const s = useSharedValue(1);
  const aStyle = useAnimatedStyle(() => ({ transform: [{ scale: s.value }] }));
  return (
    <AnimatedPressable
      onPress={onPress}
      onPressIn={() => {
        s.value = withTiming(0.95, { duration: 110, easing: Easing.bezier(0.4, 0, 0.2, 1) });
      }}
      onPressOut={() => {
        s.value = withTiming(1, { duration: 140, easing: Easing.bezier(0.34, 1.56, 0.64, 1) });
      }}
      style={[style, aStyle]}
    >
      {children}
    </AnimatedPressable>
  );
}

const pbtn = StyleSheet.create({
  base: { flex: 1, height: 48, borderRadius: 8, alignItems: 'center', justifyContent: 'center' },
  teal: { backgroundColor: colors.primaryDark, borderWidth: 1.5, borderColor: colors.gold },
  gold: { backgroundColor: colors.gold },
  outline: { backgroundColor: 'rgba(255,248,231,0.1)', borderWidth: 1, borderColor: OUTLINE_BORDER },
  text: { fontFamily: fonts.pixel, fontSize: 15 },
});

/* ------------------------------------------------------------------ *
 * GamePanel — inline (non-modal, NO dim) dark-teal card used by Screen 1
 * (커뮤니티 피드 위 중앙 카드 팝업, dim 없음). Same visual as the game popup.
 * ------------------------------------------------------------------ */
export function GamePanel({ children, style }: { children: React.ReactNode; style?: StyleProp<ViewStyle> }) {
  return (
    <View style={[gp.outer, style]}>
      <LinearGradient colors={gamePopup.goldFrame} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={gp.frame}>
        <LinearGradient colors={['#0C4249', '#052024']} start={{ x: 0.5, y: 0 }} end={{ x: 0.5, y: 1 }} style={gp.body}>
          {children}
        </LinearGradient>
      </LinearGradient>
    </View>
  );
}

const gp = StyleSheet.create({
  outer: {
    borderRadius: 22,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 24 },
    shadowOpacity: 0.55,
    shadowRadius: 40,
    elevation: 18,
  },
  frame: { padding: 2.5, borderRadius: 22 },
  body: {
    borderRadius: 20,
    paddingHorizontal: 24,
    paddingVertical: 26,
    borderWidth: 1.5,
    borderColor: gamePopup.innerRing,
  },
});
