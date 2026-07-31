/**
 * SCREEN 06-1 · 마이페이지 (route MyPage) — 마이페이지 탭 ROOT (MainHeader, no back).
 * 골드 conic 링 프로필 카드(→ Level) · 퀘스트 달성 타임라인(내부 스크롤, 스태거) ·
 * 달성 상세 팝업(GamePopup) · 숏폼 만들기 / 아이템 목록 버튼.
 * Matches 06_mypage_flow.dc.html screen 1 + popup 2.
 */
// ⭐ 수정: useEffect, ActivityIndicator 추가
import React, { useCallback, useEffect, useState } from 'react';
import { View, Text, Image, StyleSheet, ScrollView, Pressable, ActivityIndicator } from 'react-native';
import * as ImagePicker from 'expo-image-picker'; // ⭐ 수정
import { useFocusEffect } from '@react-navigation/native'; // ⭐ 수정: 아이템 목록에서 칭호 장착 후 돌아왔을 때 실시간 반영
import { StatusBar } from 'expo-status-bar';
import Animated, { FadeInDown } from 'react-native-reanimated';
import { colors, fonts, radii, CATEGORY_ICONS, brand } from '../../theme';
import HazeBackground from '../../components/HazeBackground';
import MainHeader from '../../components/MainHeader';
import SpringButton from '../../components/SpringButton';
import GamePopup from '../../components/GamePopup';
import { useToast } from '../../components/Toast';
import { ConicAvatar, ChevronRight } from './_parts'; // ⭐ 수정: 더미 ACHIEVEMENTS/Achievement 제거
import {
  getMyQuestAchievements,
  type MyQuestAchievement,
  getMyProfile,
  uploadProfileImage,
  type MyProfile,
} from '../../api/mypage'; // ⭐ 수정
import { getFullImageUrl } from '../shop/_parts'; // ⭐ 수정: 장착 테두리 image_url이 상대경로(/static/...)라 base URL을 붙여야 함

// ⭐ 수정: completed_at(ISO)을 리스트용 짧은 날짜 / 팝업용 상세 시각 문자열로 변환
function formatShortDate(iso: string): string {
  const d = new Date(iso);
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}
function formatCompletedAt(iso: string): string {
  const d = new Date(iso);
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  const hh = String(d.getHours()).padStart(2, '0');
  const mm = String(d.getMinutes()).padStart(2, '0');
  return `${y}.${m}.${day} ${hh}:${mm}`;
}

export default function MyPageScreen({ navigation }: any) {
  // ⭐ 수정: 더미 Achievement 대신 API 응답 타입 + 로딩/에러 상태
  const [selected, setSelected] = useState<MyQuestAchievement | null>(null);
  const [achievements, setAchievements] = useState<MyQuestAchievement[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(false);
  // ⭐ 수정: 프로필 헤더(이름/칭호/레벨/연속접속일/이미지) 상태
  const [profile, setProfile] = useState<MyProfile | null>(null);
  const [profileLoading, setProfileLoading] = useState(true);
  const [profileError, setProfileError] = useState(false);
  const [uploadingImage, setUploadingImage] = useState(false);
  const toast = useToast();

  // ⭐ 수정: 마운트 시 달성 퀘스트 타임라인 조회
  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setLoadError(false);
      try {
        setAchievements(await getMyQuestAchievements());
      } catch (err: any) {
        setLoadError(true);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  // ⭐ 수정: 프로필 헤더 조회 — useFocusEffect로 변경 (마운트 + 아이템 목록에서 칭호 장착/해제하고
  // 돌아올 때마다 재조회되어 화면의 칭호 표시가 실시간으로 갱신됨)
  useFocusEffect(
    useCallback(() => {
      let cancelled = false;
      const loadProfile = async () => {
        setProfileLoading(true);
        setProfileError(false);
        try {
          const data = await getMyProfile();
          if (!cancelled) setProfile(data);
        } catch (err: any) {
          if (!cancelled) setProfileError(true);
        } finally {
          if (!cancelled) setProfileLoading(false);
        }
      };
      loadProfile();
      return () => {
        cancelled = true;
      };
    }, [])
  );

  // ⭐ 수정: 프로필 이미지 탭 → 갤러리 열기 → 업로드
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

  const goShortform = () => {
    try {
      navigation.navigate('Shortform');
    } catch {}
  };
  const goItemList = () => navigation.navigate('ItemList');

  return (
    <View style={styles.root}>
      <StatusBar style="light" />
      <HazeBackground />
      <MainHeader />

      <ScrollView
        style={styles.scroll}
        contentContainerStyle={styles.body}
        showsVerticalScrollIndicator={false}
      >
        {/* profile card → Level (아바타 탭 = 프로필 이미지 변경, 카메라 배지는 ConicAvatar deco) */}
        {/* ⭐ 수정: 더미 이름/칭호/레벨/연속접속일 → 실제 프로필 조회 + 아바타 탭 시 갤러리 업로드 */}
        <SpringButton style={styles.profileCard} onPress={() => navigation.navigate('MyLevel')} pressScale={0.985}>
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
                <Text style={styles.name}>{profile.nickname}</Text>
                <Text style={styles.title}>{profile.title}</Text>
                <View style={styles.metaRow}>
                  <Text style={styles.lv}>LV.{profile.current_level}</Text>
                  <Text style={styles.streak}>🔥 {profile.daily_streak}일째 연속접속</Text>
                </View>
              </>
            )}
          </View>
          <ChevronRight />
        </SpringButton>

        {/* section title */}
        <Text style={styles.sectionTitle}>퀘스트 달성업적 및 타임라인</Text>

        {/* achievement timeline (inner scroll, max 320) */}
        {/* ⭐ 수정: 더미 ACHIEVEMENTS → API 응답(achievements) + 로딩/에러/빈 목록 상태 */}
        <View style={styles.timelineCard}>
          {loading ? (
            <View style={styles.timelineStateBox}>
              <ActivityIndicator color={colors.primaryDark} />
            </View>
          ) : loadError ? (
            <View style={styles.timelineStateBox}>
              <Text style={styles.timelineStateText}>달성 내역을 불러오지 못했어요</Text>
            </View>
          ) : achievements.length === 0 ? (
            <View style={styles.timelineStateBox}>
              <Text style={styles.timelineStateText}>달성한 퀘스트가 없습니다</Text>
            </View>
          ) : (
            <ScrollView
              style={{ maxHeight: 320 }}
              nestedScrollEnabled
              showsVerticalScrollIndicator={false}
            >
              {/* ⭐ 수정: key를 quest_id → submission_id로 변경 (같은 퀘스트를 여러 번 완료할 수 있어 quest_id는 중복 가능) */}
              {achievements.map((a, i) => (
                <Animated.View key={a.submission_id} entering={FadeInDown.delay(50 + i * 70).duration(450)}>
                  <SpringButton
                    style={[styles.achRow, i === achievements.length - 1 && styles.achRowLast]}
                    onPress={() => setSelected(a)}
                    pressScale={0.99}
                  >
                    <Image source={CATEGORY_ICONS[a.category_code] ?? CATEGORY_ICONS.other} style={styles.achIcon} />
                    <Text style={styles.achName}>{a.title}</Text>
                    <Text style={styles.achDate}>{formatShortDate(a.completed_at)}</Text>
                  </SpringButton>
                </Animated.View>
              ))}
            </ScrollView>
          )}
        </View>

        {/* actions */}
        <View style={styles.actions}>
          <SpringButton style={[styles.actBtn, styles.actDark]} onPress={goShortform}>
            <Text style={styles.actDarkText}>숏폼 만들기</Text>
          </SpringButton>
          <SpringButton style={[styles.actBtn, styles.actGold]} onPress={goItemList}>
            <Text style={styles.actGoldText}>아이템 목록</Text>
          </SpringButton>
        </View>
      </ScrollView>

      {/* 달성 퀘스트 상세 팝업 (screen 2) */}
      <GamePopup visible={!!selected} onClose={() => setSelected(null)}>
        <Image source={brand.appIconCheck} style={styles.popupCheck} />
        {/* ⭐ 수정: API 응답 필드(title/description/completed_at/reward_exp/reward_point)로 매핑 */}
        {selected && (
          <>
            <Text style={styles.popupTitle}>{selected.title}</Text>
            <Text style={styles.popupDesc}>{selected.description}</Text>
            <Text style={styles.popupTime}>퀘스트 완료 시간 : {formatCompletedAt(selected.completed_at)}</Text>
            <View style={styles.chipRow}>
              <Text style={[styles.chip, styles.chipExp]}>경험치 +{selected.reward_exp ?? 0}</Text>
              <Text style={[styles.chip, styles.chipPoint]}>포인트 +{selected.reward_point ?? 0}</Text>
            </View>
            <SpringButton style={styles.popupBtn} onPress={() => setSelected(null)}>
              <Text style={styles.popupBtnText}>확인 완료</Text>
            </SpringButton>
          </>
        )}
      </GamePopup>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.screenBg },
  scroll: { flex: 1 },
  body: { padding: 16, paddingBottom: 28 },

  // profile card
  profileCard: {
    backgroundColor: colors.parchment,
    borderWidth: 2,
    borderColor: colors.pixelBorder,
    borderRadius: radii.card,
    paddingTop: 18,
    paddingBottom: 16,
    paddingHorizontal: 16,
    marginBottom: 20,
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
  // ⭐ 수정: 프로필 로딩 스피너 / 아바타 업로드 중 오버레이
  profileInfoLoading: { alignSelf: 'flex-start' },
  avatarUploadOverlay: {
    ...StyleSheet.absoluteFillObject,
    borderRadius: 999,
    backgroundColor: 'rgba(3,50,54,0.45)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  name: { fontSize: 18, fontWeight: '600', color: colors.primaryDark, fontFamily: fonts.bodyM },
  title: { fontSize: 13, color: colors.gold, fontWeight: '600', marginTop: 1, marginBottom: 3, fontFamily: fonts.bodyM },
  metaRow: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  lv: { fontFamily: fonts.pixel, fontSize: 15, color: colors.primaryDark },
  streak: { fontSize: 12, color: colors.xpGreen, fontWeight: '600', fontFamily: fonts.bodyM },

  // section
  sectionTitle: {
    fontFamily: fonts.pixel,
    fontSize: 16,
    color: colors.primaryDark,
    marginBottom: 12,
  },

  // timeline
  timelineCard: {
    backgroundColor: colors.white,
    borderRadius: 12,
    marginBottom: 14,
    overflow: 'hidden',
    shadowColor: '#033236',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.06,
    shadowRadius: 10,
    elevation: 2,
  },
  achRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    paddingVertical: 12,
    paddingHorizontal: 14,
    borderBottomWidth: 1,
    borderBottomColor: '#EEF1F0',
    backgroundColor: colors.white,
  },
  achRowLast: { borderBottomWidth: 0 },
  achIcon: { width: 40, height: 40, borderRadius: 9 },
  achName: { flex: 1, fontSize: 15, fontWeight: '600', color: colors.primaryDark, fontFamily: fonts.bodyM },
  achDate: { fontSize: 12, color: '#888', fontFamily: fonts.bodyR },
  // ⭐ 수정: 로딩/에러/빈 목록 상태 표시용
  timelineStateBox: { paddingVertical: 32, alignItems: 'center', justifyContent: 'center' },
  timelineStateText: { fontSize: 13, color: '#888', fontFamily: fonts.bodyM },

  // actions
  actions: { flexDirection: 'row', gap: 10 },
  actBtn: { flex: 1, height: 50, borderRadius: 8, alignItems: 'center', justifyContent: 'center' },
  actDark: { backgroundColor: colors.primaryDark },
  actDarkText: { color: colors.parchment, fontFamily: fonts.pixel, fontSize: 16 },
  actGold: { backgroundColor: colors.gold },
  actGoldText: { color: colors.primaryDark, fontFamily: fonts.pixel, fontSize: 16 },

  // popup
  popupCheck: { width: 72, height: 72, marginBottom: 14 },
  popupTitle: { fontFamily: fonts.pixel, fontSize: 20, color: '#F5ECCB', textAlign: 'center', marginBottom: 8 },
  popupDesc: { textAlign: 'center', fontSize: 14, color: '#B9C9BD', lineHeight: 21, marginBottom: 14, fontFamily: fonts.bodyR },
  popupTime: { textAlign: 'center', fontSize: 13, color: '#8FA79A', marginBottom: 16, fontFamily: fonts.bodyR },
  chipRow: { flexDirection: 'row', justifyContent: 'center', gap: 10, marginBottom: 20 },
  chip: { borderRadius: 24, paddingVertical: 6, paddingHorizontal: 14, fontSize: 13, fontWeight: '700', overflow: 'hidden', fontFamily: fonts.bodyB },
  chipExp: { backgroundColor: colors.xpGreen, color: colors.white },
  chipPoint: { backgroundColor: colors.gold, color: colors.primaryDark },
  popupBtn: {
    alignSelf: 'stretch',
    height: 48,
    borderRadius: 8,
    backgroundColor: colors.primaryDark,
    alignItems: 'center',
    justifyContent: 'center',
  },
  popupBtnText: { color: colors.parchment, fontFamily: fonts.pixel, fontSize: 16 },
});
