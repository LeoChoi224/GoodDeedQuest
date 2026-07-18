/**
 * Text input matching .gdq-input: 50px tall, radius 12, 1px #E5E7EB border.
 * On focus the border animates to #033236 with a soft ring (box-shadow 0 0 0 3px rgba(3,50,54,.10)).
 * Optional left icon and right accessory (e.g. eye toggle). transform/opacity + border only.
 */
import React, { useState } from 'react';
import { View, TextInput, TextInputProps, StyleSheet, Pressable } from 'react-native';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withTiming,
  interpolateColor,
  Easing,
} from 'react-native-reanimated';
import { colors, radii, fonts } from '../theme';

const AView = Animated.View;

type Props = TextInputProps & {
  leftIcon?: React.ReactNode;
  rightAccessory?: React.ReactNode;
  onRightPress?: () => void;
};

export default function GdqInput({ leftIcon, rightAccessory, onRightPress, style, ...rest }: Props) {
  const [focused, setFocused] = useState(false);
  const f = useSharedValue(0);

  const wrapStyle = useAnimatedStyle(() => ({
    borderColor: interpolateColor(f.value, [0, 1], [colors.inputBorder, colors.primaryDark]),
    // emulate the focus ring with an animated shadow
    shadowColor: colors.primaryDark,
    shadowOpacity: f.value * 0.1,
    shadowRadius: 3 * f.value + 0.01,
    shadowOffset: { width: 0, height: 0 },
    elevation: focused ? 2 : 0,
  }));

  return (
    <AView style={[styles.wrap, wrapStyle]}>
      {leftIcon ? <View style={styles.left}>{leftIcon}</View> : null}
      <TextInput
        {...rest}
        placeholderTextColor={colors.textMuted}
        onFocus={(e) => {
          setFocused(true);
          f.value = withTiming(1, { duration: 140, easing: Easing.bezier(0.4, 0, 0.2, 1) });
          rest.onFocus?.(e);
        }}
        onBlur={(e) => {
          setFocused(false);
          f.value = withTiming(0, { duration: 140, easing: Easing.bezier(0.4, 0, 0.2, 1) });
          rest.onBlur?.(e);
        }}
        style={[
          styles.input,
          { paddingLeft: leftIcon ? 44 : 14, paddingRight: rightAccessory ? 44 : 14 },
          style,
        ]}
      />
      {rightAccessory ? (
        <Pressable style={styles.right} onPress={onRightPress} hitSlop={8}>
          {rightAccessory}
        </Pressable>
      ) : null}
    </AView>
  );
}

const styles = StyleSheet.create({
  wrap: {
    position: 'relative',
    height: 50,
    borderWidth: 1,
    borderRadius: radii.input,
    backgroundColor: colors.white,
    justifyContent: 'center',
  },
  input: {
    height: 50,
    fontSize: 15,
    color: colors.textPrimary,
    fontFamily: fonts.bodyR,
  },
  left: { position: 'absolute', left: 14, zIndex: 2 },
  right: { position: 'absolute', right: 14, zIndex: 2, height: 50, justifyContent: 'center' },
});
