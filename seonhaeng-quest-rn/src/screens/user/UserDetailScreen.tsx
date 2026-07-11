/**
 * UserDetailScreen (route: UserDetail) — 스토리보드 #48. 어느 화면에서든 유저를 누르면
 * 오는 공용 프로필. Root 스택에 등록되어 모든 중첩 네비게이터에서 도달.
 * ① 프로필 카드(아바타·닉네임·칭호·LV·연속접속) ② 퀘스트 달성 타임라인(FlatList).
 * params.moderation=true 면 관리자용 차단 버튼(리스트 푸터) 노출.
 */
import React, { useState } from 'react';
import { View, Text, StyleSheet, FlatList, Image } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { LinearGradient } from 'expo-linear-gradient';
import Animated, { FadeInDown } from 'react-native-reanimated';
import HazeBackground from '../../components/HazeBackground';
import MainHeader from '../../components/MainHeader';
import SpringButton from '../../components/SpringButton';
import GamePopup, { PopupButtons } from '../../components/GamePopup';
import { useToast } from '../../components/Toast';
import { colors, fonts, radii, shadow, CATEGORY_ICONS } from '../../theme';

const DEFAULT_GRAD: [string, string] = ['#0E4F40', '#033236'];

// 이름 기반 안정적 목업 값 (실서비스에선 API)
function hashNum(s: string, mod: number, base: number) {
  let h = 0;
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) & 0xffff;
  return base + (h % mod);
}

const USER_QUESTS = [
  { category: 'volunteer', name: '무료 급식 봉사', date: '2026-07-01' },
  { category: 'environment', name: '한강 플로깅', date: '2026-06-30' },
  { category: 'sharing', name: '헌혈 캠페인 참여', date: '2026-06-25' },
  { category: 'animal', name: '유기견 임시보호', date: '2026-06-20' },
  { category: 'community', name: '마을 청소 활동', date: '2026-06-15' },
];

export default function UserDetailScreen({ navigation, route }: any) {
  const toast = useToast();
  const user = route?.params?.user ?? {};
  const name: string = user.name ?? '선한 영웅';
  const title: string = user.title ?? '마을 수호자';
  const level = user.level ?? user.lv ?? hashNum(name, 40, 5);
  const streak = hashNum(name + 's', 20, 3);
  const grad: [string, string] =
    Array.isArray(user.grad) && user.grad.length >= 2 ? [user.grad[0], user.grad[1]] : DEFAULT_GRAD;
  const moderation: boolean = !!route?.params?.moderation;
  const blocked: boolean = !!user.blocked;

  const [confirmBlock, setConfirmBlock] = useState(false);

  const header = (
    <View>
      <Animated.View entering={FadeInDown.duration(360)} style={styles.card}>
        <LinearGradient colors={grad} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.avatar}>
          <Text style={styles.avatarInitial}>{name.slice(0, 1)}</Text>
        </LinearGradient>
        <Text style={styles.name}>{name}</Text>
        <Text style={styles.title}>{title}</Text>
        <View style={styles.metaRow}>
          <View style={styles.lvPill}>
            <Text style={styles.lvText}>LV.{level}</Text>
          </View>
          <Text style={styles.streak}>🔥 {streak}일째 연속접속</Text>
        </View>
      </Animated.View>

      <Text style={styles.sectionTitle}>퀘스트 달성업적 및 타임라인</Text>
    </View>
  );

  const footer = moderation ? (
    <SpringButton
      style={[styles.modBtn, blocked ? styles.unblockBtn : styles.blockBtn]}
      onPress={() => setConfirmBlock(true)}
    >
      <Text style={[styles.modText, { color: blocked ? colors.primaryDark : colors.danger }]}>
        {blocked ? '차단 해제하기' : '차단하기'}
      </Text>
    </SpringButton>
  ) : (
    <View style={{ height: 20 }} />
  );

  return (
    <View style={styles.root}>
      <StatusBar style="dark" />
      <HazeBackground />
      <MainHeader showBack title="유저 정보" onBack={() => navigation.goBack()} />

      <FlatList
        data={USER_QUESTS}
        keyExtractor={(_, i) => String(i)}
        ListHeaderComponent={header}
        renderItem={({ item, index }) => (
          <Animated.View entering={FadeInDown.delay(50 + index * 60).duration(400)}>
            <View style={styles.achRow}>
              <Image source={CATEGORY_ICONS[item.category]} style={styles.achIcon} />
              <Text style={styles.achName}>{item.name}</Text>
              <Text style={styles.achDate}>{item.date}</Text>
            </View>
          </Animated.View>
        )}
        ItemSeparatorComponent={() => <View style={styles.divider} />}
        ListFooterComponent={footer}
        contentContainerStyle={{ padding: 16, paddingBottom: 40 }}
        showsVerticalScrollIndicator={false}
      />

      {/* 차단/해제 확인 (관리자) — 게임 팝업 */}
      <GamePopup
        visible={confirmBlock}
        onClose={() => setConfirmBlock(false)}
        title={blocked ? '차단을 해제하시겠습니까?' : '차단하시겠습니까?'}
      >
        <PopupButtons
          primaryLabel="예"
          onPrimary={() => {
            setConfirmBlock(false);
            toast.show(blocked ? '차단이 해제되었습니다' : `${name}님을 차단했어요`);
            navigation.goBack();
          }}
          secondaryLabel="아니오"
          onSecondary={() => setConfirmBlock(false)}
        />
      </GamePopup>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.screenBg },
  card: {
    backgroundColor: colors.white,
    borderRadius: radii.card,
    borderWidth: 1,
    borderColor: colors.inputBorder,
    alignItems: 'center',
    paddingVertical: 26,
    marginBottom: 16,
    ...shadow.card,
  },
  avatar: { width: 88, height: 88, borderRadius: 44, alignItems: 'center', justifyContent: 'center', borderWidth: 2, borderColor: colors.gold, marginBottom: 14 },
  avatarInitial: { fontFamily: fonts.pixel, fontSize: 34, color: colors.parchment },
  name: { fontFamily: fonts.pixel, fontSize: 22, color: colors.primaryDark },
  title: { fontSize: 14, color: colors.gold, fontFamily: fonts.bodyM, marginTop: 4 },
  metaRow: { flexDirection: 'row', alignItems: 'center', gap: 10, marginTop: 10 },
  lvPill: { backgroundColor: 'rgba(212,160,23,0.16)', borderWidth: 1, borderColor: 'rgba(212,160,23,0.6)', borderRadius: 999, paddingHorizontal: 10, paddingVertical: 2 },
  lvText: { fontFamily: fonts.pixel, fontSize: 12, color: '#8A6A1E' },
  streak: { fontSize: 12, color: colors.xpGreen, fontFamily: fonts.bodyM },

  sectionTitle: { fontFamily: fonts.pixel, fontSize: 16, color: colors.primaryDark, marginBottom: 10 },

  achRow: { flexDirection: 'row', alignItems: 'center', gap: 12, paddingVertical: 12, paddingHorizontal: 16, backgroundColor: colors.white },
  achIcon: { width: 40, height: 40, borderRadius: 9 },
  achName: { flex: 1, fontSize: 15, fontFamily: fonts.bodyM, color: colors.primaryDark },
  achDate: { fontSize: 12, fontFamily: fonts.bodyR, color: colors.textMuted },
  divider: { height: 1, backgroundColor: colors.divider, marginHorizontal: 16 },

  modBtn: { height: 52, borderRadius: radii.button, backgroundColor: colors.white, borderWidth: 1.5, alignItems: 'center', justifyContent: 'center', marginTop: 20 },
  blockBtn: { borderColor: colors.danger },
  unblockBtn: { borderColor: colors.primaryDark },
  modText: { fontFamily: fonts.bodyB, fontSize: 15, fontWeight: '700' },
});
