/**
 * SCREEN 05 · 시/도 드릴다운 — 전국 지도에서 특정 시/도를 확정 선택(2탭)했을 때 진입.
 * 해당 시/도의 시군구 지도(KoreaMapDrilldown, initialProvince 고정) + 시군구별 랭킹 리스트.
 * "내 주변 둘러보기" · "팀 변경하기"는 이 화면엔 아예 없음(전국 화면 전용 기능).
 * 시군구 탭(2회) → RegionDetails로 이동. 뒤로가기는 네비게이션 스택(헤더 back/스와이프) 사용.
 */
import React from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { colors, fonts, radii, shadow } from '../../theme';
import HazeBackground from '../../components/HazeBackground';
import MainHeader from '../../components/MainHeader';
import { RankRow } from './_parts';
import KoreaMapDrilldown from '../../components/KoreaMapDrilldown';

// TODO: /map/city-ranking?city=<province> API로 교체 예정. 지금은 레이아웃 확인용 더미.
const CITY_RANK_MOCK = [
  { name: '안양시', score: '1,000', v: 1000 },
  { name: '수원시', score: '860', v: 860 },
  { name: '성남시', score: '740', v: 740 },
  { name: '고양시', score: '520', v: 520 },
  { name: '용인시', score: '410', v: 410 },
];

export default function SiDoMapScreen({ navigation, route }: any) {
  const province: string = route.params?.province ?? '';
  const teamRegion: string = route.params?.teamRegion ?? '경기도';
  const teamSigungu: string = route.params?.teamSigungu ?? '안양시';

  return (
    <View style={styles.root}>
      <StatusBar style="light" />
      <HazeBackground />
      <MainHeader showBack title={province} />

      <ScrollView contentContainerStyle={styles.body} showsVerticalScrollIndicator={false}>
        <View style={styles.mapCard}>
          <KoreaMapDrilldown
            teamRegion={teamRegion}
            teamSigungu={teamSigungu}
            initialProvince={province}
            allowNational={false}
            height={520}
            onSigungu={(sg, prov) => navigation.navigate('RegionDetails', { region: prov, sigungu: sg })}
          />
        </View>

        <Text style={styles.sectionTitle}>🏆 {province} 시군구별 랭킹</Text>
        <View style={styles.listCard}>
          {CITY_RANK_MOCK.map((r, i) => (
            <RankRow
              key={r.name}
              index={i}
              name={r.name}
              score={r.score}
              pct={r.v / CITY_RANK_MOCK[0].v}
              onPress={() => navigation.navigate('RegionDetails', { region: province, sigungu: r.name })}
            />
          ))}
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.screenBg },
  body: { padding: 16, paddingBottom: 32 },
  mapCard: {
    position: 'relative',
    borderWidth: 1.5,
    borderColor: colors.pixelBorder,
    borderRadius: radii.chip,
    backgroundColor: colors.white,
    marginBottom: 16,
    padding: 12,
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
  listCard: {
    backgroundColor: colors.white,
    borderRadius: radii.chip,
    overflow: 'hidden',
    ...shadow.card,
  },
});