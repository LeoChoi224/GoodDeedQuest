/**
 * SCREEN 05·5+6+7 · 내 주변 둘러보기 + 장소 검색 + 핀 클릭 간략정보.
 * 실제 GPS 위치(expo-location) + 카카오맵(WebView, KakaoMapView) + /map/volunteer-centers 실API.
 * 이 화면에 들어올 때마다 GPS를 새로 읽어서 지도 표시용으로 쓰는 동시에
 * /auth/me/location으로 서버에도 저장함(User.current_latitude/current_longitude, 주기적 갱신은 안 함).
 * /map/volunteer-centers는 "봉사센터" 단위가 아니라 VMS 모집공고 단위(같은 기관에 모집글이 여러 개면
 * 행도 여러 개)라서, 같은 이름+주소(없으면 좌표)를 하나의 장소로 묶어 마커/리스트를 중복 없이 보여줌.
 * 한 장소에 활동이 여러 건이면 상세정보 화면에서 전부 카드로 나열함.
 * 지도(고정 높이) 아래에 3km 이내 리스트를 보여줌 - 리스트 항목 탭하면 마커 탭과 동일하게 바텀시트가 뜨고,
 * 지도가 그 장소로 이동(panTo)하며, 화면도 지도가 보이도록 위로 스크롤됨.
 * 검색: 타이핑할 때마다(300ms 디바운스) 카카오 로컬 검색 REST API(kakaoLocal.ts)로 후보를 여러 개
 * 받아 검색창 아래 드롭다운으로 보여주고, 사용자가 직접 하나를 선택함 - 예전처럼 "1등 결과로
 * 무조건 이동"하지 않음. 선택하면 그 좌표로 지도 이동 + /map/volunteer-centers 재조회.
 * 후보 선택 시 setQuery()로 입력창 텍스트를 바꾸는데, 이게 다시 디바운스 검색을 트리거해서
 * 드롭다운이 재등장하는 버그가 있었음 - suppressNextSearchRef로 그 한 번만 재검색을 건너뜀.
 * 내 실제 위치(빨간 점)는 검색해도 유지되고, 지도 우하단 현위치 버튼으로 되돌아갈 수 있음.
 */
import React, { useEffect, useMemo, useState, useCallback, useRef } from 'react';
import { View, Text, StyleSheet, Pressable, ActivityIndicator, ScrollView } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import * as Location from 'expo-location';
import Svg, { Path, Circle } from 'react-native-svg';
import Animated, { FadeInDown } from 'react-native-reanimated';
import { colors, fonts, radii, shadow } from '../../theme';
import HazeBackground from '../../components/HazeBackground';
import MainHeader from '../../components/MainHeader';
import GdqInput from '../../components/GdqInput';
import BottomSheet from '../../components/BottomSheet';
import SpringButton from '../../components/SpringButton';
import KakaoMapView, { KakaoMapViewHandle, MapMarker } from '../../components/KakaoMapView';
import { SearchIcon, PinDot } from './_parts';
import { getNearbyVolunteerCenters, VolunteerCenter } from '../../api/map';
import { searchKakaoPlaces, KakaoPlace } from '../../api/kakaoLocal';
import { updateMyLocation } from '../../api/auth';

const RADIUS_KM = 3;
const MAP_HEIGHT = 340;
const SEARCH_DEBOUNCE_MS = 300;

function toRad(deg: number) {
  return (deg * Math.PI) / 180;
}

function distanceKm(lat1: number, lng1: number, lat2: number, lng2: number) {
  const R = 6371;
  const dLat = toRad(lat2 - lat1);
  const dLng = toRad(lng2 - lng1);
  const a = Math.sin(dLat / 2) ** 2 + Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLng / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

function formatDist(km: number) {
  return km < 1 ? `${Math.round(km * 1000)}m` : `${km.toFixed(1)}km`;
}

// 지도 우하단 "현위치로 이동" FAB 아이콘 (크로스헤어)
function LocateIcon({ size = 20, color = colors.primaryDark }: { size?: number; color?: string }) {
  return (
    <Svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={2} strokeLinecap="round">
      <Circle cx={12} cy={12} r={3.5} />
      <Path d="M12 2v3M12 19v3M2 12h3M19 12h3" />
    </Svg>
  );
}

// 같은 기관(이름+주소, 없으면 좌표)의 모집공고를 하나의 장소로 묶은 단위
type LocationGroup = {
  key: string;
  vol_name: string | null;
  vol_address: string | null;
  latitude: number;
  longitude: number;
  distKm: number;
  activities: VolunteerCenter[];
};
type LatLng = { lat: number; lng: number };

function groupCenters(centers: VolunteerCenter[], mapCenter: LatLng): LocationGroup[] {
  const map = new Map<string, { vol_name: string | null; vol_address: string | null; latitude: number; longitude: number; activities: VolunteerCenter[] }>();

  centers.forEach((c) => {
    if (c.latitude == null || c.longitude == null) return;
    const key =
      c.vol_name && c.vol_address
        ? `${c.vol_name}__${c.vol_address}`
        : `${c.latitude.toFixed(5)}_${c.longitude.toFixed(5)}`;
    const existing = map.get(key);
    if (existing) {
      existing.activities.push(c);
    } else {
      map.set(key, { vol_name: c.vol_name, vol_address: c.vol_address, latitude: c.latitude, longitude: c.longitude, activities: [c] });
    }
  });

  return Array.from(map.entries())
    .map(([key, g]) => ({
      key,
      ...g,
      distKm: distanceKm(mapCenter.lat, mapCenter.lng, g.latitude, g.longitude),
    }))
    .sort((a, b) => a.distKm - b.distKm);
}

export default function NearbyScreen({ navigation, route }: any) {
  const mapRef = useRef<KakaoMapViewHandle>(null);
  const scrollRef = useRef<ScrollView>(null);
  // handleSelectSuggestion에서 setQuery()로 텍스트를 바꿀 때는 재검색(디바운스 이펙트)을 건너뛰기 위한 플래그
  const suppressNextSearchRef = useRef(false);

  const [query, setQuery] = useState('');
  const [pin, setPin] = useState<(LocationGroup & { dist: string }) | null>(null);

  // 검색 자동완성 드롭다운
  const [suggestions, setSuggestions] = useState<KakaoPlace[]>([]);
  const [searching, setSearching] = useState(false);
  const [suggestNoResults, setSuggestNoResults] = useState(false);

  const [myLoc, setMyLoc] = useState<LatLng | null>(null);
  const [mapCenter, setMapCenter] = useState<LatLng | null>(null);
  const [placeName, setPlaceName] = useState<string | null>(null);
  const [locError, setLocError] = useState<string | null>(null);
  const [centers, setCenters] = useState<VolunteerCenter[]>([]);
  const [loading, setLoading] = useState(true);

  const loadCentersAt = useCallback(async (center: LatLng) => {
    const result = await getNearbyVolunteerCenters(center.lat, center.lng, RADIUS_KM);
    setCenters(result.filter((c) => c.latitude != null && c.longitude != null));
  }, []);

  const initLocation = useCallback(async () => {
    setLoading(true);
    setLocError(null);
    try {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') {
        setLocError('위치 권한이 없으면 주변 봉사 시설을 찾을 수 없어요. 설정에서 위치 권한을 허용해주세요.');
        setLoading(false);
        return;
      }
      const pos = await Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.Balanced });
      const loc = { lat: pos.coords.latitude, lng: pos.coords.longitude };
      setMyLoc(loc);
      setMapCenter(loc);

      // 서버에도 최근 위치 저장 - 실패해도 지도/검색은 정상 동작해야 하니 별도로 감싸서 무시
      updateMyLocation(loc.lat, loc.lng).catch(() => {});

      await loadCentersAt(loc);
    } catch (err: any) {
      setLocError(err.message ?? '위치 정보를 가져오지 못했습니다.');
    } finally {
      setLoading(false);
    }
  }, [loadCentersAt]);

  useEffect(() => {
    initLocation();
  }, [initLocation]);

  // 검색어가 바뀔 때마다 300ms 뒤에 자동완성 후보 조회 (연타 방지 디바운스)
  // suppressNextSearchRef가 true면 방금 사용자가 후보를 "선택"해서 query가 프로그램적으로 바뀐 것이므로
  // 재검색하지 않고 드롭다운만 닫음 (안 그러면 선택한 장소명으로 다시 검색이 돌면서 드롭다운이 또 뜸)
  useEffect(() => {
    const q = query.trim();
    if (suppressNextSearchRef.current) {
      suppressNextSearchRef.current = false;
      setSuggestions([]);
      setSuggestNoResults(false);
      setSearching(false);
      return;
    }
    if (!q) {
      setSuggestions([]);
      setSuggestNoResults(false);
      setSearching(false);
      return;
    }
    setSearching(true);
    const timer = setTimeout(async () => {
      try {
        const results = await searchKakaoPlaces(q);
        setSuggestions(results);
        setSuggestNoResults(results.length === 0);
      } catch {
        setSuggestions([]);
        setSuggestNoResults(true);
      } finally {
        setSearching(false);
      }
    }, SEARCH_DEBOUNCE_MS);
    return () => clearTimeout(timer);
  }, [query]);

  const groups: LocationGroup[] = useMemo(() => {
    if (!mapCenter) return [];
    return groupCenters(centers, mapCenter);
  }, [centers, mapCenter]);

  const markers: MapMarker[] = useMemo(
    () => groups.map((g) => ({ id: g.key, lat: g.latitude, lng: g.longitude })),
    [groups]
  );

  const openGroup = (group: LocationGroup) => {
    setPin({ ...group, dist: formatDist(group.distKm) });
  };

  const handleMarkerPress = (id: string) => {
    const found = groups.find((g) => g.key === id);
    if (found) openGroup(found);
  };

  const handleListItemPress = (group: LocationGroup) => {
    openGroup(group);
    mapRef.current?.panTo(group.latitude, group.longitude);
    scrollRef.current?.scrollTo({ y: 0, animated: true });
  };

  const moveToPlace = useCallback(
    async (place: KakaoPlace) => {
      setSuggestions([]);
      setSuggestNoResults(false);
      setPlaceName(place.placeName);
      const center = { lat: place.lat, lng: place.lng };
      setMapCenter(center);
      setLoading(true);
      try {
        await loadCentersAt(center);
      } finally {
        setLoading(false);
      }
    },
    [loadCentersAt]
  );

  const handleSelectSuggestion = (place: KakaoPlace) => {
    suppressNextSearchRef.current = true;
    setQuery(place.placeName);
    moveToPlace(place);
  };

  // 엔터/검색 키 - 후보가 떠 있으면 그중 첫 번째로 이동(직접 목록에서 고르는 걸 기본 흐름으로 유도)
  const handleSubmitSearch = () => {
    if (suggestions.length > 0) {
      handleSelectSuggestion(suggestions[0]);
    }
  };

  const handleBackToMyLocation = () => {
    if (!myLoc) return;
    setPlaceName(null);
    setQuery('');
    setMapCenter(myLoc);
    // 상태 변경으로 인한 리마운트만 믿지 않고, 이미 떠 있는 지도 인스턴스에도 직접 이동 명령
    mapRef.current?.panTo(myLoc.lat, myLoc.lng);
    setLoading(true);
    loadCentersAt(myLoc).finally(() => setLoading(false));
  };

  return (
    <View style={styles.root}>
      <StatusBar style="light" />
      <HazeBackground />
      <MainHeader showBack title={placeName ? `'${placeName}' 주변` : '내 주변 둘러보기'} />

      {/* 검색 + 자동완성 드롭다운 */}
      <View style={styles.searchWrap}>
        <GdqInput
          value={query}
          onChangeText={setQuery}
          onSubmitEditing={handleSubmitSearch}
          placeholder="장소 검색 (예: 강남역, OO복지관)"
          leftIcon={<SearchIcon />}
          style={styles.searchInput}
          returnKeyType="search"
        />
        {searching || suggestions.length > 0 || suggestNoResults ? (
          <View style={styles.suggestBox}>
            {searching ? (
              <View style={styles.suggestLoading}>
                <ActivityIndicator size="small" color={colors.primaryDark} />
              </View>
            ) : suggestions.length > 0 ? (
              <ScrollView keyboardShouldPersistTaps="handled" style={styles.suggestList} nestedScrollEnabled>
                {suggestions.map((s, i) => (
                  <Pressable
                    key={s.id}
                    style={({ pressed }) => [
                      styles.suggestRow,
                      i === suggestions.length - 1 && { borderBottomWidth: 0 },
                      pressed && styles.suggestRowPressed,
                    ]}
                    onPress={() => handleSelectSuggestion(s)}
                  >
                    <SearchIcon size={14} color={colors.textMuted} />
                    <View style={{ flex: 1 }}>
                      <Text style={styles.suggestName} numberOfLines={1}>{s.placeName}</Text>
                      <Text style={styles.suggestAddr} numberOfLines={1}>{s.roadAddressName || s.addressName}</Text>
                    </View>
                  </Pressable>
                ))}
              </ScrollView>
            ) : (
              <Text style={styles.suggestEmpty}>'{query}' 검색 결과가 없어요.</Text>
            )}
          </View>
        ) : null}
      </View>

      <ScrollView ref={scrollRef} contentContainerStyle={styles.body} showsVerticalScrollIndicator={false}>
        {/* Kakao 3km 지도 - 고정 높이 */}
        <View style={styles.mapArea}>
          {loading ? (
            <View style={styles.centerBox}>
              <ActivityIndicator color={colors.primaryDark} />
            </View>
          ) : locError ? (
            <View style={styles.centerBox}>
              <Text style={styles.errorText}>{locError}</Text>
              <SpringButton style={styles.retryBtn} onPress={initLocation}>
                <Text style={styles.retryText}>다시 시도</Text>
              </SpringButton>
            </View>
          ) : mapCenter ? (
            <>
              <KakaoMapView
                ref={mapRef}
                latitude={mapCenter.lat}
                longitude={mapCenter.lng}
                myLocation={myLoc}
                showSearchMarker={!!placeName}
                radiusKm={RADIUS_KM}
                markers={markers}
                onMarkerPress={handleMarkerPress}
              />
              <View style={styles.kakaoChip}>
                <Text style={styles.kakaoText}>Kakao Map · {RADIUS_KM}km 반경 · {groups.length}곳</Text>
              </View>
              {myLoc ? (
                <Pressable
                  onPress={handleBackToMyLocation}
                  style={({ pressed }) => [styles.locateFab, pressed && styles.locateFabPressed]}
                  hitSlop={8}
                >
                  <LocateIcon />
                </Pressable>
              ) : null}
            </>
          ) : null}
        </View>

        {/* 지도 아래 리스트 */}
        {!loading && !locError && (
          <>
            <Text style={styles.sectionTitle}>📍 {RADIUS_KM}km 이내 봉사시설 ({groups.length})</Text>
            {groups.length === 0 ? (
              <View style={styles.emptyList}>
                <Text style={styles.emptyText}>주변에 봉사시설이 없어요.</Text>
              </View>
            ) : (
              <View style={styles.listCard}>
                {groups.map((g, i) => (
                  <Animated.View key={g.key} entering={FadeInDown.delay(i * 40).duration(300)}>
                    <Pressable
                      style={({ pressed }) => [styles.resultRow, pressed && styles.rowPressed]}
                      onPress={() => handleListItemPress(g)}
                    >
                      <PinDot size={18} />
                      <View style={{ flex: 1 }}>
                        <View style={styles.resultNameRow}>
                          <Text style={styles.resultName}>{g.vol_name ?? '이름 미상'}</Text>
                          {g.activities.length > 1 ? (
                            <View style={styles.countBadge}>
                              <Text style={styles.countBadgeText}>{g.activities.length}건</Text>
                            </View>
                          ) : null}
                        </View>
                        <Text style={styles.resultAddr}>{g.vol_address ?? '주소 정보 없음'}</Text>
                      </View>
                      <Text style={styles.resultDist}>{formatDist(g.distKm)}</Text>
                    </Pressable>
                  </Animated.View>
                ))}
              </View>
            )}
          </>
        )}
      </ScrollView>

      {/* 핀 간략정보 바텀시트 */}
      <BottomSheet visible={!!pin} onClose={() => setPin(null)}>
        {pin ? (
          <View>
            <View style={styles.sheetHead}>
              <Text style={styles.sheetName}>{pin.vol_name ?? '이름 미상'}</Text>
              <Text style={styles.sheetDist}>{pin.dist}</Text>
            </View>
            <Text style={styles.sheetAddr}>{pin.vol_address ?? '주소 정보 없음'}</Text>
            {pin.activities.length > 1 ? (
              <Text style={styles.sheetCount}>모집 중인 봉사 {pin.activities.length}건</Text>
            ) : null}
            <SpringButton
              style={styles.sheetBtn}
              onPress={() => {
                const activities = pin.activities;
                const place = pin.vol_name;
                const address = pin.vol_address;
                const latitude = pin.latitude;
                const longitude = pin.longitude;
                setPin(null);
                navigation.navigate('VolunteerDetail', { items: activities, place, address, latitude, longitude });
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
  searchWrap: { paddingHorizontal: 16, paddingTop: 14, paddingBottom: 10, zIndex: 100, elevation: 6 },
  searchInput: { fontSize: 14 },
  suggestBox: {
    position: 'absolute',
    top: 54,
    left: 16,
    right: 16,
    backgroundColor: colors.white,
    borderRadius: radii.chip,
    borderWidth: 1,
    borderColor: colors.inputBorder,
    overflow: 'hidden',
    zIndex: 100,
    elevation: 8,
    ...shadow.card,
  },
  suggestList: { maxHeight: 260 },
  suggestLoading: { paddingVertical: 16, alignItems: 'center' },
  suggestRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    paddingHorizontal: 14,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#F0F0F0',
  },
  suggestRowPressed: { backgroundColor: '#F4F9F5' },
  suggestName: { fontSize: 14, fontWeight: '700', color: colors.primaryDark, fontFamily: fonts.bodyB, marginBottom: 2 },
  suggestAddr: { fontSize: 12, color: '#888', fontFamily: fonts.bodyR },
  suggestEmpty: { fontSize: 13, color: colors.textMuted, fontFamily: fonts.bodyR, paddingVertical: 14, paddingHorizontal: 14, textAlign: 'center' },
  emptyList: { paddingVertical: 24, alignItems: 'center' },
  emptyText: { fontSize: 14, color: colors.textMuted, fontFamily: fonts.bodyR, textAlign: 'center' },
  body: { paddingHorizontal: 16, paddingBottom: 32 },
  mapArea: {
    height: MAP_HEIGHT,
    marginBottom: 16,
    borderWidth: 1.5,
    borderColor: colors.pixelBorder,
    borderRadius: radii.chip,
    overflow: 'hidden',
  },
  centerBox: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 12, padding: 24 },
  errorText: { fontSize: 13, color: colors.textSecondary, fontFamily: fonts.bodyR, textAlign: 'center' },
  retryBtn: { height: 40, borderRadius: 8, backgroundColor: colors.primaryDark, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 20 },
  retryText: { fontFamily: fonts.pixel, fontSize: 13, color: colors.parchment },
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
  locateFab: {
    position: 'absolute',
    bottom: 10,
    right: 10,
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: colors.white,
    borderWidth: 1.5,
    borderColor: colors.pixelBorder,
    alignItems: 'center',
    justifyContent: 'center',
    ...shadow.card,
    zIndex: 20,
    elevation: 20,
  },
  locateFabPressed: { backgroundColor: '#F0F0F0' },
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
  resultNameRow: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  resultName: { fontSize: 14, fontWeight: '700', color: colors.primaryDark, fontFamily: fonts.bodyB, marginBottom: 2 },
  resultAddr: { fontSize: 12, color: '#888', fontFamily: fonts.bodyR },
  resultDist: { fontSize: 13, fontWeight: '700', color: colors.gold, fontFamily: fonts.bodyB },
  countBadge: { backgroundColor: '#FDF1DA', borderRadius: 8, paddingHorizontal: 6, paddingVertical: 1 },
  countBadgeText: { fontSize: 10, fontWeight: '700', color: colors.gold, fontFamily: fonts.bodyB },
  sheetHead: { flexDirection: 'row', alignItems: 'baseline', justifyContent: 'space-between', marginBottom: 6 },
  sheetName: { fontFamily: fonts.pixel, fontSize: 16, color: colors.primaryDark },
  sheetDist: { fontSize: 13, fontWeight: '700', color: colors.primaryDark, fontFamily: fonts.bodyB },
  sheetAddr: { fontSize: 13, color: '#666', marginBottom: 4, fontFamily: fonts.bodyR },
  sheetCount: { fontSize: 12, color: colors.gold, fontWeight: '700', marginBottom: 16, fontFamily: fonts.bodyB },
  sheetBtn: { height: 46, borderRadius: 10, backgroundColor: colors.primaryDark, alignItems: 'center', justifyContent: 'center' },
  sheetBtnText: { fontFamily: fonts.pixel, fontSize: 15, color: colors.parchment },
});