/**
 * Shimmer skeleton — interaction gallery #15 (ig-shim2). A moving highlight sweeps
 * across a placeholder block. Compose several <Shimmer/> for list/card skeletons.
 */
import React, { useEffect } from 'react';
import { View, StyleSheet, DimensionValue } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Animated, { useAnimatedStyle, useSharedValue, withRepeat, withTiming, Easing, interpolate } from 'react-native-reanimated';

export default function Shimmer({
  width = '100%',
  height = 12,
  radius = 6,
  style,
}: {
  width?: DimensionValue;
  height?: number;
  radius?: number;
  style?: any;
}) {
  const p = useSharedValue(0);
  useEffect(() => {
    p.value = withRepeat(withTiming(1, { duration: 1100, easing: Easing.linear }), -1, false);
  }, []);
  const sweep = useAnimatedStyle(() => ({
    transform: [{ translateX: interpolate(p.value, [0, 1], [-160, 160]) }],
  }));
  return (
    <View style={[{ width, height, borderRadius: radius, backgroundColor: '#E5E7EB', overflow: 'hidden' }, style]}>
      <Animated.View style={[StyleSheet.absoluteFill, sweep]}>
        <LinearGradient
          colors={['#E5E7EB', '#F3F4F6', '#E5E7EB']}
          start={{ x: 0, y: 0.5 }}
          end={{ x: 1, y: 0.5 }}
          style={StyleSheet.absoluteFill}
        />
      </Animated.View>
    </View>
  );
}
