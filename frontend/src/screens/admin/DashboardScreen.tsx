import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { LinearGradient } from 'expo-linear-gradient';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Animated, { FadeInDown } from 'react-native-reanimated';
import Svg, { Circle, Line, Path, Text as SvgText } from 'react-native-svg';
import { colors, fonts, shadow } from '../../theme';
import HazeBackground from '../../components/HazeBackground';
import MainHeader from '../../components/MainHeader';
import SpringButton from '../../components/SpringButton';
import { AD, BannerGlow, CountUp, MegaphoneIcon, SkeletonCard } from './_parts';
import { adminApi, AdminActivityTrend, AdminDashboardAlert, AdminDashboardSummary, getAdminErrorMessage } from './adminApi';

const EMPTY_SUMMARY: AdminDashboardSummary = {
  total_user_count: 0,
  active_user_count: 0,
  inactive_user_count: 0,
  today_access_user_count: 0,
  pending_report_count: 0,
};

function ActivityTrendChart({ data }: { data: AdminActivityTrend[] }) {
  const width = 340, height = 190, left = 34, right = 12, top = 14, bottom = 28;
  const values = data.length ? data.map((item) => item.user_count) : [0, 0, 0, 0, 0, 0, 0];
  const labels = data.length
    ? data.map((item) => {
        const date = new Date(`${item.access_date}T00:00:00`);
        return `${date.getMonth() + 1}/${date.getDate()}`;
      })
    : ['', '', '', '', '', '', ''];
  const max = Math.max(1, ...values);
  const ceiling = Math.max(4, Math.ceil(max / 4) * 4);
  const x = (index: number) => left + ((width - left - right) * index) / Math.max(values.length - 1, 1);
  const y = (value: number) => height - bottom - ((height - top - bottom) * value) / ceiling;
  const path = values.map((value, index) => `${index ? 'L' : 'M'}${x(index)} ${y(value)}`).join(' ');
  const guides = [0, 0.25, 0.5, 0.75, 1].map((ratio) => Math.round(ceiling * ratio));

  return (
    <View style={{ width: '100%', aspectRatio: width / height }}>
      <Svg width="100%" height="100%" viewBox={`0 0 ${width} ${height}`}>
        {guides.map((guide) => (
          <React.Fragment key={guide}>
            <Line x1={left} y1={y(guide)} x2={width - right} y2={y(guide)} stroke={AD.chartGrid} strokeDasharray="3 3" />
            <SvgText x={left - 6} y={y(guide) + 3} fontSize={9} fill={AD.axisLabel} textAnchor="end">{guide}</SvgText>
          </React.Fragment>
        ))}
        <Path d={path} fill="none" stroke={colors.primaryDark} strokeWidth={2.5} strokeLinecap="round" strokeLinejoin="round" />
        {values.map((value, index) => <Circle key={index} cx={x(index)} cy={y(value)} r={3.5} fill={colors.gold} />)}
        {labels.map((label, index) => <SvgText key={index} x={x(index)} y={height - 8} fontSize={9} fill={AD.muted} textAnchor="middle">{label}</SvgText>)}
      </Svg>
    </View>
  );
}

export default function DashboardScreen({ navigation }: any) {
  const insets = useSafeAreaInsets();
  const [summary, setSummary] = useState(EMPTY_SUMMARY);
  const [alerts, setAlerts] = useState<AdminDashboardAlert[]>([]);
  const [trend, setTrend] = useState<AdminActivityTrend[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');

  const load = useCallback(async (refresh = false) => {
    refresh ? setRefreshing(true) : setLoading(true);
    setError('');
    try {
      const [nextSummary, nextAlerts, nextTrend] = await Promise.all([
        adminApi.getDashboardSummary(), adminApi.getDashboardAlerts(), adminApi.getActivityTrend(),
      ]);
      setSummary(nextSummary);
      setAlerts(nextAlerts);
      setTrend(nextTrend);
    } catch (e) {
      setError(getAdminErrorMessage(e));
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  const cards = useMemo(() => [
    ['전체 사용자', summary.total_user_count],
    ['활성 사용자', summary.active_user_count],
    ['오늘 접속', summary.today_access_user_count],
    ['신고 대기', summary.pending_report_count],
  ] as const, [summary]);
  const mainAlert = alerts[0]?.message ?? '현재 확인이 필요한 주요 알림이 없습니다.';
  const dateLabel = new Intl.DateTimeFormat('ko-KR', { dateStyle: 'long' }).format(new Date());

  return (
    <View style={styles.root}>
      <StatusBar style="light" /><HazeBackground /><MainHeader />
      <ScrollView
        contentContainerStyle={[styles.body, { paddingBottom: insets.bottom + 96 }]}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => void load(true)} />}
      >
        <Animated.View entering={FadeInDown.duration(420)} style={styles.banner}>
          <BannerGlow /><MegaphoneIcon /><Text style={styles.bannerText}><Text style={styles.bannerBold}>주요 알림: </Text>{mainAlert}</Text>
        </Animated.View>
        {error ? <Text style={styles.error}>{error}</Text> : null}
        <View style={styles.summaryHead}><Text style={styles.sectionTitle}>오늘의 요약</Text><Text style={styles.dateText}>{dateLabel}</Text></View>
        {loading ? <View style={{ gap: 10 }}><SkeletonCard /><SkeletonCard /></View> : (
          <View style={styles.grid}>{cards.map(([label, value], index) => (
            <Animated.View key={label} entering={FadeInDown.delay(index * 70).duration(420)} style={styles.statCard}>
              <Text style={styles.statLabel}>{label}</Text><CountUp target={value} delay={index * 70} style={styles.statValue} />
            </Animated.View>
          ))}</View>
        )}
        <Text style={[styles.sectionTitle, { marginBottom: 10 }]}>활동 추이 (최근 7일)</Text>
        <View style={styles.chartCard}><ActivityTrendChart data={trend} /></View>
      </ScrollView>
      <LinearGradient colors={['rgba(238,246,240,0)', colors.screenBg]} locations={[0, 0.4]} style={[styles.footer, { paddingBottom: insets.bottom + 20 }]}>
        <SpringButton style={[styles.footerBtn, styles.usersBtn]} onPress={() => navigation.navigate('UserList')}><Text style={styles.usersBtnText}>유저 관리</Text></SpringButton>
        <SpringButton style={[styles.footerBtn, styles.reportsBtn]} onPress={() => navigation.navigate('ReportList')}><Text style={styles.reportsBtnText}>신고 / 검토</Text></SpringButton>
      </LinearGradient>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.screenBg }, body: { padding: 16 },
  banner: { flexDirection: 'row', alignItems: 'center', gap: 8, backgroundColor: colors.parchment, borderWidth: 1.5, borderColor: colors.gold, borderRadius: 8, paddingVertical: 10, paddingHorizontal: 14, marginBottom: 16, overflow: 'hidden' },
  bannerText: { flex: 1, fontSize: 14, color: colors.primaryDark, fontFamily: fonts.bodyR }, bannerBold: { fontFamily: fonts.bodyB, fontWeight: '700' },
  error: { color: AD.red, fontFamily: fonts.bodyM, marginBottom: 12 }, summaryHead: { flexDirection: 'row', alignItems: 'flex-end', justifyContent: 'space-between', marginBottom: 12 },
  sectionTitle: { fontFamily: fonts.pixel, fontSize: 16, color: colors.primaryDark }, dateText: { fontSize: 12, color: AD.muted, fontFamily: fonts.bodyR },
  grid: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between', rowGap: 10, marginBottom: 20 },
  statCard: { width: '48.5%', backgroundColor: colors.white, borderWidth: 1, borderColor: AD.cardBorder, borderRadius: 12, padding: 14, ...shadow.card, shadowOpacity: 0.05 },
  statLabel: { fontSize: 12, color: AD.muted, marginBottom: 6, fontFamily: fonts.bodyR }, statValue: { fontSize: 22, fontWeight: '700', color: colors.primaryDark, fontFamily: fonts.bodyB },
  chartCard: { backgroundColor: colors.white, borderRadius: 12, padding: 12, ...shadow.card, shadowOpacity: 0.05 },
  footer: { position: 'absolute', bottom: 0, left: 0, right: 0, flexDirection: 'row', gap: 10, paddingHorizontal: 16, paddingTop: 12 },
  footerBtn: { flex: 1, height: 50, borderRadius: 8, alignItems: 'center', justifyContent: 'center' }, usersBtn: { backgroundColor: colors.primaryDark }, usersBtnText: { color: colors.parchment, fontFamily: fonts.pixel, fontSize: 17 }, reportsBtn: { backgroundColor: AD.red }, reportsBtnText: { color: colors.white, fontFamily: fonts.pixel, fontSize: 17 },
});
