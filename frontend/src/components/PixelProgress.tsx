/**
 * Pixel/XP progress bar with animated fill (withTiming, ease-out) — quest progress,
 * level EXP bar. Gold or XP-green fill on a soft track.
 */
import React, { useEffect } from 'react';
import { View, StyleSheet } from 'react-native';
import Animated, { useAnimatedStyle, useSharedValue, withTiming, Easing } from 'react-native-reanimated';
import { colors } from '../theme';

export default function PixelProgress({
  progress, // 0..1
  height = 14,
  color = colors.xpGreen,
  track = '#E7EFE8',
}: {
  progress: number;
  height?: number;
  color?: string;
  track?: string;
}) {
  const p = useSharedValue(0);
  useEffect(() => {
    p.value = withTiming(Math.max(0, Math.min(1, progress)), { duration: 800, easing: Easing.out(Easing.cubic) });
  }, [progress]);
  const fill = useAnimatedStyle(() => ({ width: `${p.value * 100}%` }));
  return (
    <View style={[styles.track, { height, borderRadius: height / 2, backgroundColor: track }]}>
      <Animated.View style={[styles.fill, { borderRadius: height / 2, backgroundColor: color }, fill]} />
    </View>
  );
}

const styles = StyleSheet.create({
  track: { width: '100%', overflow: 'hidden' },
  fill: { height: '100%' },
});
