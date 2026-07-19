/**
 * Shop flow (04) — screen-local data + small building blocks shared across the four
 * shop screens. Verbatim from design_files/04_shop_flow.dc.html renderVals().
 * Item art = gradient boxes + emoji + rarity frames (no new art, per contract).
 */
import React, { useEffect } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import Svg, { Rect, Path } from 'react-native-svg';
import { LinearGradient } from 'expo-linear-gradient';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withRepeat,
  withTiming,
  Easing,
} from 'react-native-reanimated';
import { colors, fonts } from '../../theme';

/* ────────────────────────────── data ────────────────────────────── */

export type ShopItem = {
  id: string;
  name: string;
  desc: string;
  price: string; // "1,200"
  priceNum: number;
  c1: string;
  c2: string;
  emoji: string;
  rare: string; // frame / rarity accent color
  rareLabel: string; // 일반 · 희귀 · 영웅
  epic: boolean;
};

const rawItems: [string, string, string, string, string, string, string, string, string][] = [
  ['shield', '수호자의 방패', '프로필 수호자 뱃지', '1,200', '#5B9BD5', '#2E5A9B', '🛡️', '#5B9BD5', '희귀'],
  ['sword', '영웅의 검', '레벨업 EXP +5%', '2,000', '#D4A017', '#A97D10', '⚔️', '#D4A017', '영웅'],
  ['pot', '새싹 화분', '홈 화면 장식', '600', '#4CAF50', '#2E7D32', '🌱', '#4CAF50', '일반'],
  ['crown', '황금 왕관', '랭킹 프로필 강조', '3,000', '#F0C850', '#C99A20', '👑', '#D4A017', '영웅'],
  ['potion', '치유의 물약', '연속 달성 보호권', '900', '#E57373', '#B04A4A', '🧪', '#E57373', '희귀'],
];

export const SHOP_ITEMS: ShopItem[] = rawItems.map((a) => ({
  id: a[0],
  name: a[1],
  desc: a[2],
  price: a[3],
  priceNum: Number(a[3].replace(/,/g, '')),
  c1: a[4],
  c2: a[5],
  emoji: a[6],
  rare: a[7],
  rareLabel: a[8],
  epic: a[8] === '영웅',
}));

export type HistoryItem = { name: string; info: string; date: string; c1: string; c2: string; emoji: string };
export const HISTORY: HistoryItem[] = [
  { name: '수호자의 방패', info: '아이템 · 장식', date: '2026.07.08', c1: '#5B9BD5', c2: '#2E5A9B', emoji: '🛡️' },
  { name: '새싹 화분', info: '아이템 · 장식', date: '2026.07.02', c1: '#4CAF50', c2: '#2E7D32', emoji: '🌱' },
  { name: '치유의 물약', info: '아이템 · 소모품', date: '2026.06.28', c1: '#E57373', c2: '#B04A4A', emoji: '🧪' },
];

export type OwnedItem = { id: string; name: string; desc: string; c1: string; c2: string; emoji: string };
export const OWNED_ITEMS: OwnedItem[] = [
  { id: 'shield', name: '수호자의 방패', desc: '프로필 수호자 뱃지', c1: '#5B9BD5', c2: '#2E5A9B', emoji: '🛡️' },
  { id: 'pot', name: '새싹 화분', desc: '홈 화면 장식', c1: '#4CAF50', c2: '#2E7D32', emoji: '🌱' },
  { id: 'potion', name: '치유의 물약', desc: '연속 달성 보호권', c1: '#E57373', c2: '#B04A4A', emoji: '🧪' },
];

export const TITLES: OwnedItem[] = [
  { id: 'hero', name: '선한 영웅', desc: '누적 선행 100회 달성', c1: '#F0C850', c2: '#C99A20', emoji: '👑' },
  { id: 'guardian', name: '마을 수호자', desc: '환경 퀘스트 50회 달성', c1: '#4CAF50', c2: '#2E7D32', emoji: '🌿' },
  { id: 'angel', name: '나눔 천사', desc: '나눔 퀘스트 30회 달성', c1: '#E57373', c2: '#B04A4A', emoji: '💝' },
  { id: 'sprout', name: '새싹 지키미', desc: '첫 퀘스트 완료', c1: '#7FD69A', c2: '#4CAF50', emoji: '🌱' },
];

export const POINTS_NUM = 3250;
export const POINTS_LABEL = '3,250 P';

/* ─────────────────────────── pixel coin ─────────────────────────── */
// px rows from renderVals(): coin (gold) + coinW (white/on-pill).
const COIN_GOLD: [number, number, number, number, string][] = [
  [2, 1, 4, 1, '#A97D10'],
  [1, 2, 6, 4, '#E8B830'],
  [2, 6, 4, 1, '#A97D10'],
  [2, 2, 1, 2, '#F5D874'],
  [3, 3, 2, 1, '#C99A20'],
];
const COIN_WHITE: [number, number, number, number, string][] = [
  [2, 1, 4, 1, '#EED9A0'],
  [1, 2, 6, 4, '#FFFFFF'],
  [2, 6, 4, 1, '#EED9A0'],
  [2, 2, 1, 2, '#FFFFFF'],
];

export function PixelCoin({ size = 15, variant = 'gold' }: { size?: number; variant?: 'gold' | 'white' }) {
  const rows = variant === 'white' ? COIN_WHITE : COIN_GOLD;
  return (
    <Svg width={size} height={size} viewBox="0 0 8 8">
      {rows.map((r, i) => (
        <Rect key={i} x={r[0]} y={r[1]} width={r[2]} height={r[3]} fill={r[4]} />
      ))}
    </Svg>
  );
}

/* ───────────────────────── chevron (right) ──────────────────────── */
export function ChevronRight({ size = 20, color = '#C7B48A' }: { size?: number; color?: string }) {
  return (
    <Svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <Path d="M9 5l7 7-7 7" />
    </Svg>
  );
}

/* ─────────────────────── item art gradient tile ────────────────── */
/**
 * Neutral gradient box + emoji + optional rarity frame. `diagonal` uses the 135°
 * linear ramp (history/inventory tiles); otherwise a top→bottom ramp approximating
 * the design's radial(50% 28%) hero fill (RN has no radial gradient).
 */
export function ItemTile({
  c1,
  c2,
  emoji,
  size = 64,
  radius = 10,
  emojiSize = 26,
  frame,
  epic = false,
  diagonal = false,
  shine = false,
}: {
  c1: string;
  c2: string;
  emoji: string;
  size?: number;
  radius?: number;
  emojiSize?: number;
  frame?: string;
  epic?: boolean;
  diagonal?: boolean;
  shine?: boolean;
}) {
  return (
    <View
      style={{
        width: size,
        height: size,
        borderRadius: radius,
        overflow: 'hidden',
        borderWidth: frame ? 2 : 0,
        borderColor: frame,
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <LinearGradient
        colors={[c1, c2]}
        start={diagonal ? { x: 0, y: 0 } : { x: 0.5, y: 0 }}
        end={diagonal ? { x: 1, y: 1 } : { x: 0.5, y: 1 }}
        style={StyleSheet.absoluteFill}
      />
      {shine ? (
        <View
          pointerEvents="none"
          style={{
            position: 'absolute',
            top: -size * 0.3,
            left: -size * 0.1,
            width: size * 0.22,
            height: size * 1.6,
            backgroundColor: 'rgba(255,255,255,0.28)',
            transform: [{ rotate: '18deg' }],
          }}
        />
      ) : null}
      {epic ? <EpicGlow radius={radius} /> : null}
      <Text style={{ fontSize: emojiSize }}>{emoji}</Text>
    </View>
  );
}

/** Pulsing gold inner ring for 영웅 (epic) tiles — sp-epicglow, opacity-only. */
function EpicGlow({ radius }: { radius: number }) {
  const p = useSharedValue(0);
  useEffect(() => {
    p.value = withRepeat(withTiming(1, { duration: 1000, easing: Easing.inOut(Easing.quad) }), -1, true);
  }, []);
  const style = useAnimatedStyle(() => ({ opacity: 0.15 + p.value * 0.6 }));
  return (
    <Animated.View
      pointerEvents="none"
      style={[
        StyleSheet.absoluteFill,
        {
          borderRadius: radius,
          borderWidth: 2,
          borderColor: colors.gold,
          shadowColor: colors.gold,
          shadowOffset: { width: 0, height: 0 },
          shadowOpacity: 0.9,
          shadowRadius: 8,
        },
        style,
      ]}
    />
  );
}

/* ─────────────────────── glowing points pouch ──────────────────── */
/** Gold coin pouch pill (보유 포인트) with a soft breathing glow — sp-coinglow. */
export function PointsPouch({ points = POINTS_LABEL }: { points?: string }) {
  const g = useSharedValue(0);
  useEffect(() => {
    g.value = withRepeat(withTiming(1, { duration: 1300, easing: Easing.inOut(Easing.quad) }), -1, true);
  }, []);
  const glow = useAnimatedStyle(() => ({ opacity: 0.35 + g.value * 0.4, transform: [{ scale: 1 + g.value * 0.06 }] }));
  return (
    <View style={styles.pouchWrap}>
      <Animated.View pointerEvents="none" style={[styles.pouchGlow, glow]} />
      <LinearGradient colors={['#F0C24B', '#C99A20']} start={{ x: 0.5, y: 0 }} end={{ x: 0.5, y: 1 }} style={styles.pouch}>
        <PixelCoin size={15} variant="white" />
        <Text style={styles.pouchText}>{points}</Text>
      </LinearGradient>
    </View>
  );
}

const styles = StyleSheet.create({
  pouchWrap: { position: 'relative' },
  pouchGlow: {
    position: 'absolute',
    top: -4,
    left: -4,
    right: -4,
    bottom: -4,
    borderRadius: 999,
    backgroundColor: colors.gold,
    shadowColor: colors.gold,
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.7,
    shadowRadius: 12,
    elevation: 4,
  },
  pouch: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 7,
    borderRadius: 999,
    borderWidth: 1.5,
    borderColor: '#A97D10',
    paddingVertical: 7,
    paddingHorizontal: 14,
  },
  pouchText: {
    fontSize: 13,
    fontWeight: '800',
    color: colors.white,
    fontFamily: fonts.bodyB,
    textShadowColor: 'rgba(0,0,0,0.2)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 0,
  },
});
