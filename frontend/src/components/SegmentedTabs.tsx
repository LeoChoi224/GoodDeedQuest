/**
 * Segmented tab switcher with a sliding gold pill indicator (spring). Used by shop
 * (아이템/칭호), mypage (레벨/랭킹전), map (시군구/상세), etc.
 */
import React from 'react';
import { View, Text, Pressable, StyleSheet, LayoutChangeEvent } from 'react-native';
import Animated, { useAnimatedStyle, useSharedValue, withSpring } from 'react-native-reanimated';
import { colors, fonts, radii, spring } from '../theme';

export default function SegmentedTabs({
  tabs,
  index,
  onChange,
}: {
  tabs: string[];
  index: number;
  onChange: (i: number) => void;
}) {
  const w = useSharedValue(0);
  const x = useSharedValue(0);

  const onLayout = (e: LayoutChangeEvent) => {
    const total = e.nativeEvent.layout.width - 8; // minus padding
    w.value = total / tabs.length;
    x.value = withSpring(4 + index * (total / tabs.length), spring.press);
  };

  React.useEffect(() => {
    if (w.value) x.value = withSpring(4 + index * w.value, spring.press);
  }, [index]);

  const pill = useAnimatedStyle(() => ({ width: w.value, transform: [{ translateX: x.value }] }));

  return (
    <View style={styles.wrap} onLayout={onLayout}>
      <Animated.View style={[styles.pill, pill]} />
      {tabs.map((t, i) => (
        <Pressable key={t} style={styles.tab} onPress={() => onChange(i)}>
          <Text style={[styles.label, { color: i === index ? '#3A2A08' : colors.textSecondary }]}>{t}</Text>
        </Pressable>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    flexDirection: 'row',
    backgroundColor: '#EAF1EC',
    borderRadius: radii.pill,
    padding: 4,
    height: 44,
  },
  pill: {
    position: 'absolute',
    top: 4,
    bottom: 4,
    borderRadius: radii.pill,
    backgroundColor: colors.gold,
  },
  tab: { flex: 1, alignItems: 'center', justifyContent: 'center', zIndex: 1 },
  label: { fontSize: 14, fontWeight: '700', fontFamily: fonts.bodyB },
});
