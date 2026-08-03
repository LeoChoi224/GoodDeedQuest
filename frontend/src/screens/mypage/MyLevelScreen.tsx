/**
 * SCREEN 06-4 · 레벨 페이지 (route MyLevel, back) — 내 정보 카드(getMyProfile() 실API) ·
 * 경험치 바(PixelProgress, 마운트/포커스마다 채워짐 + XP count-up, 이번 레벨 안에서의 진행률로 표시) ·
 * 주간 경험치 추이 라인차트(react-native-svg, 그려지는 애니메이션, 일요일부터 시작하고
 * 아직 지나지 않은 요일은 선이 안 그려짐) · 랭킹 보러가기 → Ranking.
 * /growth/status + /mypage/profile 실API 연결.
 * ⭐ useFocusEffect로 교체 — 화면에 포커스가 올 때마다(다른 화면 갔다 뒤로가기로 돌아올 때도)
 * 다시 불러오게 함. 이전엔 useEffect(마운트 1회)라 퀘스트 완료 후 돌아와도 새로고침 안 됐음.
 * ⭐ 원본 디자인엔 "지난 주" 골드 점선 비교선이 있었으나, 백엔드가 이번 주 누적치만 주고
 * 지난 주 데이터는 안 줘서 이번 주 실선만 표시함(지난 주 비교는 백엔드 확장 필요).
 * Matches 06_mypage_flow.dc.html screen 4.
 */
import React, { useCallback, useEffect, useState } from 'react';
import { View, Text, StyleSheet, ScrollView, ActivityIndicator } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { useFocusEffect } from '@react-navigation/native';
import Svg, { Line, Path, Text as SvgText } from 'react-native-svg';
import Animated, {
  useSharedValue,
  useAnimatedProps,
  withTiming,
  Easing,
} from 'react-native-reanimated';
import { colors, fonts } from '../../theme';
import HazeBackground from '../../components/HazeBackground';
import MainHeader from '../../components/MainHeader';
import SpringButton from '../../components/SpringButton';
import PixelProgress from '../../components/PixelProgress';
import {
  ConicAvatar,
  useCountUp,
  comma,
  CHART_LAYOUT,
  chartX,
  chartY,
  chartLine,
  pathLength,
} from './_parts';
import { getGrowthStatus, DailyXp } from '../../api/growth';
import { getMyProfile, MyProfile } from '../../api/mypage';

const AnimatedPath = Animated.createAnimatedComponent(Path);

const WEEKDAY_KR = ['일', '월', '화', '수', '목', '금', '토'];

function dayLabel(dateStr: string): string {
  const d = new Date(dateStr);
  return isNaN(d.getTime()) ? '' : WEEKDAY_KR[d.getDay()];
}

const WeeklyChart = React.memo(function WeeklyChart({ graph }: { graph: DailyXp[] }) {
  const rawValues = graph.map((d) => d.cumulative_xp); // null 포함, 길이 7 유지
  const knownValues = rawValues.filter((v): v is number => v !== null);
  const maxV = Math.max(...knownValues, 10);
  const grid = [0, 0.25, 0.5, 0.75, 1].map((f) => Math.round(maxV * f));

  const len = pathLength(rawValues, maxV);
  const draw = useSharedValue(0); // 0 → 1 (this-week line draw)
  const fade = useSharedValue(0); // dots fade

  useEffect(() => {
    draw.value = withTiming(1, { duration: 1000, easing: Easing.inOut(Easing.cubic) });
    fade.value = withTiming(1, { duration: 900, easing: Easing.out(Easing.cubic) });
  }, []);

  const drawProps = useAnimatedProps(() => ({ strokeDashoffset: len * (1 - draw.value) }));
  const fadeProps = useAnimatedProps(() => ({ opacity: fade.value }));

  return (
    <View style={{ width: '100%', aspectRatio: CHART_LAYOUT.W / CHART_LAYOUT.H }}>
      <Svg width="100%" height="100%" viewBox={`0 0 ${CHART_LAYOUT.W} ${CHART_LAYOUT.H}`}>
        {/* gridlines */}
        {grid.map((g, i) => (
          <Line
            key={i}
            x1={CHART_LAYOUT.pad}
            y1={chartY(g, maxV)}
            x2={CHART_LAYOUT.W - CHART_LAYOUT.pad}
            y2={chartY(g, maxV)}
            stroke="#EEF1F0"
            strokeWidth={1}
          />
        ))}
        {/* 이번 주 — 초록 실선(오늘까지만, 그려지는 애니메이션) */}
        <AnimatedPath
          animatedProps={drawProps}
          d={chartLine(rawValues, maxV)}
          fill="none"
          stroke={colors.xpGreen}
          strokeWidth={2.5}
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeDasharray={len}
        />
        {/* dots (오늘까지만, fade-in) */}
        {graph.map((d, i) =>
          d.cumulative_xp === null ? null : (
            <AnimatedPath
              key={i}
              animatedProps={fadeProps}
              d={`M ${chartX(i, graph.length)} ${chartY(d.cumulative_xp, maxV)} m -3 0 a 3 3 0 1 0 6 0 a 3 3 0 1 0 -6 0`}
              fill={colors.xpGreen}
            />
          )
        )}
        {/* day labels — 일요일부터 7일 전체 표시 */}
        {graph.map((d, i) => (
          <SvgText key={i} x={chartX(i, graph.length)} y={CHART_LAYOUT.H - 4} fontSize={10} fill="#888" textAnchor="middle">
            {dayLabel(d.date)}
          </SvgText>
        ))}
      </Svg>
    </View>
  );
});

export default function MyLevelScreen({ navigation }: any) {
  const [profile, setProfile] = useState<MyProfile | null>(null);
  const [level, setLevel] = useState(1);
  const [currentXp, setCurrentXp] = useState(0);
  const [nextLevelXp, setNextLevelXp] = useState(1000);
  const [levelFloorXp, setLevelFloorXp] = useState(0);
  const [graph, setGraph] = useState<DailyXp[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // ⭐ 수정: useEffect(마운트 1회) → useFocusEffect(포커스 올 때마다) - 퀘스트 완료 후
  // Ranking 갔다 뒤로가기로 돌아와도 최신 데이터로 다시 불러오게.
  useFocusEffect(
    useCallback(() => {
      let cancelled = false;
      setLoading(true);
      setError(null);
      Promise.all([getGrowthStatus(), getMyProfile()])
        .then(([growth, prof]) => {
          if (cancelled) return;
          setLevel(growth.current_level);
          setCurrentXp(growth.current_xp);
          setNextLevelXp(growth.next_level_xp);
          setLevelFloorXp(growth.current_level_floor_xp);
          setGraph(growth.weekly_xp_graph);
          setProfile(prof);
        })
        .catch((err) => {
          if (!cancelled) setError(err.message ?? '정보를 불러오지 못했습니다.');
        })
        .finally(() => {
          if (!cancelled) setLoading(false);
        });
      return () => {
        cancelled = true;
      };
    }, [])
  );

  const xpCount = useCountUp(currentXp);

  return (
    <View style={styles.root}>
      <StatusBar style="light" />
      <HazeBackground />
      <MainHeader showBack title="레벨" />

      <ScrollView
        style={styles.scroll}
        contentContainerStyle={styles.body}
        showsVerticalScrollIndicator={false}
      >
        {/* info card — /mypage/profile 실API */}
        <View style={styles.infoCard}>
          <ConicAvatar size={52} imageUri={profile?.profile_image_url ?? null} />
          <View style={{ flex: 1 }}>
            <Text style={styles.name}>{profile?.nickname ?? ''}</Text>
            <Text style={styles.sub}>
              {profile?.title ? `${profile.title} · ` : ''}LV.{level} · 🔥 {profile?.daily_streak ?? 0}일째
            </Text>
          </View>
        </View>

        {loading ? (
          <View style={styles.centerBox}>
            <ActivityIndicator color={colors.primaryDark} />
          </View>
        ) : error ? (
          <View style={styles.centerBox}>
            <Text style={styles.errorText}>{error}</Text>
          </View>
        ) : (
          <>
            {/* xp bar — 이번 레벨 안에서의 진행률로 표시(레벨업마다 0%로 리셋) */}
            <View style={styles.xpBlock}>
              <View style={styles.xpHead}>
                <Text style={styles.xpLv}>LV.{level}</Text>
                <Text style={styles.xpVal}>
                  {comma(xpCount)} / {comma(nextLevelXp)} XP
                </Text>
              </View>
              <View style={styles.xpBarBox}>
                <PixelProgress
                  progress={
                    nextLevelXp - levelFloorXp > 0
                      ? (currentXp - levelFloorXp) / (nextLevelXp - levelFloorXp)
                      : 0
                  }
                  height={22}
                  color={colors.xpGreen}
                  track={colors.screenBg}
                />
              </View>
            </View>

            {/* weekly chart */}
            <Text style={styles.chartTitle}>주간 경험치 추이</Text>
            <View style={styles.chartCard}>
              {graph.length === 0 ? (
                <Text style={styles.emptyText}>최근 7일간 획득한 경험치가 없어요.</Text>
              ) : (
                <>
                  <WeeklyChart graph={graph} />
                  <View style={styles.legend}>
                    <View style={styles.legendItem}>
                      <View style={[styles.legendDash, { backgroundColor: colors.xpGreen }]} />
                      <Text style={styles.legendText}>이번 주 누적 XP</Text>
                    </View>
                  </View>
                </>
              )}
            </View>
          </>
        )}

        {/* → Rank */}
        <SpringButton style={styles.rankBtn} onPress={() => navigation.navigate('Ranking')}>
          <Text style={styles.rankBtnText}>랭킹 보러가기</Text>
        </SpringButton>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.screenBg },
  scroll: { flex: 1 },
  body: { padding: 16, paddingBottom: 28 },

  infoCard: {
    backgroundColor: colors.parchment,
    borderWidth: 1,
    borderColor: colors.pixelBorder,
    borderRadius: 12,
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 18,
  },
  name: { fontSize: 16, fontWeight: '600', color: colors.primaryDark, fontFamily: fonts.bodyM },
  sub: { fontSize: 12, color: colors.gold, marginTop: 2, fontFamily: fonts.bodyR },

  centerBox: { paddingVertical: 32, alignItems: 'center' },
  errorText: { fontSize: 13, color: colors.textSecondary, fontFamily: fonts.bodyR },
  emptyText: { fontSize: 13, color: colors.textSecondary, fontFamily: fonts.bodyR, textAlign: 'center', paddingVertical: 24 },

  xpBlock: { marginBottom: 22 },
  xpHead: { flexDirection: 'row', alignItems: 'baseline', justifyContent: 'space-between', marginBottom: 8 },
  xpLv: { fontFamily: fonts.pixel, fontSize: 18, color: colors.primaryDark },
  xpVal: { fontSize: 13, color: '#888', fontFamily: fonts.bodyR },
  xpBarBox: {
    borderWidth: 1.5,
    borderColor: colors.pixelBorder,
    borderRadius: 10,
    overflow: 'hidden',
  },

  chartTitle: { fontFamily: fonts.pixel, fontSize: 14, color: colors.primaryDark, marginBottom: 10 },
  chartCard: {
    backgroundColor: colors.white,
    borderRadius: 12,
    padding: 14,
    marginBottom: 18,
    shadowColor: '#033236',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.06,
    shadowRadius: 10,
    elevation: 2,
  },
  legend: { flexDirection: 'row', gap: 16, justifyContent: 'center', marginTop: 10 },
  legendItem: { flexDirection: 'row', alignItems: 'center', gap: 5 },
  legendDash: { width: 14, height: 3, borderRadius: 2 },
  legendText: { fontSize: 11, color: '#666', fontFamily: fonts.bodyR },

  rankBtn: {
    height: 50,
    borderRadius: 8,
    backgroundColor: colors.primaryDark,
    alignItems: 'center',
    justifyContent: 'center',
  },
  rankBtnText: { color: colors.parchment, fontFamily: fonts.pixel, fontSize: 16 },
});