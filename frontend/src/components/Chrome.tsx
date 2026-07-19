/**
 * Shared chrome: the in-frame status bar row and the white app header used on
 * signup screens (COMPONENT A pattern — app icon + "선행퀘스트", optional back ←).
 */
import React from 'react';
import { View, Text, Image, StyleSheet, Pressable } from 'react-native';
import { StatusGlyphs, BatteryGlyph, ChevronLeft } from './PixelIcons';
import { colors, fonts, brand, shadow } from '../theme';

export function StatusBarRow({ dark = true }: { dark?: boolean }) {
  const color = dark ? colors.textPrimary : colors.white;
  return (
    <View style={styles.statusRow}>
      <Text style={[styles.statusTime, { color }]}>9:41</Text>
      <View style={styles.statusIcons}>
        <StatusGlyphs color={color} />
        <BatteryGlyph color={color} />
      </View>
    </View>
  );
}

export function AppHeader({ onBack }: { onBack?: () => void }) {
  return (
    <View style={styles.header}>
      {onBack ? (
        <Pressable style={styles.back} onPress={onBack} hitSlop={10}>
          <ChevronLeft size={24} color={colors.textPrimary} />
        </Pressable>
      ) : null}
      <View style={styles.brandRow}>
        <Image source={brand.appIcon} style={styles.brandIcon} />
        <Text style={styles.brandText}>선행퀘스트</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  statusRow: {
    height: 54,
    paddingTop: 14,
    paddingHorizontal: 28,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    zIndex: 20,
  },
  statusTime: { fontSize: 15, fontWeight: '600', fontFamily: fonts.bodyB },
  statusIcons: { flexDirection: 'row', gap: 6, alignItems: 'center' },
  header: {
    height: 56,
    backgroundColor: colors.white,
    borderBottomWidth: 1,
    borderBottomColor: colors.hairline,
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 20,
    ...shadow.header,
  },
  back: { position: 'absolute', left: 14, zIndex: 3, padding: 4 },
  brandRow: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  brandIcon: { width: 30, height: 30, borderRadius: 7 },
  brandText: { fontFamily: fonts.pixel, fontSize: 16, color: colors.primaryDark },
});
