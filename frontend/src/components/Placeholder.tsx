/**
 * Temporary placeholder screen — replaced by each flow agent's real implementation.
 * Kept minimal so the app compiles & runs while flows are being built.
 */
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import HazeBackground from './HazeBackground';
import MainHeader from './MainHeader';
import { colors, fonts } from '../theme';

export default function Placeholder({ name, back }: { name: string; back?: boolean }) {
  return (
    <View style={styles.root}>
      <HazeBackground />
      <MainHeader showBack={back} />
      <View style={styles.center}>
        <Text style={styles.title}>{name}</Text>
        <Text style={styles.sub}>구현 예정 화면</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.screenBg },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 8 },
  title: { fontFamily: fonts.pixel, fontSize: 22, color: colors.primaryDark },
  sub: { fontSize: 13, color: colors.textSecondary, fontFamily: fonts.bodyR },
});
