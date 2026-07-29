/**
 * SCREEN 05·3+4 · 시군구 랭킹 + 시군구별 상세랭킹 (SegmentedTabs).
 * Tab0 시군구 랭킹: 경기도 시군구 SVG(Layer2) + 시군구별 포인트 랭킹(애니 바) + 페이지 도트.
 * Tab1 상세 랭킹: 유저 랭킹 카드(XP) + 🤖 부족봉사 AI 판단(shimmer→로딩) + 📌 추천 봉사시설.
 * 시군구 탭/랭킹 행 → Tab1. 추천 봉사시설 → VolunteerDetail. 팀 변경 → 팀 선택 모달.
 */
import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, ScrollView, Pressable } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import Animated, { FadeInDown } from 'react-native-reanimated';
import { colors, fonts, radii, shadow } from '../../theme';
import HazeBackground from '../../components/HazeBackground';
import MainHeader from '../../components/MainHeader';
import SegmentedTabs from '../../components/SegmentedTabs';
import Shimmer from '../../components/Shimmer';
import { RankRow, UserRankRow, TeamSelectPopup } from './_parts';
import KoreaMapDrilldown from '../../components/KoreaMapDrilldown';

const SIGUNGU_RANK = [
  { name: '안양시', score: '1,000', v: 1000 },
  { name: '수원시', score: '800', v: 800 },
  { name: '성남시', score: '500', v: 500 },
  { name: '고양시', score: '420', v: 420 },
  { name: '용인시', score: '380', v: 380 },
];

const USER_RANK = [
  { rank: 'MVP', name: 'user1', xp: '200' },
  { rank: '2등', name: 'user2', xp: '150' },
  { rank: '3등', name: 'user3', xp: '100' },
];

const FACILITIES = [
  { name: '경기 안양시 수리 장애인 복지관', sub: '장애/비장애인 형제지원프로그램 봉사자' },
  { name: '경기 만안 종합 사회복지관', sub: '식사자원 봉사자 모집' },
];

export default function RankingScreen({ navigation, route }: any) {
  const region = route?.params?.region ?? '경기도';
  const city = '안양시';
  const [tab, setTab] = useState(0);
  const [pickOpen, setPickOpen] = useState(false);
  const [aiLoading, setAiLoading] = useState(true);

  useEffect(() => {
    const t = setTimeout(() => setAiLoading(false), 1400);
    return () => clearTimeout(t);
  }, []);

  const goDetail = (_name?: string) => setTab(1);

  return (
    <View style={styles.root}>
      <StatusBar style="light" />
      <HazeBackground />
      <MainHeader
        showBack
        title={region}
        right={
          <Pressable hitSlop={8} onPress={() => setPickOpen(true)}>
            <Text style={styles.headerAction}>팀 변경</Text>
          </Pressable>
        }
      />

      <View style={styles.tabsWrap}>
        <SegmentedTabs tabs={['시군구 랭킹', '상세 랭킹']} index={tab} onChange={setTab} />
      </View>

      <ScrollView contentContainerStyle={styles.body} showsVerticalScrollIndicator={false}>
        {tab === 0 ? (
          <>
            <View style={styles.mapCard}>
              <KoreaMapDrilldown
                initialProvince={region}
                allowNational={false}
                teamSigungu="안양시"
                height={320}
                onSigungu={(sg) => goDetail(sg)}
              />
            </View>

            <Text style={styles.sectionTitle}>📊 시군구별 포인트 랭킹</Text>
            <View style={styles.listCard}>
              {SIGUNGU_RANK.map((r, i) => (
                <RankRow
                  key={r.name}
                  index={i}
                  name={r.name}
                  score={r.score}
                  pct={r.v / SIGUNGU_RANK[0].v}
                  onPress={() => goDetail(r.name)}
                />
              ))}
            </View>

            <View style={styles.dots}>
              <View style={[styles.dot, styles.dotActive]} />
              <View style={styles.dot} />
              <View style={styles.dot} />
            </View>
          </>
        ) : (
          <>
            <Text style={styles.cityTitle}>{city}</Text>

            {/* 유저 랭킹 카드 */}
            <View style={styles.userCard}>
              <View style={styles.userHead}>
                <Text style={[styles.userHeadTxt, { width: 56 }]}>순위</Text>
                <Text style={[styles.userHeadTxt, { flex: 1 }]}>닉네임</Text>
                <Text style={styles.userHeadTxt}>획득 XP</Text>
              </View>
              {USER_RANK.map((u, i) => (
                <UserRankRow
                  key={u.name}
                  index={i}
                  rank={u.rank}
                  name={u.name}
                  xp={u.xp}
                  onPress={() => navigation.navigate('UserDetail', { user: { name: u.name, info: `${u.rank} · ${u.xp} XP` } })}
                />
              ))}
            </View>

            {/* AI 부족봉사 판단 */}
            <View style={styles.aiBox}>
              <Text style={styles.aiTitle}>🤖 지역 부족봉사 AI 판단</Text>
              {aiLoading ? (
                <View style={{ gap: 8 }}>
                  <Shimmer height={12} width="100%" />
                  <Shimmer height={12} width="80%" />
                </View>
              ) : (
                <Text style={styles.aiText}>
                  {city}는 현재 <Text style={styles.aiBold}>장애인 복지 및 식사 지원</Text> 봉사 분야 인력이 부족합니다.
                  관련 봉사에 참여하면 추가 포인트를 받을 수 있어요.
                </Text>
              )}
            </View>

            {/* 추천 봉사시설 */}
            <Text style={styles.recTitle}>📌 추천 봉사시설</Text>
            <View style={{ gap: 10 }}>
              {FACILITIES.map((f, i) => (
                <Animated.View key={f.name} entering={FadeInDown.delay(100 + i * 90).duration(420)}>
                  <Pressable
                    style={({ pressed }) => [styles.facCard, pressed && styles.facPressed]}
                    onPress={() => navigation.navigate('VolunteerDetail', { item: f })}
                  >
                    <Text style={styles.facName}>{f.name}</Text>
                    <Text style={styles.facSub}>{f.sub}</Text>
                  </Pressable>
                </Animated.View>
              ))}
            </View>
          </>
        )}
      </ScrollView>

      <TeamSelectPopup
        visible={pickOpen}
        onClose={() => setPickOpen(false)}
        onConfirm={() => setPickOpen(false)}
        region={region}
        city={city}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.screenBg },
  headerAction: { fontFamily: fonts.bodyB, fontSize: 13, color: colors.gold },
  tabsWrap: { paddingHorizontal: 16, paddingTop: 12, paddingBottom: 4 },
  body: { padding: 16, paddingBottom: 32 },
  mapCard: {
    borderWidth: 1.5,
    borderColor: colors.pixelBorder,
    borderRadius: radii.chip,
    overflow: 'hidden',
    backgroundColor: colors.white,
    height: 280,
    marginBottom: 16,
    padding: 8,
  },
  sectionTitle: {
    fontFamily: fonts.pixel,
    fontSize: 16,
    color: colors.primaryDark,
    marginBottom: 12,
    paddingBottom: 8,
    borderBottomWidth: 2,
    borderBottomColor: '#E6D9B8',
  },
  listCard: { backgroundColor: colors.white, borderRadius: radii.chip, overflow: 'hidden', ...shadow.card },
  dots: { flexDirection: 'row', justifyContent: 'center', gap: 6, marginTop: 12 },
  dot: { width: 7, height: 7, borderRadius: 4, backgroundColor: '#C9D6CE' },
  dotActive: { width: 16, backgroundColor: colors.primaryDark },
  /* detail tab */
  cityTitle: { textAlign: 'center', fontFamily: fonts.pixel, fontSize: 22, color: colors.primaryDark, marginBottom: 16 },
  userCard: {
    backgroundColor: colors.parchment,
    borderWidth: 1.5,
    borderColor: colors.pixelBorder,
    borderRadius: radii.chip,
    padding: 16,
    marginBottom: 16,
  },
  userHead: { flexDirection: 'row', paddingBottom: 10, borderBottomWidth: 1, borderBottomColor: '#E6D9B8' },
  userHeadTxt: { fontFamily: fonts.pixel, fontSize: 13, color: '#888' },
  aiBox: {
    backgroundColor: colors.screenBg,
    borderLeftWidth: 4,
    borderLeftColor: colors.gold,
    borderRadius: 8,
    padding: 14,
    marginBottom: 18,
  },
  aiTitle: { fontFamily: fonts.pixel, fontSize: 15, color: colors.primaryDark, marginBottom: 8 },
  aiText: { fontSize: 13, color: '#555', lineHeight: 21, fontFamily: fonts.bodyR },
  aiBold: { color: colors.primaryDark, fontFamily: fonts.bodyB },
  recTitle: { fontFamily: fonts.pixel, fontSize: 16, color: colors.primaryDark, marginBottom: 12 },
  facCard: {
    backgroundColor: colors.white,
    borderLeftWidth: 3,
    borderLeftColor: colors.xpGreen,
    borderRadius: 8,
    paddingHorizontal: 14,
    paddingVertical: 13,
    ...shadow.card,
  },
  facPressed: { backgroundColor: '#F4F9F5' },
  facName: { fontWeight: '700', fontSize: 14, color: colors.primaryDark, marginBottom: 3, fontFamily: fonts.bodyB },
  facSub: { fontSize: 12, color: '#888', fontFamily: fonts.bodyR },
});
