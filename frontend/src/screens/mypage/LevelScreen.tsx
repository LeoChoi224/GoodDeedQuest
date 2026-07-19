/**
 * SCREEN 06-4 · 레벨 페이지 (route Level, back) — 내 정보 카드 · 경험치 바(PixelProgress,
 * 마운트 시 채워짐 + XP count-up) · 주간 경험치 추이 라인차트(react-native-svg, 그려지는 애니메이션:
 * 이번 주 초록 실선 / 지난 주 골드 점선) · 랭킹 보러가기 → Rank.
 * Matches 06_mypage_flow.dc.html screen 4.
 */
import React, { useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { StatusBar } from 'expo-status-bar';
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
  CHART,
  chartX,
  chartY,
  chartLine,
  pathLength,
} from './_parts';

const AnimatedPath = Animated.createAnimatedComponent(Path);

const XP_CUR = 1240;
const XP_MAX = 2000;

const WeeklyChart = React.memo(function WeeklyChart() {
  const len = pathLength(CHART.thisW);
  const draw = useSharedValue(0); // 0 → 1 (this-week line draw)
  const fade = useSharedValue(0); // last-week dashed + dots fade

  useEffect(() => {
    draw.value = withTiming(1, { duration: 1000, easing: Easing.inOut(Easing.cubic) });
    fade.value = withTiming(1, { duration: 900, easing: Easing.out(Easing.cubic) });
  }, []);

  const drawProps = useAnimatedProps(() => ({ strokeDashoffset: len * (1 - draw.value) }));
  const fadeProps = useAnimatedProps(() => ({ opacity: fade.value }));

  return (
    <View style={{ width: '100%', aspectRatio: CHART.W / CHART.H }}>
      <Svg width="100%" height="100%" viewBox={`0 0 ${CHART.W} ${CHART.H}`}>
        {/* gridlines */}
        {CHART.grid.map((g, i) => (
          <Line
            key={i}
            x1={CHART.pad}
            y1={chartY(g)}
            x2={CHART.W - CHART.pad}
            y2={chartY(g)}
            stroke="#EEF1F0"
            strokeWidth={1}
          />
        ))}
        {/* last week — gold dashed (fade-in) */}
        <AnimatedPath
          animatedProps={fadeProps}
          d={chartLine(CHART.lastW)}
          fill="none"
          stroke={colors.gold}
          strokeWidth={2}
          strokeDasharray="5 4"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        {/* this week — green solid (line-draw) */}
        <AnimatedPath
          animatedProps={drawProps}
          d={chartLine(CHART.thisW)}
          fill="none"
          stroke={colors.xpGreen}
          strokeWidth={2.5}
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeDasharray={len}
        />
        {/* this-week dots (fade-in) */}
        {CHART.thisW.map((v, i) => (
          <AnimatedPath
            key={i}
            animatedProps={fadeProps}
            d={`M ${chartX(i)} ${chartY(v)} m -3 0 a 3 3 0 1 0 6 0 a 3 3 0 1 0 -6 0`}
            fill={colors.xpGreen}
          />
        ))}
        {/* day labels */}
        {CHART.days.map((d, i) => (
          <SvgText key={i} x={chartX(i)} y={CHART.H - 4} fontSize={10} fill="#888" textAnchor="middle">
            {d}
          </SvgText>
        ))}
      </Svg>
    </View>
  );
});

export default function LevelScreen({ navigation }: any) {
  const xp = useCountUp(XP_CUR);

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
        {/* info card */}
        <View style={styles.infoCard}>
          <ConicAvatar size={52} />
          <View style={{ flex: 1 }}>
            <Text style={styles.name}>선한김철수</Text>
            <Text style={styles.sub}>마을 수호자 · LV.12 · 🔥 7일째</Text>
          </View>
        </View>

        {/* xp bar */}
        <View style={styles.xpBlock}>
          <View style={styles.xpHead}>
            <Text style={styles.xpLv}>LV.12</Text>
            <Text style={styles.xpVal}>
              {comma(xp)} / {comma(XP_MAX)} XP
            </Text>
          </View>
          <View style={styles.xpBarBox}>
            <PixelProgress progress={XP_CUR / XP_MAX} height={22} color={colors.xpGreen} track={colors.screenBg} />
          </View>
        </View>

        {/* weekly chart */}
        <Text style={styles.chartTitle}>주간 경험치 추이</Text>
        <View style={styles.chartCard}>
          <WeeklyChart />
          <View style={styles.legend}>
            <View style={styles.legendItem}>
              <View style={[styles.legendDash, { backgroundColor: colors.xpGreen }]} />
              <Text style={styles.legendText}>이번 주</Text>
            </View>
            <View style={styles.legendItem}>
              <View style={[styles.legendDash, { backgroundColor: colors.gold }]} />
              <Text style={styles.legendText}>지난 주</Text>
            </View>
          </View>
        </View>

        {/* → Rank */}
        <SpringButton style={styles.rankBtn} onPress={() => navigation.navigate('Rank')}>
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
