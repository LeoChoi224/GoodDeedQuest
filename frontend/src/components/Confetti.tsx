/**
 * Celebration confetti — ported from 01_login_flow.dc.html screen 5 (gdq-burst).
 * 12 pieces radiate from the app-icon center, drift down, fade, loop — infinite.
 * gdq-burst: scale 0→1 out to (dx,dy), then +16px & fade, opacity ramp 12%→80%.
 */
import React, { useEffect } from 'react';
import { View, StyleSheet } from 'react-native';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withRepeat,
  withDelay,
  withTiming,
  Easing,
  interpolate,
} from 'react-native-reanimated';

const CC = ['#D4A017', '#4CAF50', '#FFFFFF'];
const POS: [number, number][] = [
  [-90, -70], [-110, 10], [-70, 90], [10, -110], [90, -80], [120, 0],
  [100, 90], [-20, 110], [60, 110], [-130, -20], [130, -50], [40, -120],
];

const PIECES = POS.map((p, i) => ({
  dx: p[0],
  dy: p[1],
  size: i % 3 === 0 ? 8 : 6,
  color: CC[i % 3],
  dur: (1.9 + (i % 4) * 0.25) * 1000,
  delay: (0.4 + i * 0.1) * 1000,
}));

function Piece({ def }: { def: (typeof PIECES)[number] }) {
  const p = useSharedValue(0);
  useEffect(() => {
    p.value = withDelay(
      def.delay,
      withRepeat(withTiming(1, { duration: def.dur, easing: Easing.out(Easing.ease) }), -1, false)
    );
  }, []);

  const style = useAnimatedStyle(() => {
    const tx = interpolate(p.value, [0, 0.55, 1], [0, def.dx, def.dx]);
    const ty = interpolate(p.value, [0, 0.55, 1], [0, def.dy, def.dy + 16]);
    const scale = interpolate(p.value, [0, 0.55, 1], [0, 1, 0.85]);
    const opacity = interpolate(p.value, [0, 0.12, 0.8, 1], [0, 1, 1, 0]);
    return { opacity, transform: [{ translateX: tx }, { translateY: ty }, { scale }] };
  });

  return (
    <Animated.View
      style={[
        { position: 'absolute', width: def.size, height: def.size, backgroundColor: def.color },
        style,
      ]}
    />
  );
}

export default function Confetti() {
  // absoluteFill → centered anchor (0-size) → pieces burst from the icon center.
  return (
    <View style={[StyleSheet.absoluteFill, styles.center]} pointerEvents="none">
      <View>
        {PIECES.map((def, i) => (
          <Piece key={i} def={def} />
        ))}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  center: { alignItems: 'center', justifyContent: 'center' },
});
