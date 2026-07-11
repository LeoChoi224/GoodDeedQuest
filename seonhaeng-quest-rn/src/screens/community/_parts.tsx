/**
 * Community flow (03) — screen-local building blocks shared by FeedScreen & NewPostScreen.
 * Icons are ported 1:1 from 03_community_flow.dc.html renderVals() (React.createElement → react-native-svg).
 * Gradient placeholders stand in for feed photos / avatars (no new art per CONTRACT).
 */
import React from 'react';
import { View, Text, Pressable, StyleSheet, StyleProp, ViewStyle } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Svg, { Path, Circle } from 'react-native-svg';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withSequence,
  withTiming,
  withSpring,
  Easing,
} from 'react-native-reanimated';
import { colors, fonts, spring } from '../../theme';

/* ---------- icons (stroke() equivalent from the .dc.html) ---------- */
const Stroke = ({
  d,
  color = '#1A1A1A',
  w = 2,
  size = 24,
}: {
  d: string | string[];
  color?: string;
  w?: number;
  size?: number;
}) => (
  <Svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={w} strokeLinecap="round" strokeLinejoin="round">
    {(Array.isArray(d) ? d : [d]).map((p, i) => (
      <Path key={i} d={p} />
    ))}
  </Svg>
);

export const DotsIcon = ({ size = 22, color = '#6B7280' }: { size?: number; color?: string }) => (
  <Svg width={size} height={size} viewBox="0 0 24 24" fill={color}>
    <Circle cx={5} cy={12} r={2} />
    <Circle cx={12} cy={12} r={2} />
    <Circle cx={19} cy={12} r={2} />
  </Svg>
);

export const CommentIcon = ({ size = 24, color = '#1A1A1A' }: { size?: number; color?: string }) => (
  <Stroke d="M4 6h16v10H9l-4 3v-3H4z" color={color} size={size} />
);

export const ChevronDownIcon = ({ size = 24, color = '#9CA3AF' }: { size?: number; color?: string }) => (
  <Stroke d="M6 9l6 6 6-6" color={color} w={2.4} size={size} />
);

export const SirenIcon = ({ size = 24, color = '#E53935' }: { size?: number; color?: string }) => (
  <Stroke d={['M12 4a5 5 0 0 1 5 5v5H7V9a5 5 0 0 1 5-5z', 'M5 19h14', 'M12 2v1']} color={color} size={size} />
);

export const XCircleIcon = ({ size = 24, color = '#9CA3AF' }: { size?: number; color?: string }) => (
  <Svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
    <Circle cx={12} cy={12} r={9} />
    <Path d="M9 9l6 6M15 9l-6 6" />
  </Svg>
);

export const WhiteCheck = ({ size = 14, color = '#fff' }: { size?: number; color?: string }) => (
  <Stroke d="M5 13l4 4 10-11" color={color} w={3} size={size} />
);

export const PlayIcon = ({ size = 20, color = '#fff' }: { size?: number; color?: string }) => (
  <Svg width={size} height={size} viewBox="0 0 24 24" fill={color}>
    <Path d="M8 5v14l11-7z" />
  </Svg>
);

const HEART_D = 'M12 21C5 15.5 3 12 3 8.5A4.5 4.5 0 0 1 12 6a4.5 4.5 0 0 1 9 2.5C21 12 19 15.5 12 21z';
export const HeartFilled = ({ size = 24 }: { size?: number }) => (
  <Svg width={size} height={size} viewBox="0 0 24 24" fill={colors.danger}>
    <Path d={HEART_D} />
  </Svg>
);
export const HeartOutline = ({ size = 24 }: { size?: number }) => (
  <Stroke d={HEART_D} color={colors.textMuted} w={2} size={size} />
);

/* ---------- gradient placeholders (feed photo / avatar) ---------- */
export const Avatar = ({ grad, size = 36 }: { grad: [string, string]; size?: number }) => (
  <LinearGradient colors={grad} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={{ width: size, height: size, borderRadius: size / 2 }} />
);

export const GradientFill = ({
  grad,
  style,
  children,
}: {
  grad: [string, string];
  style?: StyleProp<ViewStyle>;
  children?: React.ReactNode;
}) => (
  <LinearGradient colors={grad} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={style}>
    {children}
  </LinearGradient>
);

/** ▶ badge (rgba black circle + play glyph) — video overlays. */
export const PlayBadge = ({ size = 52 }: { size?: number }) => (
  <View
    style={{
      width: size,
      height: size,
      borderRadius: size / 2,
      backgroundColor: 'rgba(0,0,0,0.4)',
      alignItems: 'center',
      justifyContent: 'center',
    }}
  >
    <PlayIcon size={size * 0.4} />
  </View>
);

/* ---------- heart toggle w/ bounce (cm-heart keyframe) ---------- */
export function HeartButton({ liked, onToggle }: { liked: boolean; onToggle: () => void }) {
  const scale = useSharedValue(1);
  const onPress = () => {
    // 0%1 · 40%1.35 · 70%.9 · 100%1
    scale.value = withSequence(
      withTiming(1.35, { duration: 150, easing: Easing.bezier(0.34, 1.56, 0.64, 1) }),
      withTiming(0.9, { duration: 110, easing: Easing.bezier(0.4, 0, 0.2, 1) }),
      withSpring(1, spring.pop),
    );
    onToggle();
  };
  const aStyle = useAnimatedStyle(() => ({ transform: [{ scale: scale.value }] }));
  return (
    <Pressable onPress={onPress} hitSlop={6}>
      <Animated.View style={aStyle}>{liked ? <HeartFilled /> : <HeartOutline />}</Animated.View>
    </Pressable>
  );
}

/* ---------- bottom-sheet header / footer (centered title + v 접기) ---------- */
export const SheetTitle = ({ text }: { text: string }) => (
  <View style={styles.sheetTitleWrap}>
    <Text style={styles.sheetTitle}>{text}</Text>
  </View>
);

export const SheetCloseChevron = ({ onPress }: { onPress: () => void }) => (
  <Pressable onPress={onPress} hitSlop={12} style={styles.sheetClose}>
    <ChevronDownIcon />
  </Pressable>
);

const styles = StyleSheet.create({
  sheetTitleWrap: {
    marginHorizontal: -20,
    paddingVertical: 12,
    alignItems: 'center',
    borderBottomWidth: 1,
    borderBottomColor: colors.inputBorder,
  },
  sheetTitle: { fontSize: 16, fontWeight: '700', color: colors.textPrimary, fontFamily: fonts.bodyB },
  sheetClose: { alignItems: 'center', paddingTop: 14, paddingBottom: 4 },
});
