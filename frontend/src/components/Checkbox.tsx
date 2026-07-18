/**
 * Checkbox — 22x22, radius 6. Off: white w/ #D1D5DB border. On: #033236 filled + check.
 * Toggling pops the box (withSpring overshoot) and the checkmark scales in.
 */
import React, { useEffect } from 'react';
import { Pressable } from 'react-native';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withSpring,
  withTiming,
} from 'react-native-reanimated';
import { CheckMark } from './PixelIcons';
import { colors, spring } from '../theme';

export default function Checkbox({
  checked,
  onToggle,
  size = 22,
}: {
  checked: boolean;
  onToggle?: () => void;
  size?: number;
}) {
  const pop = useSharedValue(1);
  const mark = useSharedValue(checked ? 1 : 0);

  useEffect(() => {
    mark.value = withTiming(checked ? 1 : 0, { duration: 140 });
    pop.value = 0.8;
    pop.value = withSpring(1, spring.pop);
  }, [checked]);

  const boxStyle = useAnimatedStyle(() => ({ transform: [{ scale: pop.value }] }));
  const markStyle = useAnimatedStyle(() => ({ transform: [{ scale: mark.value }], opacity: mark.value }));

  return (
    <Pressable onPress={onToggle} hitSlop={8}>
      <Animated.View
        style={[
          {
            width: size,
            height: size,
            borderRadius: 6,
            alignItems: 'center',
            justifyContent: 'center',
            backgroundColor: checked ? colors.primaryDark : colors.white,
            borderWidth: checked ? 0 : 1,
            borderColor: '#D1D5DB',
          },
          boxStyle,
        ]}
      >
        <Animated.View style={markStyle}>
          <CheckMark size={size * 0.6} color="#fff" />
        </Animated.View>
      </Animated.View>
    </Pressable>
  );
}
