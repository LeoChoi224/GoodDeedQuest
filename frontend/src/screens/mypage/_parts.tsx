/**
 * 마이페이지 플로우 (06) — screen-local parts shared by MyPage / Level / Rank.
 * Ports the 06_mypage_flow.dc.html decorations to RN + react-native-svg + Reanimated:
 *  - ConicAvatar : rotating rainbow conic ring + gold ring + green app-icon disc (+deco)
 *  - Sparkle / CameraBadge / ChevronRight glyphs
 *  - useCountUp hook (count-up motion)
 *  - static data (achievements, ranks, weekly chart) extracted verbatim from the .dc.html
 */
import React, { useEffect, useRef, useState } from 'react';
import { View, Image, StyleSheet } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Svg, { Path, Circle } from 'react-native-svg';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withRepeat,
  withTiming,
  withDelay,
  Easing,
} from 'react-native-reanimated';
import { colors, brand } from '../../theme';

/* ------------------------------------------------------------------ *
 *  arc helpers (react-native-svg has no conic-gradient → segment ring) *
 * ------------------------------------------------------------------ */
function polar(cx: number, cy: number, r: number, deg: number) {
  const a = ((deg - 90) * Math.PI) / 180;
  return [cx + r * Math.cos(a), cy + r * Math.sin(a)];
}
function arc(cx: number, cy: number, r: number, start: number, end: number) {
  const [x1, y1] = polar(cx, cy, r, end);
  const [x2, y2] = polar(cx, cy, r, start);
  const large = end - start <= 180 ? 0 : 1;
  return `M ${x1.toFixed(2)} ${y1.toFixed(2)} A ${r} ${r} 0 ${large} 0 ${x2.toFixed(2)} ${y2.toFixed(2)}`;
}
/** a full donut ring built from equal colored arc segments */
function SegmentRing({ d, colorsArr, width }: { d: number; colorsArr: string[]; width: number }) {
  const r = d / 2 - width / 2;
  const n = colorsArr.length;
  const seg = 360 / n;
  return (
    <Svg width={d} height={d}>
      {colorsArr.map((c, i) => (
        <Path
          key={i}
          d={arc(d / 2, d / 2, r, i * seg - 1, (i + 1) * seg + 1)}
          stroke={c}
          strokeWidth={width}
          strokeLinecap="round"
          fill="none"
        />
      ))}
    </Svg>
  );
}

const RAINBOW = ['#F5D874', '#4CAF50', '#5B9BD5', '#D4A017', '#F0C24B', '#F5D874'];
const GOLD = ['#F5D874', '#C99A20', '#F0C24B', '#A97D10', '#F5D874'];

/* ------------------------------------------------------------------ *
 *  ConicAvatar — rotating rainbow ring + gold ring + green icon disc   *
 * ------------------------------------------------------------------ */
export function ConicAvatar({
  size = 64,
  deco = false,
  imageUri = null, // ⭐ 수정: 실제 프로필 이미지 URI (없으면 기본 앱 아이콘)
}: {
  size?: number;
  deco?: boolean;
  imageUri?: string | null;
}) {
  const inset = size >= 60 ? 5 : 4;
  const pad = size >= 60 ? 3 : 2.5;
  const inner = size - pad * 2;
  const img = inner - 4;
  const D = size + inset * 2;

  const rot = useSharedValue(0);
  const glow = useSharedValue(0.15);
  useEffect(() => {
    rot.value = withRepeat(withTiming(360, { duration: 5000, easing: Easing.linear }), -1);
    glow.value = withRepeat(
      withTiming(0.4, { duration: 1500, easing: Easing.inOut(Easing.ease) }),
      -1,
      true
    );
  }, []);
  const spin = useAnimatedStyle(() => ({ transform: [{ rotate: `${rot.value}deg` }] }));
  const halo = useAnimatedStyle(() => ({ opacity: glow.value }));

  return (
    <View style={{ width: size, height: size }}>
      {/* soft gold glow halo (pulse) */}
      <Animated.View
        style={[
          {
            position: 'absolute',
            top: -inset,
            left: -inset,
            width: D,
            height: D,
            borderRadius: D / 2,
            backgroundColor: '#F5D874',
          },
          halo,
        ]}
      />
      {/* rotating rainbow conic ring */}
      <Animated.View style={[{ position: 'absolute', top: -inset, left: -inset }, spin]}>
        <SegmentRing d={D} colorsArr={RAINBOW} width={inset + 3} />
      </Animated.View>
      {/* static gold ring */}
      <View style={{ position: 'absolute', top: 0, left: 0 }}>
        <SegmentRing d={size} colorsArr={GOLD} width={pad + 2} />
      </View>
      {/* green app-icon disc */}
      <View
        style={{
          position: 'absolute',
          top: pad,
          left: pad,
          width: inner,
          height: inner,
          borderRadius: inner / 2,
          borderWidth: 2,
          borderColor: colors.parchment,
          overflow: 'hidden',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <LinearGradient
          colors={['#4CAF50', '#2E7D32']}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
          style={StyleSheet.absoluteFill}
        />
        <Image source={imageUri ? { uri: imageUri } : brand.appIcon} style={{ width: img, height: img }} />
      </View>

      {deco && (
        <>
          <Sparkle style={{ top: -3, right: 4 }} color="#F5D874" fontSize={12} delay={0} />
          <Sparkle style={{ bottom: 2, left: -4 }} color="#F0C24B" fontSize={9} delay={600} />
          <Sparkle style={{ top: 8, left: -6 }} color="#7FD69A" fontSize={8} delay={1000} />
          <CameraBadge size={24} style={{ bottom: -2, right: -2 }} />
        </>
      )}
    </View>
  );
}

/* ------------------------------------------------------------------ *
 *  Sparkle (twinkle: opacity .3→1 · scale .7→1.15)                     *
 * ------------------------------------------------------------------ */
export function Sparkle({
  style,
  color,
  fontSize,
  delay = 0,
}: {
  style?: any;
  color: string;
  fontSize: number;
  delay?: number;
}) {
  const t = useSharedValue(0);
  useEffect(() => {
    t.value = withDelay(
      delay,
      withRepeat(withTiming(1, { duration: 900, easing: Easing.inOut(Easing.ease) }), -1, true)
    );
  }, []);
  const anim = useAnimatedStyle(() => ({
    opacity: 0.3 + t.value * 0.7,
    transform: [{ scale: 0.7 + t.value * 0.45 }],
  }));
  return (
    <Animated.Text
      style={[{ position: 'absolute', color, fontSize, zIndex: 3 }, style, anim]}
    >
      ✦
    </Animated.Text>
  );
}

/* ------------------------------------------------------------------ *
 *  small SVG glyphs                                                    *
 * ------------------------------------------------------------------ */
export function CameraBadge({ size = 24, style }: { size?: number; style?: any }) {
  return (
    <View
      style={[
        {
          position: 'absolute',
          width: size,
          height: size,
          borderRadius: size / 2,
          backgroundColor: colors.primaryDark,
          borderWidth: 2,
          borderColor: colors.parchment,
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 4,
        },
        style,
      ]}
    >
      <Svg width={13} height={13} viewBox="0 0 24 24" fill="none" stroke={colors.parchment} strokeWidth={2.2} strokeLinecap="round" strokeLinejoin="round">
        <Path d="M4 8h3l1.5-2h7L17 8h3v11H4z" />
        <Circle cx={12} cy={13} r={3} />
      </Svg>
    </View>
  );
}

export function ChevronRight({ size = 22, color = colors.primaryDark }: { size?: number; color?: string }) {
  return (
    <Svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <Path d="M9 5l7 7-7 7" />
    </Svg>
  );
}

/* ------------------------------------------------------------------ *
 *  useCountUp — ease-in-out count-up (count-up motion)                 *
 * ------------------------------------------------------------------ */
export function useCountUp(target: number, duration = 1100) {
  const [val, setVal] = useState(0);
  const raf = useRef<number | null>(null);
  useEffect(() => {
    const start = Date.now();
    const tick = () => {
      const t = Math.min(1, (Date.now() - start) / duration);
      const eased = 0.5 - Math.cos(Math.PI * t) / 2; // ease-in-out
      setVal(Math.round(target * eased));
      if (t < 1) raf.current = requestAnimationFrame(tick);
    };
    raf.current = requestAnimationFrame(tick);
    return () => {
      if (raf.current) cancelAnimationFrame(raf.current);
    };
  }, [target]);
  return val;
}

export const comma = (n: number) => n.toLocaleString('en-US');

/* ------------------------------------------------------------------ *
 *  DATA — verbatim from 06_mypage_flow.dc.html                         *
 * ------------------------------------------------------------------ */
// ⭐ 수정: 퀘스트 달성 타임라인 더미데이터(Achievement/ACHIEVEMENTS) 제거 —
// 실 데이터는 api/mypage.ts::getMyQuestAchievements()로 대체 (MyPageScreen.tsx 참고)

export type RankRow = { rank: string; name: string; val: string };

export const RANKS_LEVEL: RankRow[] = [
  { rank: '1위', name: 'user1', val: '100lv' },
  { rank: '2위', name: 'user2', val: '92lv' },
  { rank: '3위', name: '사용자 (나)', val: '79lv' },
  { rank: '4위', name: 'user4', val: '71lv' },
  { rank: '5위', name: 'user5', val: '64lv' },
  { rank: '6위', name: 'user6', val: '58lv' },
];

export const RANKS_BATTLE: RankRow[] = [
  { rank: '🥇', name: 'quest_king', val: '2,480pt' },
  { rank: '🥈', name: 'green_soul', val: '2,210pt' },
  { rank: '🥉', name: 'user2', val: '1,980pt' },
  { rank: '4위', name: 'kind_kim', val: '1,640pt' },
  { rank: '5위', name: 'eco_lee', val: '1,420pt' },
  { rank: '6위', name: 'sunny', val: '1,180pt' },
];

// weekly EXP chart (line chart) — verbatim
export const CHART = {
  W: 300,
  H: 130,
  pad: 24,
  maxV: 140,
  days: ['월', '화', '수', '목', '금', '토', '일'],
  thisW: [20, 45, 40, 80, 70, 110, 130],
  lastW: [10, 30, 55, 50, 60, 75, 95],
  grid: [0, 35, 70, 105, 140],
};
export const chartX = (i: number) => CHART.pad + (CHART.W - CHART.pad * 2) * (i / 6);
export const chartY = (v: number) => CHART.H - 20 - (CHART.H - 34) * (v / CHART.maxV);
export function chartLine(arr: number[]) {
  return arr.map((v, i) => (i ? 'L' : 'M') + chartX(i).toFixed(1) + ' ' + chartY(v).toFixed(1)).join(' ');
}
export function pathLength(arr: number[]) {
  let len = 0;
  for (let i = 1; i < arr.length; i++) {
    const dx = chartX(i) - chartX(i - 1);
    const dy = chartY(arr[i]) - chartY(arr[i - 1]);
    len += Math.hypot(dx, dy);
  }
  return len;
}
