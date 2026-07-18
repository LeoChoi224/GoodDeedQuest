/**
 * SCREEN 05·5+6+7 · 내 주변 둘러보기 + 지역 검색 + 핀 클릭 간략정보.
 * 주소 검색(GdqInput) + 필터 탭(봉사·선행) + Kakao 3km 지도(내 위치 파란 마커·핀).
 * 검색어 입력 → 결과 리스트. 핀 탭 → 하단 BottomSheet(기관명·거리·주소) → VolunteerDetail.
 */
import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, Pressable } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { LinearGradient } from 'expo-linear-gradient';
import Svg, { Line } from 'react-native-svg';
import Animated, { FadeInDown } from 'react-native-reanimated';
import { colors, fonts, radii } from '../../theme';
import HazeBackground from '../../components/HazeBackground';
import MainHeader from '../../components/MainHeader';
import GdqInput from '../../components/GdqInput';
import BottomSheet from '../../components/BottomSheet';
import SpringButton from '../../components/SpringButton';
import { SearchIcon, MapPinIcon, PinDot, PulseRing, MAP } from './_parts';

type Pin = { name: string; dist: string; addr: string; left: string; top: string };
const PINS: Pin[] = [
  { name: '수리 장애인 복지관', dist: '1.2km', addr: '경기 안양시 만안구 안양로 123', left: '28%', top: '26%' },
  { name: '만안 종합 사회복지관', dist: '0.8km', addr: '경기 안양시 만안구 예술공원로 7', left: '64%', top: '34%' },
  { name: '안양 노인복지센터', dist: '2.1km', addr: '경기 안양시 동안구 시민대로 45', left: '56%', top: '66%' },
];

const RESULTS = [
  { addr: '경기 안양시 만안구 안양로 123', kind: '봉사' },
  { addr: '경기 안양시 동안구 시민대로 45', kind: '봉사' },
  { addr: '경기 안양시 만안구 예술공원로 7', kind: '선행' },
  { addr: '경기 안양시 만안구 냇마을로 22', kind: '봉사' },
];

function MapGrid() {
  const cells = Array.from({ length: 10 });
  return (
    <Svg style={StyleSheet.absoluteFill} width="100%" height="100%" viewBox="0 0 300 400" preserveAspectRatio="none">
      {cells.map((_, i) => (
        <Line key={`v${i}`} x1={i * 30} y1={0} x2={i * 30} y2={400} stroke={MAP.grid} strokeWidth={0.6} />
      ))}
      {Array.from({ length: 14 }).map((_, i) => (
        <Line key={`h${i}`} x1={0} y1={i * 30} x2={300} y2={i * 30} stroke={MAP.grid} strokeWidth={0.6} />
      ))}
    </Svg>
  );
}

export default function NearbyScreen({ navigation, route }: any) {
  const [query, setQuery] = useState('');
  const [filter, setFilter] = useState<'봉사' | '선행'>('봉사');
  const [pin, setPin] = useState<Pin | null>(null);

  const searching = query.trim().length > 0;
  const chips: Array<'봉사' | '선행'> = ['봉사', '선행'];

  return (
    <View style={styles.root}>
      <StatusBar style="light" />
      <HazeBackground />
      <MainHeader showBack title={searching ? '지역 검색' : '내 주변 둘러보기'} />

      {/* 검색 + 필터 */}
      <View style={styles.searchWrap}>
        <GdqInput
          value={query}
          onChangeText={setQuery}
          placeholder="주소 검색..."
          leftIcon={<SearchIcon />}
          style={styles.searchInput}
          returnKeyType="search"
        />
        <View style={styles.chipRow}>
          {chips.map((c) => {
            const on = filter === c;
            return (
              <Pressable key={c} onPress={() => setFilter(c)} style={[styles.chip, on ? styles.chipOn : styles.chipOff]}>
                <Text style={[styles.chipText, { color: on ? colors.white : colors.primaryDark }]}>{c}</Text>
              </Pressable>
            );
          })}
        </View>
      </View>

      {searching ? (
        /* ── 지역 검색 결과 ── */
        <ScrollView style={styles.results} showsVerticalScrollIndicator={false}>
          {RESULTS.filter((r) => r.addr.includes(query.trim())).length === 0 ? (
            <View style={styles.empty}>
              <Text style={styles.emptyText}>검색 결과가 없습니다</Text>
            </View>
          ) : (
            RESULTS.filter((r) => r.addr.includes(query.trim())).map((r, i) => (
              <Animated.View key={r.addr} entering={FadeInDown.delay(i * 50).duration(360)}>
                <Pressable
                  style={({ pressed }) => [styles.resultRow, pressed && styles.rowPressed]}
                  onPress={() => setQuery('')}
                >
                  <PinDot size={18} />
                  <Text style={styles.resultAddr}>{r.addr}</Text>
                  <Text style={styles.resultKind}>{r.kind}</Text>
                </Pressable>
              </Animated.View>
            ))
          )}
        </ScrollView>
      ) : (
        /* ── Kakao 3km 지도 ── */
        <View style={styles.mapArea}>
          <LinearGradient colors={[MAP.canvasA, MAP.canvasB]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={StyleSheet.absoluteFill} />
          <MapGrid />

          {/* 내 위치 */}
          <View style={styles.myRing} />
          <PulseRing color={MAP.myRing} size={22} style={{ left: '50%', top: '52%', marginLeft: -11, marginTop: -11 }} />
          <View style={styles.myDot} />

          {/* 봉사 핀 */}
          {PINS.map((p) => (
            <Pressable key={p.name} style={[styles.pinBtn, { left: p.left as any, top: p.top as any }]} hitSlop={8} onPress={() => setPin(p)}>
              <MapPinIcon size={30} />
            </Pressable>
          ))}

          <View style={styles.kakaoChip}>
            <Text style={styles.kakaoText}>Kakao Map · 3km 반경</Text>
          </View>
        </View>
      )}

      {/* 핀 간략정보 바텀시트 */}
      <BottomSheet visible={!!pin} onClose={() => setPin(null)}>
        {pin ? (
          <View>
            <View style={styles.sheetHead}>
              <Text style={styles.sheetName}>{pin.name}</Text>
              <Text style={styles.sheetDist}>{pin.dist}</Text>
            </View>
            <Text style={styles.sheetAddr}>{pin.addr}</Text>
            <SpringButton
              style={styles.sheetBtn}
              onPress={() => {
                const item = pin;
                setPin(null);
                navigation.navigate('VolunteerDetail', { item });
              }}
            >
              <Text style={styles.sheetBtnText}>상세정보 보기</Text>
            </SpringButton>
          </View>
        ) : null}
      </BottomSheet>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.screenBg },
  searchWrap: { paddingHorizontal: 16, paddingTop: 14, paddingBottom: 10 },
  searchInput: { fontSize: 14 },
  chipRow: { flexDirection: 'row', gap: 8, marginTop: 12 },
  chip: { borderRadius: 16, paddingHorizontal: 16, paddingVertical: 6 },
  chipOn: { backgroundColor: colors.primaryDark },
  chipOff: { backgroundColor: colors.screenBg, borderWidth: 1, borderColor: colors.pixelBorder },
  chipText: { fontSize: 13, fontWeight: '700', fontFamily: fonts.bodyB },
  /* results */
  results: { flex: 1, backgroundColor: colors.white },
  resultRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: '#E0E0E0',
  },
  rowPressed: { backgroundColor: '#F4F9F5' },
  resultAddr: { flex: 1, fontSize: 14, color: colors.primaryDark, fontFamily: fonts.bodyR },
  resultKind: {
    fontSize: 11,
    fontWeight: '700',
    color: colors.xpGreen,
    backgroundColor: '#EAF6EC',
    borderRadius: 8,
    paddingHorizontal: 8,
    paddingVertical: 2,
    overflow: 'hidden',
    fontFamily: fonts.bodyB,
  },
  empty: { alignItems: 'center', justifyContent: 'center', paddingVertical: 60 },
  emptyText: { fontSize: 14, color: colors.textMuted, fontFamily: fonts.bodyR },
  /* map */
  mapArea: {
    flex: 1,
    marginHorizontal: 16,
    marginBottom: 16,
    borderWidth: 1.5,
    borderColor: colors.pixelBorder,
    borderRadius: radii.chip,
    overflow: 'hidden',
  },
  myRing: {
    position: 'absolute',
    left: '50%',
    top: '52%',
    width: 64,
    height: 64,
    marginLeft: -32,
    marginTop: -32,
    borderRadius: 32,
    backgroundColor: 'rgba(91,155,213,0.25)',
    borderWidth: 2,
    borderColor: MAP.myRing,
  },
  myDot: {
    position: 'absolute',
    left: '50%',
    top: '52%',
    width: 14,
    height: 14,
    marginLeft: -7,
    marginTop: -7,
    borderRadius: 7,
    backgroundColor: MAP.myRing,
    borderWidth: 2,
    borderColor: colors.white,
  },
  pinBtn: { position: 'absolute', marginLeft: -15, marginTop: -30 },
  kakaoChip: {
    position: 'absolute',
    bottom: 10,
    alignSelf: 'center',
    backgroundColor: 'rgba(255,255,255,0.85)',
    borderRadius: 12,
    paddingHorizontal: 10,
    paddingVertical: 3,
  },
  kakaoText: { fontSize: 11, color: '#5B6B60', fontFamily: fonts.bodyR },
  /* sheet */
  sheetHead: { flexDirection: 'row', alignItems: 'baseline', justifyContent: 'space-between', marginBottom: 6 },
  sheetName: { fontFamily: fonts.pixel, fontSize: 16, color: colors.primaryDark },
  sheetDist: { fontSize: 13, fontWeight: '700', color: colors.primaryDark, fontFamily: fonts.bodyB },
  sheetAddr: { fontSize: 13, color: '#666', marginBottom: 16, fontFamily: fonts.bodyR },
  sheetBtn: { height: 46, borderRadius: 10, backgroundColor: colors.primaryDark, alignItems: 'center', justifyContent: 'center' },
  sheetBtnText: { fontFamily: fonts.pixel, fontSize: 15, color: colors.parchment },
});
