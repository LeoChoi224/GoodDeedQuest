/**
 * SCREEN 08-4 · 숏폼 생성 로딩 (route: Generating — fade in, no back).
 * Rotating render spinner + "영상을 생성하는 중입니다..." + FFmpeg 안내.
 * Auto-advances to Player after a short delay (navigation.replace).
 */
import React, { useEffect, useRef } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import Animated, { FadeIn } from 'react-native-reanimated';
import HazeBackground from '../../components/HazeBackground';
import MainHeader from '../../components/MainHeader';
import { colors, fonts } from '../../theme';
import { Spinner } from './_parts';

export default function GeneratingScreen({ navigation, route }: any) {
  const done = useRef(false);

  useEffect(() => {
    const t = setTimeout(() => {
      if (!done.current) {
        done.current = true;
        navigation.replace('Player');
      }
    }, 2400);
    return () => clearTimeout(t);
  }, [navigation]);

  return (
    <View style={styles.root}>
      <StatusBar style="light" />
      <HazeBackground />
      <MainHeader />

      <Animated.View entering={FadeIn.duration(260)} style={styles.center}>
        <Spinner />
        <Text style={styles.title}>영상을 생성하는 중입니다...</Text>
        <Text style={styles.sub}>FFmpeg으로 렌더링하고 있어요. 잠시만 기다려주세요.</Text>
      </Animated.View>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.screenBg },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 24 },
  title: { fontFamily: fonts.pixel, fontSize: 16, color: colors.primaryDark, marginTop: 20, marginBottom: 8 },
  sub: { fontSize: 12, color: '#888', textAlign: 'center', fontFamily: fonts.bodyR },
});
