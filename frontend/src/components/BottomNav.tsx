/**
 * COMPONENT B — Bottom Nav (custom tabBar). Height 83, bg #033236, top border
 * #5C3D1E 2px. Tabs: 커뮤니티 | 지도 | 홈 | 상점 | 마이페이지. Active: gold #D4A017 +
 * highlight tile behind the icon (spring). Inactive: white 60%.
 */
import React, { useEffect } from 'react'; // ⭐ 수정: useEffect 추가
import { View, Text, Image, Pressable, StyleSheet } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import type { BottomTabBarProps } from '@react-navigation/bottom-tabs';
import Animated, { useAnimatedStyle, useSharedValue, withSpring, withTiming } from 'react-native-reanimated';
import { bottomNav, fonts, NAV_ICONS, spring } from '../theme';

const TABS: Record<string, { label: string; icon: keyof typeof NAV_ICONS }> = {
  Community: { label: '커뮤니티', icon: 'community' },
  Map: { label: '지도', icon: 'map' },
  Home: { label: '홈', icon: 'home' },
  Shop: { label: '상점', icon: 'shop' },
  My: { label: '마이페이지', icon: 'my' },
};

function TabButton({
  routeName,
  focused,
  onPress,
}: {
  routeName: string;
  focused: boolean;
  onPress: () => void;
}) {
  const meta = TABS[routeName];
  const tile = useSharedValue(focused ? 1 : 0);
  const press = useSharedValue(1);
  // ⭐ 수정: 렌더 중에 shared value를 직접 write하고 있었음(Reanimated strict-mode 경고
  // "Writing to `value` during component render") — focused가 바뀔 때만 useEffect에서 반영
  useEffect(() => {
    tile.value = withSpring(focused ? 1 : 0, spring.pop);
  }, [focused]);

  const tileStyle = useAnimatedStyle(() => ({
    opacity: tile.value,
    transform: [{ scale: 0.7 + tile.value * 0.3 }],
  }));
  const iconStyle = useAnimatedStyle(() => ({ transform: [{ scale: press.value }] }));

  return (
    <Pressable
      style={styles.tab}
      onPress={onPress}
      onPressIn={() => (press.value = withTiming(0.9, { duration: 100 }))}
      onPressOut={() => (press.value = withSpring(1, spring.press))}
    >
      <Animated.View style={[styles.iconWrap, iconStyle]}>
        <Animated.View style={[styles.tile, tileStyle]} />
        <Image
          source={NAV_ICONS[meta.icon]}
          style={[styles.icon, { opacity: focused ? 1 : 0.6 }]}
        />
      </Animated.View>
      <Text style={[styles.label, { color: focused ? bottomNav.active : bottomNav.inactive }]}>
        {meta.label}
      </Text>
    </Pressable>
  );
}

export default function BottomNav({ state, navigation }: BottomTabBarProps) {
  const insets = useSafeAreaInsets();
  return (
    <View style={[styles.bar, { paddingBottom: insets.bottom, height: bottomNav.height + insets.bottom }]}>
      {state.routes.map((route, i) => {
        const focused = state.index === i;
        const onPress = () => {
          const event = navigation.emit({ type: 'tabPress', target: route.key, canPreventDefault: true });
          if (!focused && !event.defaultPrevented) navigation.navigate(route.name);
        };
        return <TabButton key={route.key} routeName={route.name} focused={focused} onPress={onPress} />;
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  bar: {
    flexDirection: 'row',
    backgroundColor: bottomNav.bg,
    borderTopWidth: 2,
    borderTopColor: bottomNav.topBorder,
    paddingTop: 10,
  },
  tab: { flex: 1, alignItems: 'center', gap: 4 },
  iconWrap: { width: 44, height: 34, alignItems: 'center', justifyContent: 'center' },
  tile: {
    position: 'absolute',
    width: 44,
    height: 34,
    borderRadius: 11,
    backgroundColor: 'rgba(212,160,23,0.18)',
    borderWidth: 1,
    borderColor: 'rgba(212,160,23,0.5)',
  },
  icon: { width: 26, height: 26 },
  label: { fontSize: 10, fontFamily: fonts.bodyM },
});
