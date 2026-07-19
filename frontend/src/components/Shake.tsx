/**
 * Error Shake — interaction gallery #17 (ig-shake).
 * keyframe: 0/100 x0 · 15 -9 · 30 +8 · 45 -6 · 60 +5 · 75 -3 (translateX only)
 * Re-fires whenever `trigger` (a monotonically increasing number) changes.
 */
import React, { useEffect } from 'react';
import { StyleProp, ViewStyle } from 'react-native';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withSequence,
  withTiming,
  Easing,
} from 'react-native-reanimated';

export default function Shake({
  trigger,
  children,
  style,
}: {
  trigger: number;
  children: React.ReactNode;
  style?: StyleProp<ViewStyle>;
}) {
  const x = useSharedValue(0);

  useEffect(() => {
    if (trigger === 0) return; // don't shake on first mount
    const t = (v: number) => withTiming(v, { duration: 75, easing: Easing.linear });
    x.value = withSequence(t(-9), t(8), t(-6), t(5), t(-3), t(0));
  }, [trigger]);

  const aStyle = useAnimatedStyle(() => ({ transform: [{ translateX: x.value }] }));

  return <Animated.View style={[style, aStyle]}>{children}</Animated.View>;
}
