/**
 * SCREEN 05·1+2 · 지도메인 + 대항전 전국지도 — 지도 탭 ROOT (전국 뷰 전용).
 * 내 주변 둘러보기(상단) + 전국(시/도) 스타일라이즈드 SVG 지도(우리 팀=경기도 골드, pulse/pin) +
 * 팀 변경하기(팀 선택 모달, 지도 우측 하단 오버레이) + 시/도별 랭킹(/map/national-ranking).
 * "내 위치·지역 변경" 배너는 제거함 — 실시간 GPS 연동은 별도 작업으로 진행 예정, 팀 변경은 지도에 이미 있어 중복.
 * 시/도를 2탭으로 확정 선택하면 SiDoMap 화면으로 이동(드릴다운은 이 화면 안에서 안 함).
 */
import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, ScrollView, Pressable, ActivityIndicator } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { colors, fonts, radii, shadow } from '../../theme';
import HazeBackground from '../../components/HazeBackground';
import MainHeader from '../../components/MainHeader';
import SpringButton from '../../components/SpringButton';
import { TeamSelectPopup, RankRow } from './_parts';
import KoreaMapDrilldown from '../../components/KoreaMapDrilldown';
import { resolveProvinceName } from './provinceCityIds';
import { getNationalRanking, NationalRankingEntry } from '../../api/map';

export default function MainMapScreen({ navigation, route }: any) {
  const [teamSet, setTeamSet] = useState(true);
  const [pickOpen, setPickOpen] = useState(false);
  const [teamRegion, setTeamRegion] = useState('경기도');
  const [teamSigungu, setTeamSigungu] = useState('안양시');

  const [ranking, setRanking] = useState<NationalRankingEntry[]>([]);
  const [rankLoading, setRankLoading] = useState(true);
  const [rankError, setRankError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setRankLoading(true);
    setRankError(null);
    getNationalRanking()
      .then((data) => {
        if (!cancelled) setRanking(data.ranking);
      })
      .catch((err) => {
        if (!cancelled) setRankError(err.message ?? '랭킹을 불러오지 못했습니다.');
      })
      .finally(() => {
        if (!cancelled) setRankLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const maxScore = ranking.length > 0 ? Math.max(ranking[0].total_score, 1) : 1;

  const goToProvince = (cityId: number, fallbackName: string) => {
    const svgName = resolveProvinceName(cityId) ?? fallbackName;
    navigation.navigate('SiDoMap', { province: svgName, teamRegion, teamSigungu });
  };

  return (
    <View style={styles.root}>
      <StatusBar style="light" />
      <HazeBackground />
      <MainHeader />

      <ScrollView contentContainerStyle={styles.body} showsVerticalScrollIndicator={false}>
        {/* 내 주변 둘러보기 — 랭킹에 밀려 아래로 안 가도록 상단 배치 */}
        <SpringButton style={styles.nearbyBtn} onPress={() => navigation.navigate('VolSearch')}>
          <Text style={styles.nearbyText}>내 주변 둘러보기</Text>
        </SpringButton>

        {/* 지도 카드 — 전국 지도, 시/도를 2탭으로 확정하면 SiDoMap 화면으로 이동 */}
        <View style={styles.mapCard}>
          <KoreaMapDrilldown
            teamRegion={teamRegion}
            teamSigungu={teamSigungu}
            height={560}
            drillOnRegionTap={false}
            onRegion={(name) => navigation.navigate('SiDoMap', { province: name, teamRegion, teamSigungu })}
          />
          {teamSet ? (
            <Pressable style={styles.teamChangeBtn} onPress={() => setPickOpen(true)}>
              <Text style={styles.teamChangeText}>팀 변경하기</Text>
            </Pressable>
          ) : (
            <View style={styles.teamOverlay}>
              <Text style={styles.overlayHint}>대항전에 참여할 팀을 설정해 주세요</Text>
              <SpringButton style={styles.overlayBtn} onPress={() => setPickOpen(true)}>
                <Text style={styles.overlayBtnText}>대항전 참여팀 설정하기</Text>
              </SpringButton>
            </View>
          )}
        </View>

        {/* 시/도별 랭킹 */}
        <Text style={styles.sectionTitle}>🏆 시/도별 랭킹</Text>
        {rankLoading ? (
          <View style={styles.centerBox}>
            <ActivityIndicator color={colors.primaryDark} />
          </View>
        ) : rankError ? (
          <View style={styles.centerBox}>
            <Text style={styles.errorText}>{rankError}</Text>
          </View>
        ) : ranking.length === 0 ? (
          <View style={styles.centerBox}>
            <Text style={styles.errorText}>아직 랭킹 데이터가 없어요.</Text>
          </View>
        ) : (
          <View style={styles.listCard}>
            {ranking.map((r, i) => (
              <RankRow
                key={r.city_id}
                index={i}
                name={r.city_name}
                score={r.total_score.toLocaleString()}
                pct={r.total_score / maxScore}
                onPress={() => goToProvince(r.city_id, r.city_name)}
              />
            ))}
          </View>
        )}
      </ScrollView>

      <TeamSelectPopup
        visible={pickOpen}
        onClose={() => setPickOpen(false)}
        region={teamRegion}
        city={teamSigungu}
        onConfirm={(region, city) => {
          setTeamRegion(region);
          setTeamSigungu(city);
          setTeamSet(true);
          setPickOpen(false);
        }}
      />
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
  teamChangeBtn: {
    position: 'absolute',
    right: 20,
    bottom: 20,
    backgroundColor: colors.pixelBorder,
    borderRadius: 24,
    paddingHorizontal: 16,
    paddingVertical: 8,
    ...shadow.card,
  },
  teamChangeText: { fontFamily: fonts.pixel, fontSize: 12, color: colors.parchment },
  teamOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(3,50,54,0.55)',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 14,
    padding: 24,
  },
  overlayHint: { color: colors.parchment, fontSize: 14, fontFamily: fonts.bodyM, textAlign: 'center' },
  overlayBtn: {
    height: 48,
    borderRadius: radii.button,
    backgroundColor: colors.gold,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 22,
  },
  overlayBtnText: { fontFamily: fonts.pixel, fontSize: 15, color: colors.parchment },
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
    marginBottom: 16,
    ...shadow.card,
  },
  centerBox: {
    paddingVertical: 32,
    alignItems: 'center',
    marginBottom: 16,
  },
  errorText: {
    fontSize: 13,
    color: colors.textSecondary,
    fontFamily: fonts.bodyR,
  },
  nearbyBtn: {
    height: 52,
    borderRadius: 8,
    backgroundColor: colors.primaryDark,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
    ...shadow.button,
  },
  nearbyText: { fontFamily: fonts.pixel, fontSize: 18, color: colors.parchment },
});