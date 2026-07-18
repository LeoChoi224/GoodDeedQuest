/**
 * Spring press button — interaction gallery #3 (ig-spring) + login flow gdq-btn.
 * gdq-btn: transition transform 120ms cubic-bezier(.4,0,.2,1); :active scale(.96)
 * We press down with withTiming(0.95) and release with an overshoot withSpring.
 * Supports a disabled state whose background can animate (gray → teal) via `bgColor`.
 */
import React from 'react';
import { Pressable, StyleProp, ViewStyle, PressableProps } from 'react-native';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withTiming,
  withSpring,
  Easing,
  interpolateColor,
  useDerivedValue,
} from 'react-native-reanimated';
import { spring } from '../theme';

// Animate the Pressable itself so caller layout styles (flex:1, width, margins)
// apply to the touchable — side-by-side buttons then split evenly in a row.
const AnimatedPressable = Animated.createAnimatedComponent(Pressable);

type Props = {
  onPress?: () => void;
  disabled?: boolean;
  style?: StyleProp<ViewStyle>;
  /** [offColor, onColor] to cross-fade the background driven by `active`. */
  bgColors?: [string, string];
  active?: boolean;
  children: React.ReactNode;
  pressScale?: number;
  hitSlop?: PressableProps['hitSlop'];
};

export default function SpringButton({
  onPress,
  disabled,
  style,
  bgColors,
  active = true,
  children,
  pressScale = 0.95,
  hitSlop,
}: Props) {
  const scale = useSharedValue(1);
  // animated 0→1 progress for the (optional) background cross-fade
  const prog = useDerivedValue(() =>
    withTiming(active ? 1 : 0, { duration: 200, easing: Easing.bezier(0.4, 0, 0.2, 1) })
  );

  const animStyle = useAnimatedStyle(() => {
    const base: any = { transform: [{ scale: scale.value }] };
    if (bgColors) {
      base.backgroundColor = interpolateColor(prog.value, [0, 1], bgColors);
    }
    return base;
  });

  return (
    <AnimatedPressable
      onPress={onPress}
      disabled={disabled}
      hitSlop={hitSlop}
      onPressIn={() => {
        scale.value = withTiming(pressScale, { duration: 120, easing: Easing.bezier(0.4, 0, 0.2, 1) });
      }}
      onPressOut={() => {
        scale.value = withSpring(1, spring.press);
      }}
      style={[style, animStyle]}
    >
      {children}
    </AnimatedPressable>
  );
}
