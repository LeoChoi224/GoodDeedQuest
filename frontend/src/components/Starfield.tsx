/**
 * Hero starfield — twinkling stars (gdq-twinkle) + drifting particles (gdq-drift).
 * gdq-twinkle: 0/100 opacity .25 → 50 opacity 1  (withRepeat reverse)
 * gdq-drift:   rises translateY 6 → -46 with fade in/out (withRepeat)
 * All transform/opacity only, staggered by animation-delay.
 */
import React, { useEffect } from 'react';
import { View, StyleSheet, DimensionValue } from 'react-native';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withRepeat,
  withTiming,
  withDelay,
  Easing,
  interpolate,
} from 'react-native-reanimated';

const STAR_DEFS = [
  ['8%', '16%'], ['22%', '9%'], ['34%', '22%'], ['62%', '13%'], ['74%', '24%'],
  ['86%', '11%'], ['48%', '30%'], ['90%', '32%'], ['6%', '34%'],
].map((s, i) => ({
  left: s[0] as DimensionValue,
  top: s[1] as DimensionValue,
  size: i % 3 === 0 ? 4 : i % 3 === 1 ? 3 : 2,
  color: i % 2 === 0 ? '#D4A017' : '#FFFFFF',
  dur: (2.2 + (i % 4) * 0.6) * 1000,
  delay: i * 350,
}));

const PARTICLE_DEFS = Array.from({ length: 14 }, (_, i) => ({
  color: i % 2 === 0 ? '#D4A017' : '#4CAF50',
  left: (6 + ((i * 6.7) % 88)) + '%',
  bottom: 60 + ((i * 13) % 120),
  dur: (4 + (i % 5)) * 1000,
  delay: i * 500,
}));

function Star({ def }: { def: (typeof STAR_DEFS)[number] }) {
  const t = useSharedValue(0.25);
  useEffect(() => {
    t.value = withDelay(
      def.delay,
      withRepeat(withTiming(1, { duration: def.dur / 2, easing: Easing.inOut(Easing.ease) }), -1, true)
    );
  }, []);
  const style = useAnimatedStyle(() => ({ opacity: t.value }));
  return (
    <Animated.View
      style={[
        {
          position: 'absolute',
          left: def.left,
          top: def.top,
          width: def.size,
          height: def.size,
          backgroundColor: def.color,
          shadowColor: '#D4A017',
          shadowOpacity: 0.5,
          shadowRadius: 3,
        },
        style,
      ]}
    />
  );
}

function Particle({ def }: { def: (typeof PARTICLE_DEFS)[number] }) {
  const p = useSharedValue(0);
  useEffect(() => {
    p.value = withDelay(def.delay, withRepeat(withTiming(1, { duration: def.dur, easing: Easing.linear }), -1, false));
  }, []);
  const style = useAnimatedStyle(() => ({
    transform: [{ translateY: interpolate(p.value, [0, 1], [6, -46]) }],
    opacity: interpolate(p.value, [0, 0.2, 0.8, 1], [0, 0.9, 0.9, 0]),
  }));
  return (
    <Animated.View
      style={[
        {
          position: 'absolute',
          left: def.left as DimensionValue,
          bottom: def.bottom,
          width: 4,
          height: 4,
          backgroundColor: def.color,
        },
        style,
      ]}
    />
  );
}

export default function Starfield() {
  return (
    <View style={StyleSheet.absoluteFill} pointerEvents="none">
      {STAR_DEFS.map((d, i) => (
        <Star key={`s${i}`} def={d} />
      ))}
      {PARTICLE_DEFS.map((d, i) => (
        <Particle key={`p${i}`} def={d} />
      ))}
    </View>
  );
}
