/**
 * SCREEN 06-1 · 마이페이지 (route MyPage) — 마이페이지 탭 ROOT (MainHeader, no back).
 * 골드 conic 링 프로필 카드(→ Level) · 퀘스트 달성 타임라인(내부 스크롤, 스태거) ·
 * 달성 상세 팝업(GamePopup) · 숏폼 만들기 / 아이템 목록 버튼.
 * Matches 06_mypage_flow.dc.html screen 1 + popup 2.
 */
import React, { useState } from 'react';
import { View, Text, Image, StyleSheet, ScrollView, Pressable } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import Animated, { FadeInDown } from 'react-native-reanimated';
import { colors, fonts, radii, CATEGORY_ICONS, brand } from '../../theme';
import HazeBackground from '../../components/HazeBackground';
import MainHeader from '../../components/MainHeader';
import SpringButton from '../../components/SpringButton';
import GamePopup from '../../components/GamePopup';
import { useToast } from '../../components/Toast';
import {
  ConicAvatar,
  ChevronRight,
  ACHIEVEMENTS,
  type Achievement,
} from './_parts';

export default function MyPageScreen({ navigation }: any) {
  const [selected, setSelected] = useState<Achievement | null>(null);
  const toast = useToast();

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
        <SpringButton style={styles.profileCard} onPress={() => navigation.navigate('MyLevel')} pressScale={0.985}>
          <Pressable onPress={() => toast.show('프로필 이미지 변경')}>
            <ConicAvatar size={64} deco />
          </Pressable>
          <View style={styles.profileInfo}>
            <Text style={styles.name}>선한김철수</Text>
            <Text style={styles.title}>마을 수호자</Text>
            <View style={styles.metaRow}>
              <Text style={styles.lv}>LV.12</Text>
              <Text style={styles.streak}>🔥 7일째 연속접속</Text>
            </View>
          </View>
          <ChevronRight />
        </SpringButton>

        {/* section title */}
        <Text style={styles.sectionTitle}>퀘스트 달성업적 및 타임라인</Text>

        {/* achievement timeline (inner scroll, max 320) */}
        <View style={styles.timelineCard}>
          <ScrollView
            style={{ maxHeight: 320 }}
            nestedScrollEnabled
            showsVerticalScrollIndicator={false}
          >
            {ACHIEVEMENTS.map((a, i) => (
              <Animated.View key={a.name} entering={FadeInDown.delay(50 + i * 70).duration(450)}>
                <SpringButton
                  style={[styles.achRow, i === ACHIEVEMENTS.length - 1 && styles.achRowLast]}
                  onPress={() => setSelected(a)}
                  pressScale={0.99}
                >
                  <Image source={CATEGORY_ICONS[a.category]} style={styles.achIcon} />
                  <Text style={styles.achName}>{a.name}</Text>
                  <Text style={styles.achDate}>{a.date}</Text>
                </SpringButton>
              </Animated.View>
            ))}
          </ScrollView>
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
        {selected && (
          <>
            <Text style={styles.popupTitle}>{selected.name}</Text>
            <Text style={styles.popupDesc}>{selected.desc}</Text>
            <Text style={styles.popupTime}>퀘스트 완료 시간 : {selected.completedAt}</Text>
            <View style={styles.chipRow}>
              <Text style={[styles.chip, styles.chipExp]}>경험치 +{selected.exp}</Text>
              <Text style={[styles.chip, styles.chipPoint]}>포인트 +{selected.point}</Text>
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
