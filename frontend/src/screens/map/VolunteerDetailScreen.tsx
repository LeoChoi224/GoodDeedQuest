/**
 * SCREEN 05·9 · 봉사활동 상세정보.
 * 센터 위치 지도(180px) + 상세 정보 카드(label 골드 + value) + sticky 신청하기(글로우 펄스).
 * 신청하기 → 외부 VMS 연동(데모: Toast).
 */
import React, { useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, Pressable } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { LinearGradient } from 'expo-linear-gradient';
import Svg, { Line } from 'react-native-svg';
import Animated, { useSharedValue, useAnimatedStyle, withRepeat, withTiming, interpolate, Easing } from 'react-native-reanimated';
import { colors, fonts, radii } from '../../theme';
import HazeBackground from '../../components/HazeBackground';
import MainHeader from '../../components/MainHeader';
import { useToast } from '../../components/Toast';
import { MapPinIcon, MAP } from './_parts';

function DetailGrid() {
  return (
    <Svg style={StyleSheet.absoluteFill} width="100%" height="100%" viewBox="0 0 300 180" preserveAspectRatio="none">
      {Array.from({ length: 10 }).map((_, i) => (
        <Line key={`v${i}`} x1={i * 34} y1={0} x2={i * 34} y2={180} stroke={MAP.grid} strokeWidth={0.6} />
      ))}
      {Array.from({ length: 6 }).map((_, i) => (
        <Line key={`h${i}`} x1={0} y1={i * 34} x2={300} y2={i * 34} stroke={MAP.grid} strokeWidth={0.6} />
      ))}
    </Svg>
  );
}

export default function VolunteerDetailScreen({ navigation, route }: any) {
  const toast = useToast();
  const item = route?.params?.item;
  const place = item?.name ?? '경기 안양시 수리 장애인 복지관';

  const rows = [
    { label: '활동기간', value: '2026.07.15 ~ 08.30' },
    { label: '봉사장소', value: place },
    { label: '봉사대상', value: '지역 장애인 아동' },
    { label: '자격요건', value: '만 19세 이상' },
    { label: '활동설명', value: '장애/비장애인 형제지원 프로그램 보조 봉사' },
  ];

  // sticky 신청하기 글로우 펄스 (design mp-applyglow)
  const g = useSharedValue(0);
  useEffect(() => {
    g.value = withRepeat(withTiming(1, { duration: 1200, easing: Easing.inOut(Easing.ease) }), -1, true);
  }, []);
  const glow = useAnimatedStyle(() => ({
    opacity: interpolate(g.value, [0, 1], [0.3, 0.7]),
    transform: [{ scale: interpolate(g.value, [0, 1], [1, 1.05]) }],
  }));

  return (
    <View style={styles.root}>
      <StatusBar style="light" />
      <HazeBackground />
      <MainHeader showBack title="봉사활동 상세" />

      <ScrollView contentContainerStyle={styles.body} showsVerticalScrollIndicator={false}>
        {/* 센터 위치 지도 */}
        <View style={styles.mapBox}>
          <LinearGradient colors={[MAP.canvasA, MAP.canvasB]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={StyleSheet.absoluteFill} />
          <DetailGrid />
          <View style={styles.pinCenter}>
            <MapPinIcon size={40} />
          </View>
        </View>

        {/* 상세 정보 카드 */}
        <View style={styles.card}>
          {rows.map((r, i) => (
            <View key={r.label} style={[styles.row, i === rows.length - 1 && { borderBottomWidth: 0 }]}>
              <Text style={styles.label}>{r.label}</Text>
              <Text style={styles.value}>{r.value}</Text>
            </View>
          ))}
        </View>
      </ScrollView>

      {/* sticky 신청하기 */}
      <LinearGradient colors={['rgba(238,246,240,0)', colors.screenBg]} locations={[0, 0.4]} style={styles.footer}>
        <View>
          <Animated.View style={[styles.glow, glow]} pointerEvents="none" />
          <Pressable
            android_ripple={undefined}
            onPress={() => toast.show('봉사 신청 페이지로 이동합니다')}
            style={({ pressed }) => [styles.applyBtn, pressed && { transform: [{ scale: 0.97 }] }]}
          >
            <Text style={styles.applyText}>신청하기</Text>
          </Pressable>
        </View>
      </LinearGradient>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.screenBg },
  body: { padding: 16, paddingBottom: 96 },
  mapBox: {
    height: 180,
    borderRadius: radii.chip,
    overflow: 'hidden',
    borderWidth: 1.5,
    borderColor: colors.pixelBorder,
    marginBottom: 16,
  },
  pinCenter: { position: 'absolute', left: '50%', top: '44%', marginLeft: -20, marginTop: -20 },
  card: {
    backgroundColor: colors.parchment,
    borderWidth: 1.5,
    borderColor: colors.pixelBorder,
    borderRadius: radii.chip,
    paddingHorizontal: 16,
    paddingVertical: 4,
  },
  row: { flexDirection: 'row', gap: 12, paddingVertical: 9, borderBottomWidth: 1, borderBottomColor: '#EFE6CC' },
  label: { width: 64, fontFamily: fonts.pixel, fontSize: 13, color: colors.gold },
  value: { flex: 1, fontSize: 14, color: colors.primaryDark, lineHeight: 21, fontFamily: fonts.bodyR },
  footer: { position: 'absolute', bottom: 0, left: 0, right: 0, paddingHorizontal: 16, paddingTop: 16, paddingBottom: 12 },
  glow: {
    position: 'absolute',
    top: -7,
    left: -7,
    right: -7,
    bottom: -7,
    borderRadius: 12,
    backgroundColor: colors.gold,
  },
  applyBtn: {
    height: 52,
    borderRadius: 8,
    backgroundColor: colors.gold,
    alignItems: 'center',
    justifyContent: 'center',
  },
  applyText: { fontFamily: fonts.pixel, fontSize: 18, color: colors.primaryDark },
});
