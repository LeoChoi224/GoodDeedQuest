/**
 * SCREEN 1 · 관리자 대시보드 — route "Dashboard" (STACK ROOT reached from drawer;
 * MainHeader without back, hamburger present). Alert banner (megaphone + gold glow
 * pulse) · 오늘의 요약 2×2 stat cards (stagger count-up) · 활동 추이 7-day line chart
 * (svg draw + point pop). Pinned footer: 유저 관리 → UserList, 신고 / 검토 → ReportList.
 */
import React from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { LinearGradient } from 'expo-linear-gradient';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Animated, { FadeInDown } from 'react-native-reanimated';
import { colors, fonts, radii, shadow } from '../../theme';
import HazeBackground from '../../components/HazeBackground';
import MainHeader from '../../components/MainHeader';
import SpringButton from '../../components/SpringButton';
import { AD, MegaphoneIcon, BannerGlow, CountUp, ActivityChart } from './_parts';

const SUMMARY: { label: string; value: number; display: string; delta: string; deltaColor: string }[] = [
  { label: '전체 사용자', value: 1248, display: '1,248', delta: '+80', deltaColor: colors.xpGreen },
  { label: '활동한 사용자', value: 342, display: '342', delta: '+27', deltaColor: colors.xpGreen },
  { label: '완료한 퀘스트', value: 592, display: '592', delta: '+45', deltaColor: colors.xpGreen },
  { label: '신고 / 검토 건', value: 12, display: '12', delta: '-3', deltaColor: AD.red },
];

export default function DashboardScreen({ navigation }: any) {
  const insets = useSafeAreaInsets();

  return (
    <View style={styles.root}>
      <StatusBar style="dark" />
      <HazeBackground />
      <MainHeader />

      <ScrollView
        contentContainerStyle={[styles.body, { paddingBottom: insets.bottom + 96 }]}
        showsVerticalScrollIndicator={false}
      >
        {/* 주요 알림 배너 (골드 글로우 펄스) */}
        <Animated.View entering={FadeInDown.duration(420)} style={styles.banner}>
          <BannerGlow />
          <MegaphoneIcon />
          <Text style={styles.bannerText}>
            <Text style={styles.bannerBold}>주요 알림 : </Text>금일 신고 12건 검토 대기중
          </Text>
        </Animated.View>

        {/* 오늘의 요약 */}
        <View style={styles.summaryHead}>
          <Text style={styles.sectionTitle}>오늘의 요약</Text>
          <Text style={styles.dateText}>2026.07.11 (금)</Text>
        </View>

        <View style={styles.grid}>
          {SUMMARY.map((s, i) => (
            <Animated.View key={s.label} entering={FadeInDown.delay(50 + i * 80).duration(500)} style={styles.statCard}>
              <Text style={styles.statLabel}>{s.label}</Text>
              <View style={styles.statRow}>
                <CountUp target={s.value} delay={50 + i * 80} style={styles.statValue} />
                <Text style={[styles.statDelta, { color: s.deltaColor }]}>{s.delta}</Text>
              </View>
            </Animated.View>
          ))}
        </View>

        {/* 활동 추이 (최근 7일) */}
        <Text style={[styles.sectionTitle, { marginBottom: 10 }]}>활동 추이 (최근 7일)</Text>
        <View style={styles.chartCard}>
          <ActivityChart />
        </View>
      </ScrollView>

      {/* pinned footer */}
      <LinearGradient
        colors={['rgba(238,246,240,0)', colors.screenBg]}
        locations={[0, 0.4]}
        style={[styles.footer, { paddingBottom: insets.bottom + 20 }]}
      >
        <SpringButton style={[styles.footerBtn, styles.usersBtn]} onPress={() => navigation.navigate('UserList')}>
          <Text style={styles.usersBtnText}>유저 관리</Text>
        </SpringButton>
        <SpringButton style={[styles.footerBtn, styles.reportsBtn]} onPress={() => navigation.navigate('ReportList')}>
          <Text style={styles.reportsBtnText}>신고 / 검토</Text>
        </SpringButton>
      </LinearGradient>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.screenBg },
  body: { padding: 16 },
  banner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: colors.parchment,
    borderWidth: 1.5,
    borderColor: colors.gold,
    borderRadius: 8,
    paddingVertical: 10,
    paddingHorizontal: 14,
    marginBottom: 16,
    overflow: 'hidden',
  },
  bannerText: { flex: 1, fontSize: 14, color: colors.primaryDark, fontFamily: fonts.bodyR },
  bannerBold: { fontFamily: fonts.bodyB, fontWeight: '700' },
  summaryHead: { flexDirection: 'row', alignItems: 'flex-end', justifyContent: 'space-between', marginBottom: 12 },
  sectionTitle: { fontFamily: fonts.pixel, fontSize: 16, color: colors.primaryDark },
  dateText: { fontSize: 12, color: AD.muted, fontFamily: fonts.bodyR },
  grid: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between', rowGap: 10, marginBottom: 20 },
  statCard: {
    width: '48.5%',
    backgroundColor: colors.white,
    borderWidth: 1,
    borderColor: AD.cardBorder,
    borderRadius: 12,
    padding: 14,
    ...shadow.card,
    shadowOpacity: 0.05,
  },
  statLabel: { fontSize: 12, color: AD.muted, marginBottom: 6, fontFamily: fonts.bodyR },
  statRow: { flexDirection: 'row', alignItems: 'baseline', gap: 8 },
  statValue: { fontSize: 22, fontWeight: '700', color: colors.primaryDark, fontFamily: fonts.bodyB },
  statDelta: { fontSize: 13, fontWeight: '700', fontFamily: fonts.bodyB },
  chartCard: {
    backgroundColor: colors.white,
    borderRadius: 12,
    padding: 12,
    ...shadow.card,
    shadowOpacity: 0.05,
  },
  footer: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    flexDirection: 'row',
    gap: 10,
    paddingHorizontal: 16,
    paddingTop: 12,
  },
  footerBtn: { flex: 1, height: 50, borderRadius: 8, alignItems: 'center', justifyContent: 'center' },
  usersBtn: { backgroundColor: colors.primaryDark },
  usersBtnText: { color: colors.parchment, fontFamily: fonts.pixel, fontSize: 17 },
  reportsBtn: { backgroundColor: AD.red },
  reportsBtnText: { color: colors.white, fontFamily: fonts.pixel, fontSize: 17 },
});
