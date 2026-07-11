/**
 * SCREEN 05·1+2 · 지도메인 + 대항전 전국지도 — 지도 탭 ROOT.
 * 내 위치 배너 + 전국(시/도) 스타일라이즈드 SVG 지도(우리 팀=경기도 골드, pulse/pin) +
 * 팀 변경하기(팀 선택 모달) + 내 주변 둘러보기 + 🏆 시도별 랭킹 리스트.
 * 시/도 탭 → Ranking, 내 주변 둘러보기 → Nearby.
 */
import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, Pressable } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import Animated, { FadeInDown } from 'react-native-reanimated';
import { colors, fonts, radii, shadow } from '../../theme';
import HazeBackground from '../../components/HazeBackground';
import MainHeader from '../../components/MainHeader';
import SpringButton from '../../components/SpringButton';
import BottomSheet from '../../components/BottomSheet';
import { PinDot, RankRow, TeamSelectPopup } from './_parts';
import KoreaMapDrilldown from '../../components/KoreaMapDrilldown';

const SIDO_RANK = [
  { name: '강원도', score: '1,000', v: 1000 },
  { name: '서울특별시', score: '800', v: 800 },
  { name: '경기도', score: '500', v: 500 },
  { name: '부산광역시', score: '420', v: 420 },
  { name: '전라남도', score: '360', v: 360 },
];

export default function MapScreen({ navigation, route }: any) {
  const [teamSet, setTeamSet] = useState(true);
  const [pickOpen, setPickOpen] = useState(false);
  const [myRegion, setMyRegion] = useState('경기도 안양시');
  const [regionPickOpen, setRegionPickOpen] = useState(false);
  const [teamRegion, setTeamRegion] = useState('경기도');
  const [teamSigungu, setTeamSigungu] = useState('안양시');

  const openRanking = (region: string) => navigation.navigate('Ranking', { region });

  return (
    <View style={styles.root}>
      <StatusBar style="light" />
      <HazeBackground />
      <MainHeader />

      <ScrollView contentContainerStyle={styles.body} showsVerticalScrollIndicator={false}>
        {/* 내 위치 배너 — 탭하면 지역 선택 */}
        <Animated.View entering={FadeInDown.duration(360)}>
          <Pressable style={styles.locBanner} onPress={() => setRegionPickOpen(true)}>
            <PinDot size={16} />
            <Text style={styles.locText}>{myRegion} · 내 위치</Text>
            <Text style={styles.locEdit}>지역 변경</Text>
          </Pressable>
        </Animated.View>

        {/* 지도 카드 — korea_map_drilldown 지도 (시/도 탭 → 시군구 랭킹으로 이동) */}
        <View style={styles.mapCard}>
          <KoreaMapDrilldown
            teamRegion={teamRegion}
            teamSigungu={teamSigungu}
            onSigungu={(sg, prov) => navigation.navigate('Ranking', { region: prov, sigungu: sg })}
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

        {/* 내 주변 둘러보기 */}
        <SpringButton style={styles.nearbyBtn} onPress={() => navigation.navigate('Nearby')}>
          <Text style={styles.nearbyText}>내 주변 둘러보기</Text>
        </SpringButton>

        {/* 🏆 시도별 랭킹 */}
        <Text style={styles.sectionTitle}>🏆 시도별 랭킹</Text>
        <View style={styles.listCard}>
          {SIDO_RANK.map((r, i) => (
            <RankRow
              key={r.name}
              index={i}
              name={r.name}
              score={r.score}
              pct={r.v / SIDO_RANK[0].v}
              onPress={() => openRanking(r.name)}
            />
          ))}
        </View>
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

      {/* 지역 선택 — 드릴다운 지도로 시/도 → 시군구 선택 */}
      <BottomSheet visible={regionPickOpen} onClose={() => setRegionPickOpen(false)} title="지역 선택">
        <KoreaMapDrilldown
          teamRegion={teamRegion}
          teamSigungu={teamSigungu}
          onSigungu={(sg, prov) => {
            setMyRegion(`${prov} ${sg}`);
            setRegionPickOpen(false);
          }}
        />
      </BottomSheet>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.screenBg },
  body: { padding: 16, paddingBottom: 32 },
  locBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: colors.parchment,
    borderWidth: 1,
    borderColor: colors.pixelBorder,
    borderRadius: 24,
    paddingHorizontal: 16,
    paddingVertical: 11,
    marginBottom: 16,
  },
  locText: { flex: 1, fontSize: 14, fontWeight: '500', color: colors.primaryDark, fontFamily: fonts.bodyM },
  locEdit: { fontFamily: fonts.pixel, fontSize: 12, color: colors.gold },
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
    alignSelf: 'center',
    marginTop: 10,
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
  overlayBtnText: { fontFamily: fonts.pixel, fontSize: 15, color: colors.primaryDark },
  nearbyBtn: {
    height: 52,
    borderRadius: 8,
    backgroundColor: colors.primaryDark,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 24,
    ...shadow.button,
  },
  nearbyText: { fontFamily: fonts.pixel, fontSize: 18, color: colors.parchment },
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
