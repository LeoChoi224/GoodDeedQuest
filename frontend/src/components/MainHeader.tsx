/**
 * COMPONENT A — Header (모든 메인 화면 공통). Height 56, bg #033236.
 * Left: app icon + "선행퀘스트" (DotGothic16 16, #FFF8E7). Right: hamburger ≡ (white).
 * Back-needed screens: ← left of the logo. Hamburger opens the right drawer.
 */
import React from 'react';
import { View, Text, Image, StyleSheet, Pressable } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useNavigation, DrawerActions } from '@react-navigation/native';
import { HamburgerIcon, ChevronLeft } from './PixelIcons';
import { colors, fonts, brand } from '../theme';

export default function MainHeader({
  showBack = false,
  onBack,
  title = '선행퀘스트',
  right,
}: {
  showBack?: boolean;
  onBack?: () => void;
  title?: string;
  right?: React.ReactNode;
}) {
  const insets = useSafeAreaInsets();
  const navigation = useNavigation<any>();

  return (
    <View style={{ paddingTop: insets.top, backgroundColor: colors.primaryDark }}>
      <View style={styles.bar}>
        <View style={styles.left}>
          {showBack ? (
            // 서브 화면: 뒤로가기 + 타이틀만 (앱 아이콘 생략)
            <Pressable onPress={onBack ?? (() => navigation.goBack())} hitSlop={10} style={styles.backBtn}>
              <ChevronLeft size={22} color={colors.white} />
            </Pressable>
          ) : (
            // 탭 루트: 앱 아이콘 + 브랜드
            <Image source={brand.appIcon} style={styles.icon} />
          )}
          <Text style={styles.title}>{title}</Text>
        </View>
        <View style={styles.right}>
          {right}
          <Pressable
            onPress={() => navigation.dispatch(DrawerActions.openDrawer())}
            hitSlop={10}
            style={styles.menuBtn}
          >
            <HamburgerIcon size={24} color={colors.white} />
          </Pressable>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  bar: {
    height: 56,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    // 2px brown pixel edge — mirrors the bottom nav's top border so every screen's
    // content is framed consistently (단차 통일, RPG "window" 느낌).
    borderBottomWidth: 2,
    borderBottomColor: colors.pixelBorder,
  },
  left: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  backBtn: { marginRight: 2 },
  icon: { width: 28, height: 28, borderRadius: 7 },
  title: { fontFamily: fonts.pixel, fontSize: 16, color: colors.parchment },
  right: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  menuBtn: { padding: 2 },
});
