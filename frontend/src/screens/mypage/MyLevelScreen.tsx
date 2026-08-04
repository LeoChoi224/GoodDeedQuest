/**
 * SCREEN 06-4 · 레벨 페이지 (route MyLevel, back) — 프로필 카드(MyPageScreen과 완전 동일:
 * ProfileContext 공유, 아바타 업로드, 닉네임/관심카테고리 수정 모달 포함) ·
 * 경험치 바(PixelProgress, 마운트/포커스마다 채워짐 + XP count-up, 이번 레벨 안에서의 진행률로 표시) ·
 * 주간 경험치 추이 라인차트(react-native-svg, 그려지는 애니메이션, 일요일부터 시작하고
 * 아직 지나지 않은 요일은 선이 안 그려짐) · 랭킹 보러가기 → Ranking.
 * /growth/status 실API + ProfileContext(/mypage/profile) 연결.
 * ⭐ 수정: 프로필 카드를 MyPageScreen.tsx와 1:1 동일하게 이식 — 기존엔 아바타 52px·테두리 미표시·
 * 이름/칭호/레벨을 한 줄로 압축 표시했는데, 마이페이지 메인과 스타일이 달라 보여서 완전히 통일함.
 * 이 화면 자체가 이미 "레벨" 화면이라 마이페이지처럼 카드 전체를 눌러 MyLevel로 이동하는
 * 동작(및 화살표)만 빼고, 아바타 크기(64)·장착 테두리·편집 연필·칭호+관심카테고리·LV+연속접속일
 * 레이아웃/스타일은 전부 동일.
 * ⭐ useFocusEffect로 교체 — 화면에 포커스가 올 때마다(다른 화면 갔다 뒤로가기로 돌아올 때도)
 * 다시 불러오게 함. 이전엔 useEffect(마운트 1회)라 퀘스트 완료 후 돌아와도 새로고침 안 됐음.
 * ⭐ 원본 디자인엔 "지난 주" 골드 점선 비교선이 있었으나, 백엔드가 이번 주 누적치만 주고
 * 지난 주 데이터는 안 줘서 이번 주 실선만 표시함(지난 주 비교는 백엔드 확장 필요).
 * Matches 06_mypage_flow.dc.html screen 4.
 */
import React, { useCallback, useEffect, useState } from 'react';
import { View, Text, Image, StyleSheet, ScrollView, Pressable, ActivityIndicator } from 'react-native';
import * as ImagePicker from 'expo-image-picker'; // ⭐ 수정: 프로필 카드 마이페이지와 완전히 동일하게 맞추면서 아바타 업로드도 이식
import { StatusBar } from 'expo-status-bar';
import { useFocusEffect } from '@react-navigation/native';
import Svg, { Line, Path, Text as SvgText } from 'react-native-svg';
import Animated, {
  useSharedValue,
  useAnimatedProps,
  withTiming,
  Easing,
} from 'react-native-reanimated';
import { colors, fonts, radii, CATEGORY_DEFS, CATEGORY_ICONS } from '../../theme'; // ⭐ 수정: radii/CATEGORY_DEFS/CATEGORY_ICONS 추가
import HazeBackground from '../../components/HazeBackground';
import MainHeader from '../../components/MainHeader';
import SpringButton from '../../components/SpringButton';
import PixelProgress from '../../components/PixelProgress';
import GamePopup, { PopupButtons } from '../../components/GamePopup'; // ⭐ 수정
import GdqInput from '../../components/GdqInput'; // ⭐ 수정
import { useToast } from '../../components/Toast'; // ⭐ 수정
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
import { uploadProfileImage, updateMyProfile } from '../../api/mypage'; // ⭐ 수정: getMyProfile 직접 호출 대신 ProfileContext 사용
import { useProfile } from '../../context/ProfileContext'; // ⭐ 수정: 마이페이지/드로어와 같은 프로필 소스 공유
import { getFullImageUrl } from '../shop/_parts'; // ⭐ 수정: 장착 테두리 image_url 절대경로 변환

// ⭐ 수정: 관심카테고리 key → 화면 표기 라벨 (MyPageScreen과 동일 로직)
function categoryLabel(key: string): string {
  return CATEGORY_DEFS.find((c) => c.key === key)?.label ?? key;
}

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
  // ⭐ 수정: 프로필(이름/칭호/레벨/연속접속일/이미지/관심카테고리)은 마이페이지·드로어와
  // 공유하는 ProfileContext에서 가져온다 — 이 화면에서 수정해도 즉시 다른 화면에 반영됨.
  const { profile, loading: profileLoading, error: profileError, refreshProfile, setProfile } = useProfile();
  const [level, setLevel] = useState(1);
  const [currentXp, setCurrentXp] = useState(0);
  const [nextLevelXp, setNextLevelXp] = useState(1000);
  const [levelFloorXp, setLevelFloorXp] = useState(0);
  const [graph, setGraph] = useState<DailyXp[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [uploadingImage, setUploadingImage] = useState(false);
  const toast = useToast();

  // ⭐ 수정: 프로필 수정(닉네임/관심카테고리) 모달 상태 — MyPageScreen과 동일
  const [editVisible, setEditVisible] = useState(false);
  const [editNickname, setEditNickname] = useState('');
  const [editNickError, setEditNickError] = useState<string | null>(null);
  const [editCats, setEditCats] = useState<Record<string, boolean>>({});
  const [savingProfile, setSavingProfile] = useState(false);

  // ⭐ 수정: 포커스될 때마다 프로필 재조회 (칭호 장착/프로필 수정 후 돌아와도 최신 반영)
  useFocusEffect(
    useCallback(() => {
      refreshProfile();
    }, [refreshProfile])
  );

  // ⭐ 수정: useEffect(마운트 1회) → useFocusEffect(포커스 올 때마다) - 퀘스트 완료 후
  // Ranking 갔다 뒤로가기로 돌아와도 최신 데이터로 다시 불러오게.
  useFocusEffect(
    useCallback(() => {
      let cancelled = false;
      setLoading(true);
      setError(null);
      getGrowthStatus()
        .then((growth) => {
          if (cancelled) return;
          setLevel(growth.current_level);
          setCurrentXp(growth.current_xp);
          setNextLevelXp(growth.next_level_xp);
          setLevelFloorXp(growth.current_level_floor_xp);
          setGraph(growth.weekly_xp_graph);
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

  // ⭐ 수정: 프로필 이미지 탭 → 갤러리 열기 → 업로드 (MyPageScreen과 동일)
  const pickAndUploadAvatar = async () => {
    if (uploadingImage) return;
    const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!permission.granted) {
      toast.show('사진 접근 권한을 허용해 주세요.');
      return;
    }
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ['images'],
      quality: 0.7,
    });
    if (result.canceled || result.assets.length === 0) return;

    try {
      setUploadingImage(true);
      const updated = await uploadProfileImage(result.assets[0].uri);
      setProfile(updated);
      toast.show('프로필 이미지를 변경했어요.');
    } catch (err) {
      toast.show('프로필 이미지 변경에 실패했어요.');
    } finally {
      setUploadingImage(false);
    }
  };

  // ⭐ 수정: 연필 버튼 탭 → 현재 프로필 값으로 수정 모달 초기화 후 오픈
  const openEditProfile = () => {
    if (!profile) return;
    setEditNickname(profile.nickname);
    setEditNickError(null);
    const cats: Record<string, boolean> = {};
    CATEGORY_DEFS.forEach((c) => {
      cats[c.key] = !!profile.category?.includes(c.key);
    });
    setEditCats(cats);
    setEditVisible(true);
  };

  const toggleEditCat = (key: string) => setEditCats((s) => ({ ...s, [key]: !s[key] }));

  // ⭐ 수정: 닉네임(2~10자) + 관심카테고리 부분 수정 저장
  const saveProfile = async () => {
    const nick = editNickname.trim();
    if (nick.length < 2 || nick.length > 10) {
      setEditNickError('닉네임은 2~10자로 입력해 주세요.');
      return;
    }
    setEditNickError(null);
    const category = Object.keys(editCats).filter((k) => editCats[k]);

    try {
      setSavingProfile(true);
      const updated = await updateMyProfile({ nickname: nick, category });
      setProfile(updated);
      setEditVisible(false);
      toast.show('프로필을 수정했어요.');
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      toast.show(typeof detail === 'string' ? detail : '프로필 수정에 실패했어요.');
    } finally {
      setSavingProfile(false);
    }
  };

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
        {/* profile card — MyPageScreen 프로필 카드와 완전히 동일 (아바타 업로드/닉네임·관심카테고리 수정 포함) */}
        <View style={styles.profileCard}>
          <Pressable onPress={pickAndUploadAvatar} disabled={uploadingImage}>
            <ConicAvatar
              size={64}
              deco
              imageUri={profile?.profile_image_url ?? null}
              borderImageUrl={profile?.equipped_border_image_url ? getFullImageUrl(profile.equipped_border_image_url) : null}
            />
            {uploadingImage && (
              <View style={styles.avatarUploadOverlay}>
                <ActivityIndicator color={colors.parchment} size="small" />
              </View>
            )}
          </Pressable>
          <View style={styles.profileInfo}>
            {profileLoading ? (
              <ActivityIndicator color={colors.primaryDark} style={styles.profileInfoLoading} />
            ) : profileError || !profile ? (
              <Text style={styles.name}>프로필을 불러오지 못했어요</Text>
            ) : (
              <>
                <View style={styles.nameRow}>
                  <Text style={styles.name}>{profile.nickname}</Text>
                  <Pressable onPress={openEditProfile} hitSlop={8} style={styles.editBtn}>
                    <Text style={styles.editIcon}>✏️</Text>
                  </Pressable>
                </View>
                <View style={styles.titleRow}>
                  <Text style={styles.title}>{profile.title}</Text>
                  {profile.category && profile.category.length > 0 && (
                    <Text style={styles.categoryText} numberOfLines={1} ellipsizeMode="tail">
                      {profile.category.map(categoryLabel).join(', ')}
                    </Text>
                  )}
                </View>
                <View style={styles.metaRow}>
                  <Text style={styles.lv}>LV.{level}</Text>
                  <Text style={styles.streak}>🔥 {profile.daily_streak}일째 연속접속</Text>
                </View>
              </>
            )}
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

      {/* ⭐ 수정: 프로필 수정(닉네임/관심카테고리) 모달 — MyPageScreen과 동일 */}
      <GamePopup visible={editVisible} onClose={() => setEditVisible(false)} title="프로필 수정" width={320}>
        <View style={{ alignSelf: 'stretch' }}>
          <Text style={styles.editLabel}>닉네임</Text>
          <GdqInput
            value={editNickname}
            onChangeText={(v) => {
              setEditNickname(v);
              if (editNickError) setEditNickError(null);
            }}
            placeholder="닉네임을 입력하세요"
            maxLength={10}
          />
          {editNickError ? <Text style={styles.editErrorText}>{editNickError}</Text> : null}

          <Text style={[styles.editLabel, { marginTop: 16 }]}>관심 카테고리</Text>
          <View style={styles.editGrid}>
            {CATEGORY_DEFS.map((c) => {
              const on = !!editCats[c.key];
              return (
                <Pressable
                  key={c.key}
                  onPress={() => toggleEditCat(c.key)}
                  style={[styles.editCatCell, on ? styles.editCatCellOn : styles.editCatCellOff]}
                >
                  <Image source={CATEGORY_ICONS[c.key]} style={styles.editCatIcon} />
                  <Text style={[styles.editCatLabel, { color: on ? colors.white : colors.parchment }]}>{c.label}</Text>
                </Pressable>
              );
            })}
          </View>
        </View>

        {savingProfile ? (
          <ActivityIndicator color={colors.gold} style={{ marginTop: 20 }} />
        ) : (
          <PopupButtons
            primaryLabel="저장"
            onPrimary={saveProfile}
            secondaryLabel="취소"
            onSecondary={() => setEditVisible(false)}
          />
        )}
      </GamePopup>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.screenBg },
  scroll: { flex: 1 },
  body: { padding: 16, paddingBottom: 28 },

  // ⭐ 수정: profileCard 이하 프로필 카드 스타일 세트 — MyPageScreen.tsx와 완전히 동일(1:1 이식)
  profileCard: {
    backgroundColor: colors.parchment,
    borderWidth: 2,
    borderColor: colors.pixelBorder,
    borderRadius: radii.card,
    paddingTop: 18,
    paddingBottom: 16,
    paddingHorizontal: 16,
    marginBottom: 18,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 14,
    shadowColor: '#5C3D1E',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.12,
    shadowRadius: 14,
    elevation: 3,
  },
  profileInfo: { flex: 1, minWidth: 0 },
  nameRow: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  editBtn: { padding: 2 },
  editIcon: { fontSize: 13 },
  editLabel: { fontSize: 13, fontWeight: '700', color: colors.gold, marginBottom: 8, fontFamily: fonts.bodyB },
  editErrorText: { marginTop: 6, fontSize: 12, color: '#FF8A80', fontFamily: fonts.bodyM },
  editGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  editCatCell: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    height: 42,
    borderRadius: radii.chip,
    paddingHorizontal: 10,
    width: '47%',
  },
  editCatCellOn: { backgroundColor: colors.primaryDark, borderWidth: 2, borderColor: colors.gold },
  editCatCellOff: { backgroundColor: 'rgba(255,255,255,0.06)', borderWidth: 1, borderColor: 'rgba(242,215,131,0.35)' },
  editCatIcon: { width: 24, height: 24, borderRadius: 6 },
  editCatLabel: { fontSize: 13, fontWeight: '600', fontFamily: fonts.bodyM },
  profileInfoLoading: { alignSelf: 'flex-start' },
  avatarUploadOverlay: {
    ...StyleSheet.absoluteFillObject,
    borderRadius: 999,
    backgroundColor: 'rgba(3,50,54,0.45)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  name: { fontSize: 18, fontWeight: '600', color: colors.primaryDark, fontFamily: fonts.bodyM },
  titleRow: { flexDirection: 'row', alignItems: 'center', gap: 6, marginTop: 1, marginBottom: 3 },
  title: { fontSize: 13, color: colors.gold, fontWeight: '600', fontFamily: fonts.bodyM },
  categoryText: { flexShrink: 1, fontSize: 11, color: colors.textMuted, fontFamily: fonts.bodyM },
  metaRow: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  lv: { fontFamily: fonts.pixel, fontSize: 15, color: colors.primaryDark },
  streak: { fontSize: 12, color: colors.xpGreen, fontWeight: '600', fontFamily: fonts.bodyM },

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