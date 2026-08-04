/**
 * SCREEN 05·9 · 봉사활동 상세정보.
 * VolSearchScreen에서 { items: VolunteerCenter[], place, address, latitude, longitude } 형태로 넘어옴
 * (실데이터, 같은 기관에 모집공고가 여러 건이면 items에 전부 담겨서 옴 - 카드로 전부 나열).
 * RegionDetailsScreen의 "추천 봉사시설" 카드는 아직 { item: { name, sub, centerId } } 축약 형태로
 * 넘어오는데(주소/좌표/활동 상세가 없음), 그 경로도 안 깨지게 함께 처리 - 좌표가 없으면 지도 대신
 * 장식용 그리드를 보여줌.
 * 위치 핀은 VolSearchScreen과 동일한 봉사센터 마커 이미지(KakaoMapView의 CustomOverlay)를 사용함
 * - 지도 중앙에 RN 아이콘을 고정 오버레이하던 이전 방식은 확대/이동 시 어긋나서 실제 좌표 마커로 교체.
 * 카드별로 vms_url이 있으면 "신청하기"가 외부 VMS로 연결, 없으면 안내 토스트.
 * 자격요건은 "/"로 구분된 원본 텍스트를 줄바꿈으로 바꿔서 표시(가독성).
 * ⭐ 수정: 카드마다 "퀘스트 시작" 버튼 추가 — AI 추천을 거치지 않고 지도에서 바로 이 공고를
 * 퀘스트로 변환(없으면 생성, 있으면 재사용) + 즉시 시작까지 한 번에 처리하고 QuestDetail로 이동.
 */
import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, Pressable, Linking, ActivityIndicator } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { LinearGradient } from 'expo-linear-gradient';
import Svg, { Line } from 'react-native-svg';
import { colors, fonts, radii, shadow } from '../../theme';
import HazeBackground from '../../components/HazeBackground';
import MainHeader from '../../components/MainHeader';
import { useToast } from '../../components/Toast';
import KakaoMapView from '../../components/KakaoMapView';
import { MapPinIcon, MAP } from './_parts';
import { getOrCreateQuestFromVolunteerCenter, startQuest } from '../../api/quest'; // ⭐ 수정

function DetailGrid() {
  return (
    <Svg style={StyleSheet.absoluteFill} width="100%" height="100%" viewBox="0 0 300 180" preserveAspectRatio="none">
      {Array.from({ length: 10 }).map((_, i) => (
        <Line key={`v${i}`} x1={i * 34} y1={0} x2={i * 34} y2={180} stroke={MAP.grid} strokeWidth={0.6} />
      ))}
      {Array.from({ length: 6 }).map((_, i) => (
        <Line key={`h${i}`} x1={0} y1={i * 34} x2={300} y2={i * 34} stroke={MAP.grid} strokeWidth={0.6} />
      ))}
    </Svg>
  );
}

// VolSearchScreen(실데이터: vol_*) / RegionDetailsScreen(축약: name/sub) 둘 다 받을 수 있게 느슨한 타입 사용
type RawItem = {
  center_id?: number;
  vol_name?: string | null;
  vol_title?: string | null;
  vol_address?: string | null;
  target?: string | null;
  vol_qual?: string | null;
  vol_act?: string | null;
  vol_date?: string | null;
  vms_url?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  // RegionDetailsScreen 추천 카드 축약 형태
  name?: string;
  sub?: string;
  centerId?: number;
};

const FALLBACK = '정보 없음';

// "만 19세 이상/성별무관/차량가능자" 같은 "/" 구분 텍스트를 줄바꿈으로 - 자격요건이 한 줄로 붙어 있으면 읽기 불편해서
function formatQual(text: string | null | undefined): string {
  if (!text) return FALLBACK;
  return text
    .split('/')
    .map((s) => s.trim())
    .filter(Boolean)
    .join('\n');
}

export default function VolunteerDetailScreen({ navigation, route }: any) {
  const toast = useToast();
  const paramItems: RawItem[] | undefined = route?.params?.items;
  const singleItem: RawItem | undefined = route?.params?.item;
  const items: RawItem[] = paramItems && paramItems.length > 0 ? paramItems : singleItem ? [singleItem] : [];

  const place: string = route?.params?.place ?? items[0]?.vol_name ?? items[0]?.name ?? '이름 미상';
  const address: string | null = route?.params?.address ?? items[0]?.vol_address ?? items[0]?.sub ?? null;
  const latitude: number | null = route?.params?.latitude ?? items[0]?.latitude ?? null;
  const longitude: number | null = route?.params?.longitude ?? items[0]?.longitude ?? null;

  // ⭐ 수정: 카드별로 "퀘스트 시작" 처리 중인지 표시할 상태 (center_id 기준)
  const [startingCenterId, setStartingCenterId] = useState<number | null>(null);

  const handleApply = (vmsUrl?: string | null) => {
    if (!vmsUrl) {
      toast.show('연결된 신청 페이지가 없어요.');
      return;
    }
    Linking.openURL(vmsUrl).catch(() => toast.show('신청 페이지를 여는 데 실패했어요.'));
  };

  // ⭐ 수정: 지도에서 바로 퀘스트 시작 — 변환(또는 재사용) + 즉시 시작까지 한 번에 처리
  const handleStartQuest = async (centerId?: number) => {
    if (!centerId || startingCenterId != null) return;
    setStartingCenterId(centerId);
    try {
      const quest = await getOrCreateQuestFromVolunteerCenter(centerId);
      await startQuest(quest.quest_id);
      navigation.navigate('QuestDetail', {
        questId: quest.quest_id,
        volunteerCenterId: quest.volunteer_center_id,
        questType: quest.quest_type,
        title: quest.quest_title,
        category: quest.category_code,
        desc: quest.quest_description,
        point: quest.reward_point ?? 0,
        exp: quest.reward_exp ?? 0,
        active: true,
      });
    } catch (err) {
      toast.show('퀘스트를 시작하지 못했어요.');
    } finally {
      setStartingCenterId(null);
    }
  };

  return (
    <View style={styles.root}>
      <StatusBar style="light" />
      <HazeBackground />
      <MainHeader showBack title="봉사활동 상세" />

      <ScrollView contentContainerStyle={styles.body} showsVerticalScrollIndicator={false}>
        {/* 위치 지도 - 좌표가 있으면 실제 카카오맵 + 봉사센터 핀마커, 없으면(추천 시설 카드 경로 등) 장식용 그리드 */}
        <View style={styles.mapBox}>
          {latitude != null && longitude != null ? (
            <KakaoMapView
              latitude={latitude}
              longitude={longitude}
              radiusKm={0}
              level={4}
              markers={[{ id: 'detail-pin', lat: latitude, lng: longitude }]}
            />
          ) : (
            <>
              <LinearGradient colors={[MAP.canvasA, MAP.canvasB]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={StyleSheet.absoluteFill} />
              <DetailGrid />
              <View style={styles.pinCenter}>
                <MapPinIcon size={40} />
              </View>
            </>
          )}
        </View>

        <Text style={styles.place}>{place}</Text>
        {address ? <Text style={styles.address}>{address}</Text> : null}

        {items.length === 0 ? (
          <View style={styles.emptyBox}>
            <Text style={styles.emptyText}>표시할 봉사 정보가 없어요.</Text>
          </View>
        ) : (
          items.map((it, i) => {
            const centerId = it.center_id ?? it.centerId;
            const starting = startingCenterId === centerId;
            const rows = [
              { label: '활동기간', value: it.vol_date ?? FALLBACK },
              { label: '봉사장소', value: it.vol_address ?? it.sub ?? address ?? FALLBACK },
              { label: '봉사대상', value: it.target ?? FALLBACK },
              { label: '자격요건', value: formatQual(it.vol_qual) },
              { label: '활동설명', value: it.vol_act ?? FALLBACK },
            ];
            return (
              <View key={centerId ?? i} style={styles.card}>
                {items.length > 1 ? (
                  <Text style={styles.cardTitle}>{it.vol_title ? it.vol_title : `모집 ${i + 1}`}</Text>
                ) : it.vol_title ? (
                  <Text style={styles.cardTitle}>{it.vol_title}</Text>
                ) : null}
                {rows.map((r, ri) => (
                  <View key={r.label} style={[styles.row, ri === rows.length - 1 && { borderBottomWidth: 0 }]}>
                    <Text style={styles.label}>{r.label}</Text>
                    <Text style={styles.value}>{r.value}</Text>
                  </View>
                ))}
                {/* ⭐ 수정: 신청하기(외부 VMS) / 퀘스트 시작(앱 내) 2분할 */}
                <View style={styles.btnRow}>
                  <Pressable
                    onPress={() => handleApply(it.vms_url)}
                    style={({ pressed }) => [styles.applyBtn, styles.btnHalf, pressed && { transform: [{ scale: 0.97 }] }]}
                  >
                    <Text style={styles.applyText}>{it.vms_url ? '신청하기' : '신청 페이지 없음'}</Text>
                  </Pressable>
                  <Pressable
                    onPress={() => handleStartQuest(centerId)}
                    disabled={!centerId || starting}
                    style={({ pressed }) => [
                      styles.startBtn, styles.btnHalf,
                      (!centerId || starting) && { opacity: 0.6 },
                      pressed && { transform: [{ scale: 0.97 }] },
                    ]}
                  >
                    {starting ? (
                      <ActivityIndicator color={colors.parchment} size="small" />
                    ) : (
                      <Text style={styles.startText}>퀘스트 시작</Text>
                    )}
                  </Pressable>
                </View>
              </View>
            );
          })
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.screenBg },
  body: { padding: 16, paddingBottom: 32 },
  mapBox: {
    height: 180,
    borderRadius: radii.chip,
    overflow: 'hidden',
    borderWidth: 1.5,
    borderColor: colors.pixelBorder,
    marginBottom: 16,
  },
  pinCenter: { position: 'absolute', left: '50%', top: '44%', marginLeft: -20, marginTop: -20 },
  place: { fontFamily: fonts.pixel, fontSize: 17, color: colors.primaryDark, marginBottom: 4 },
  address: { fontSize: 13, color: colors.textSecondary, fontFamily: fonts.bodyR, marginBottom: 16 },
  emptyBox: { paddingVertical: 40, alignItems: 'center' },
  emptyText: { fontSize: 14, color: colors.textMuted, fontFamily: fonts.bodyR },
  card: {
    backgroundColor: colors.parchment,
    borderWidth: 1.5,
    borderColor: colors.pixelBorder,
    borderRadius: radii.chip,
    paddingHorizontal: 16,
    paddingTop: 12,
    paddingBottom: 16,
    marginBottom: 14,
    ...shadow.card,
  },
  cardTitle: { fontFamily: fonts.pixel, fontSize: 14, color: colors.gold, marginBottom: 6 },
  row: { flexDirection: 'row', gap: 12, paddingVertical: 9, borderBottomWidth: 1, borderBottomColor: '#EFE6CC' },
  label: { width: 64, fontFamily: fonts.pixel, fontSize: 13, color: colors.gold },
  value: { flex: 1, fontSize: 14, color: colors.primaryDark, lineHeight: 21, fontFamily: fonts.bodyR },
  // ⭐ 수정: 기존 applyBtn(단독, height 46)을 btnRow 안 2분할로 변경
  btnRow: { flexDirection: 'row', gap: 10, marginTop: 12 },
  btnHalf: { flex: 1 },
  applyBtn: {
    height: 46,
    borderRadius: 8,
    backgroundColor: colors.gold,
    alignItems: 'center',
    justifyContent: 'center',
  },
  applyText: { fontFamily: fonts.pixel, fontSize: 14, color: colors.primaryDark },
  startBtn: {
    height: 46,
    borderRadius: 8,
    backgroundColor: colors.primaryDark,
    alignItems: 'center',
    justifyContent: 'center',
  },
  startText: { fontFamily: fonts.pixel, fontSize: 14, color: colors.parchment },
});