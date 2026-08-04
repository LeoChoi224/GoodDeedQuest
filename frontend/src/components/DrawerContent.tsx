/**
 * 햄버거 드로어 — 선행퀘스트 RPG 컨셉(양피지·픽셀·골드·틸). 우측 슬라이드인.
 * 각 섹션을 토글(아코디언)하면 하위 상세 페이지가 펼쳐지고, 항목을 누르면 해당
 * 화면으로 딥링크한다. 최하단에 관리자 · 로그아웃 분리 배치.
 */
import React, { useEffect, useState } from 'react';
import { View, Text, Image, StyleSheet, Pressable, ScrollView } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import type { DrawerContentComponentProps } from '@react-navigation/drawer';
import Animated, {
  FadeIn,
  FadeOut,
  useAnimatedStyle,
  useSharedValue,
  withTiming,
  Easing,
} from 'react-native-reanimated';
import { colors, fonts, brand, heroGradient, radii, NAV_ICONS } from '../theme';
import { useAuth } from '../context/AuthContext';
import { useProfile } from '../context/ProfileContext'; // ⭐ 수정: 마이페이지 프로필 헤더와 동일한 정보를 실시간으로 표시
import { logout as logoutApi } from '../api/auth';

type Child = { label: string; screen: string };
type Section = {
  key: string;
  label: string;
  icon?: any;
  tab?: string; // tab route inside Main
  route?: string; // drawer sibling route
  children: Child[];
};

const SECTIONS: Section[] = [
  // 【판단】 '진행중 · 추천 퀘스트'와 '퀘스트 상세'는 뺐다. 앞의 것은 홈 탭이 이미
  // 같은 화면이라 중복이고, 뒤의 것은 어떤 퀘스트를 볼지 고르지 않은 채 들어가서
  // 목록의 첫 번째로 가버린다. 퀘스트 상세는 목록에서 눌러 들어가는 게 맞다.
  { key: 'home', label: '홈 · 퀘스트', icon: NAV_ICONS.home, tab: 'Home', children: [
    { label: '퀘스트 등록', screen: 'QuestRegister' },
    { label: 'AI 커스텀 추천', screen: 'AiRecommend' },
  ] },
  { key: 'community', label: '커뮤니티', icon: NAV_ICONS.community, tab: 'Community', children: [
    { label: '피드', screen: 'Feed' },
    { label: '새 피드 작성', screen: 'NewPost' },
  ] },
  { key: 'map', label: '지도 · 대항전', icon: NAV_ICONS.map, tab: 'Map', children: [
    { label: '전국 지도', screen: 'Map' },
    { label: '지역 랭킹', screen: 'Ranking' },
    { label: '내 주변 봉사', screen: 'Nearby' },
  ] },
  { key: 'shop', label: '상점', icon: NAV_ICONS.shop, tab: 'Shop', children: [
    { label: '상점', screen: 'Shop' },
    { label: '구매 내역', screen: 'PurchaseHistory' },
    { label: '보유 아이템', screen: 'Inventory' },
  ] },
  { key: 'my', label: '마이페이지', icon: NAV_ICONS.my, tab: 'My', children: [
    { label: '내 정보 · 달성', screen: 'MyPage' },
    { label: '레벨', screen: 'Level' },
    { label: '랭킹', screen: 'Rank' },
  ] },
  { key: 'team', label: '팀 챌린지', route: 'TeamChallenge', children: [
    { label: '팀 챌린지 홈', screen: 'TeamHome' },
    { label: '방 찾기', screen: 'RoomFind' },
    { label: '팀 목록 · 생성', screen: 'TeamList' },
  ] },
  { key: 'shortform', label: '숏폼 만들기', route: 'Shortform', children: [
    { label: '사진 선택 · 생성', screen: 'PhotoSelect' },
  ] },
];

function Chevron({ open }: { open: boolean }) {
  const r = useSharedValue(open ? 1 : 0);
  useEffect(() => {
    r.value = withTiming(open ? 1 : 0, { duration: 180, easing: Easing.out(Easing.ease) });
  }, [open]);
  const st = useAnimatedStyle(() => ({ transform: [{ rotate: `${90 * r.value}deg` }] }));
  return <Animated.Text style={[styles.chev, st]}>›</Animated.Text>;
}

export default function DrawerContent(props: DrawerContentComponentProps) {
  const insets = useSafeAreaInsets();
  const { navigation } = props;
  const [open, setOpen] = useState<string | null>('home');
  const { signOut } = useAuth();
  const { profile } = useProfile(); // ⭐ 수정: 마이페이지 프로필 헤더와 같은 Context

  const toggle = (key: string) => setOpen((cur) => (cur === key ? null : key));

  const goChild = (section: Section, child: Child) => {
    navigation.closeDrawer();
    if (section.tab) {
      navigation.navigate('Main', { screen: section.tab, params: { screen: child.screen } });
    } else if (section.route) {
      navigation.navigate(section.route, { screen: child.screen });
    }
  };

  const goAdmin = () => {
    navigation.closeDrawer();
    navigation.navigate('Admin', { screen: 'Dashboard' });
  };
  const logout = async () => {
    navigation.closeDrawer();
    // 【판단】 서버의 logout 을 먼저 부른다. 이게 없으면 refresh 토큰이 서버에
    //        살아남아 30일간 유효하다. 로컬만 지우는 건 회수가 아니다.
    //        실패해도 아래 signOut 은 돈다 — 인터넷이 끊겼다고 로그아웃을
    //        못 하면 안 되기 때문이다(logout 내부에서 이미 try/catch).
    await logoutApi();
    // signOut 이 로컬 토큰을 지우면 화면 묶음도 자동으로 바뀐다.
    await signOut();
  };

  return (
    <View style={styles.root}>
      <LinearGradient
        colors={heroGradient.colors}
        locations={heroGradient.locations}
        style={[styles.header, { paddingTop: insets.top + 22 }]}
      >
        <Image source={brand.appIcon} style={styles.brandIcon} />
        <View style={{ flex: 1 }}>
          <Text style={styles.brand}>선행퀘스트</Text>
          {/* ⭐ 수정: 더미 텍스트 → 마이페이지 프로필 헤더와 동일한 Context 데이터 (실시간 동기화) */}
          <Text style={styles.sub}>
            {profile ? `${profile.nickname} · ${profile.title}` : '불러오는 중...'}
          </Text>
          <View style={styles.metaRow}>
            <View style={styles.lvPill}>
              <Text style={styles.lvText}>LV.{profile?.current_level ?? '-'}</Text>
            </View>
            <Text style={styles.streak}>🔥 {profile?.daily_streak ?? 0}일째 연속접속</Text>
          </View>
        </View>
      </LinearGradient>
      <View style={styles.goldRule} />

      <ScrollView contentContainerStyle={styles.body} showsVerticalScrollIndicator={false}>
        {SECTIONS.map((s) => {
          const isOpen = open === s.key;
          return (
            <View key={s.key} style={[styles.section, isOpen && styles.sectionOpen]}>
              <Pressable style={styles.sectionHead} onPress={() => toggle(s.key)}>
                {s.icon ? (
                  <Image source={s.icon} style={styles.secIcon} />
                ) : (
                  <View style={styles.secDot} />
                )}
                <Text style={styles.sectionLabel}>{s.label}</Text>
                <Chevron open={isOpen} />
              </Pressable>

              {isOpen ? (
                <Animated.View entering={FadeIn.duration(160)} exiting={FadeOut.duration(120)} style={styles.children}>
                  {s.children.map((c, i) => (
                    <Pressable key={c.screen} style={styles.childRow} onPress={() => goChild(s, c)}>
                      <View style={styles.childDiamond} />
                      <Text style={styles.childLabel}>{c.label}</Text>
                    </Pressable>
                  ))}
                </Animated.View>
              ) : null}
            </View>
          );
        })}

        <View style={styles.divider} />
        <Pressable style={styles.footRow} onPress={goAdmin}>
          <Text style={styles.footText}>관리자 페이지</Text>
          <Text style={styles.footChev}>›</Text>
        </Pressable>
        <Pressable style={styles.footRow} onPress={logout}>
          <Text style={[styles.footText, { color: colors.danger }]}>로그아웃</Text>
          <Text style={[styles.footChev, { color: colors.danger }]}>›</Text>
        </Pressable>
      </ScrollView>

      <Text style={[styles.version, { marginBottom: insets.bottom + 12 }]}>v1.0.0 · 선행퀘스트</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.parchment },
  header: { flexDirection: 'row', alignItems: 'center', gap: 12, paddingHorizontal: 18, paddingBottom: 18 },
  brandIcon: { width: 48, height: 48, borderRadius: 11 },
  brand: { fontFamily: fonts.pixel, fontSize: 18, color: colors.white },
  sub: { fontSize: 12, color: 'rgba(255,255,255,0.72)', marginTop: 3, fontFamily: fonts.bodyR },
  metaRow: { flexDirection: 'row', alignItems: 'center', gap: 8, marginTop: 8 },
  lvPill: { backgroundColor: 'rgba(212,160,23,0.22)', borderWidth: 1, borderColor: 'rgba(212,160,23,0.6)', borderRadius: 999, paddingHorizontal: 9, paddingVertical: 2 },
  lvText: { fontFamily: fonts.pixel, fontSize: 11, color: colors.gold },
  streak: { fontSize: 11, color: 'rgba(255,255,255,0.75)', fontFamily: fonts.bodyM },
  goldRule: { height: 3, backgroundColor: colors.gold, opacity: 0.85 },

  body: { paddingHorizontal: 12, paddingTop: 12, paddingBottom: 8 },
  section: {
    backgroundColor: colors.white,
    borderRadius: radii.card,
    borderWidth: 1.5,
    borderColor: '#E7D9B5',
    marginBottom: 8,
    overflow: 'hidden',
  },
  sectionOpen: { borderColor: colors.gold },
  sectionHead: { flexDirection: 'row', alignItems: 'center', gap: 10, paddingHorizontal: 12, height: 50 },
  secIcon: { width: 26, height: 26, borderRadius: 7 },
  secDot: { width: 22, height: 22, borderRadius: 6, backgroundColor: colors.primaryDark, alignItems: 'center', justifyContent: 'center' },
  sectionLabel: { flex: 1, fontSize: 15, color: colors.textPrimary, fontFamily: fonts.bodyB, fontWeight: '700' },
  chev: { fontSize: 22, color: colors.textMuted, width: 16, textAlign: 'center' },

  children: { paddingBottom: 6, paddingLeft: 46, paddingRight: 12 },
  childRow: { flexDirection: 'row', alignItems: 'center', gap: 9, paddingVertical: 9 },
  childDiamond: { width: 6, height: 6, transform: [{ rotate: '45deg' }], backgroundColor: colors.gold },
  childLabel: { fontSize: 13.5, color: colors.textSecondary, fontFamily: fonts.bodyM },

  divider: { height: 1, backgroundColor: '#E7D9B5', marginVertical: 10, marginHorizontal: 4 },
  footRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 14, height: 48 },
  footText: { fontSize: 14, color: colors.primaryDark, fontFamily: fonts.bodyB, fontWeight: '700' },
  footChev: { fontSize: 18, color: colors.textMuted },
  version: { textAlign: 'center', fontSize: 11, color: '#B29A63', fontFamily: fonts.bodyR },
});
