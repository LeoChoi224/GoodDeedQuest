// =========================================================================
// File: frontend/src/screens/shop/_parts.tsx
// Description: 기존 UI 100% 보존 및 백엔드 프로필 테두리 이미지 동적 렌더링 지원 (최소 변경)
// =========================================================================
import React, { useEffect } from 'react';
import { View, Text, Image, StyleSheet } from 'react-native';
import Svg, { Rect, Path } from 'react-native-svg';
import { LinearGradient } from 'expo-linear-gradient';
import Constants from 'expo-constants';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withRepeat,
  withTiming,
  Easing,
} from 'react-native-reanimated';
import { colors, fonts } from '../../theme';

// =========================================================================
// [추가] 백엔드 정적 이미지 URL 변환 헬퍼 (Expo 에뮬레이터 / 실물기기 자동 대응)
// =========================================================================
// client.ts 와 같은 이유. 상점 테두리 이미지가 /static 경로로 서빙된다.
const debuggerHost = Constants.expoConfig?.hostUri?.split(':')[0];
const configuredApiUrl = Constants.expoConfig?.extra?.apiUrl as string | undefined;

export const BACKEND_BASE_URL = debuggerHost
  ? `http://${debuggerHost}:8000`
  : (configuredApiUrl ?? '');

export const getFullImageUrl = (url?: string): string => {
  if (!url) return '';
  if (url.startsWith('http://') || url.startsWith('https://')) {
    return url;
  }
  return `${BACKEND_BASE_URL}${url.startsWith('/') ? '' : '/'}${url}`;
};
// =========================================================================

/* ────────────────────────────── data ────────────────────────────── */

export type ShopItem = {
  id: string;
  name: string;
  desc: string;
  price: string;
  priceNum: number;
  c1: string;
  c2: string;
  emoji: string;
  rare: string;
  rareLabel: string;
  epic: boolean;
  image_url?: string;
};

export type HistoryItem = { name: string; info: string; date: string; c1: string; c2: string; emoji: string };
export type OwnedItem = { id: string; name: string; desc: string; c1: string; c2: string; emoji: string };

export const POINTS_NUM = 3250;
export const POINTS_LABEL = '3,250 P';

/* ─────────────────────────── pixel coin ─────────────────────────── */
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
export function ItemTile({
  c1 = '#4CAF50',
  c2 = '#2E7D32',
  emoji = '🛡️',
  size = 64,
  radius = 10,
  emojiSize = 26,
  frame,
  epic = false,
  diagonal = false,
  shine = false,
  imageUrl,
}: {
  c1?: string;
  c2?: string;
  emoji?: string;
  size?: number;
  radius?: number;
  emojiSize?: number;
  frame?: string;
  epic?: boolean;
  diagonal?: boolean;
  shine?: boolean;
  imageUrl?: string;
}) {
  // =========================================================================
  // [수정] DB 정적 테두리 이미지(imageUrl)가 전달되면 해당 테두리 자산을 렌더링
  // =========================================================================
  const fullUrl = getFullImageUrl(imageUrl);

  if (fullUrl) {
    return (
      <View
        style={{
          width: size,
          height: size,
          borderRadius: radius,
          overflow: 'hidden',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: '#F5F7F6',
        }}
      >
        <Image
          source={{ uri: fullUrl }}
          style={{ width: '100%', height: '100%' }}
          resizeMode="contain"
        />
      </View>
    );
  }

  // 기존 렌더링 구조 100% 유지를 위한 Fallback
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