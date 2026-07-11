/**
 * SCREEN 3 · 팀 상세 (route: TeamDetail, params: { room?, role? }).
 * RBAC(방장/팀원): 헤더 우측 데모 토글로 역할 전환.
 *  · 방장 "유저 초대하기" → 유저 추천 리스트(Screen 4, in-screen sub-view)
 *  · 팀원 "유저 초대하기" → 초대 이용불가 팝업(3A)
 * 추천 리스트의 "초대하기" → 초대 확인 팝업(4A). "추천 다시받기" → shimmer 로딩 후 갱신.
 * 팝업 3종 = GamePopup(다크 딤). 방장 별 = pulse/tilt.
 */
import React, { useState } from 'react';
import { View, Text, Image, StyleSheet, ScrollView, Pressable, useWindowDimensions } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import Animated, { FadeInDown } from 'react-native-reanimated';
import HazeBackground from '../../components/HazeBackground';
import MainHeader from '../../components/MainHeader';
import SpringButton from '../../components/SpringButton';
import GamePopup from '../../components/GamePopup';
import LightPopup from '../../components/LightPopup';
import Shimmer from '../../components/Shimmer';
import { useToast } from '../../components/Toast';
import { colors, fonts, brand } from '../../theme';
import {
  MEMBERS,
  RECOMMEND_USERS,
  AVATARS,
  Avatar,
  StarPulse,
  PixelTitle,
  SearchSortBar,
  StickyFooter,
  PopupTealBtn,
  PopupOutlineBtn,
  IconMega,
  POPUP_CREAM,
  INFO,
  CARD_DIVIDER,
  staggerDelay,
} from './_parts';

type Role = 'leader' | 'member';

export default function TeamDetailScreen({ navigation, route }: any) {
  const { width } = useWindowDimensions();
  const toast = useToast();
  const teamName: string = route?.params?.room?.name ?? '지구지킴이 원정대';

  // 실서비스에선 API에서 역할을 받아온다. params.role 없으면 방장(leader) 기본.
  const role: Role = route?.params?.role === 'member' ? 'member' : 'leader';
  const [view, setView] = useState<'detail' | 'recommend'>('detail');
  const [block, setBlock] = useState(false);
  const [confirmUser, setConfirmUser] = useState<string | null>(null);
  const [reloading, setReloading] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);

  const popupW = Math.min(360, width - 48);

  const onInvite = () => {
    if (role === 'leader') setView('recommend');
    else setBlock(true);
  };

  const onReload = () => {
    setReloading(true);
    setTimeout(() => {
      setReloading(false);
      setReloadKey((k) => k + 1);
    }, 900);
  };

  return (
    <View style={styles.root}>
      <StatusBar style="dark" />
      <HazeBackground />

      {view === 'detail' ? (
        <MainHeader showBack title="팀 상세" onBack={() => navigation.goBack()} />
      ) : (
        <MainHeader showBack title="유저 추천" onBack={() => setView('detail')} />
      )}

      {view === 'detail' ? (
        <>
          <ScrollView contentContainerStyle={styles.body} showsVerticalScrollIndicator={false}>
            {/* 팀 공지 배너 */}
            <View style={styles.notice}>
              <IconMega />
              <Text style={styles.noticeLabel}>팀 공지 :</Text>
              <Text style={styles.noticeText}>이번 주 목표는 환경 퀘스트 20개!</Text>
            </View>

            <PixelTitle size={20}>{teamName}</PixelTitle>
            <Text style={styles.teamSub}>환경 · 함께 동네를 지켜요</Text>

            {/* 방장 */}
            <PixelTitle size={14} color={colors.gold} style={{ marginBottom: 8 }}>
              방장
            </PixelTitle>
            <View style={styles.leaderCard}>
              <Avatar grad={AVATARS[0]} size={48} child={<Image source={brand.appIcon} style={styles.leaderImg} />} />
              <View style={{ flex: 1 }}>
                <Text style={styles.leaderName}>선한김철수</Text>
                <Text style={styles.leaderMeta}>마을 수호자 · LV.12</Text>
              </View>
              <StarPulse />
            </View>

            {/* 팀원 */}
            <PixelTitle size={14} style={{ marginBottom: 8 }}>
              팀원
            </PixelTitle>
            <View style={styles.memberList}>
              {MEMBERS.map((m, i) => (
                <Animated.View
                  key={m.name}
                  entering={FadeInDown.delay(staggerDelay(i)).duration(400)}
                  style={[styles.memberRow, i === MEMBERS.length - 1 && { borderBottomWidth: 0 }]}
                >
                  <Pressable style={styles.memberInner} onPress={() => navigation.navigate('UserDetail', { user: m })}>
                    <Avatar grad={m.grad} size={34} />
                    <Text style={styles.memberName}>{m.name}</Text>
                    <Text style={styles.memberLv}>LV.{m.lv}</Text>
                  </Pressable>
                </Animated.View>
              ))}
            </View>

            <Pressable style={styles.questLinkWrap} onPress={() => toast.show('퀘스트 상세는 준비 중입니다')}>
              <Text style={styles.questLink}>퀘스트 자세히 보기</Text>
            </Pressable>
          </ScrollView>

          <StickyFooter style={styles.footerRow}>
            <SpringButton style={[styles.footBtn, styles.inviteBtn]} onPress={onInvite}>
              <Text style={[styles.footText, { color: colors.white }]}>유저 초대하기</Text>
            </SpringButton>
            {role === 'leader' ? (
              <SpringButton style={[styles.footBtn, styles.leaveBtn]} onPress={() => navigation.goBack()}>
                <Text style={[styles.footText, { color: colors.primaryDark }]}>팀 나가기</Text>
              </SpringButton>
            ) : (
              <SpringButton style={[styles.footBtn, styles.leaveBtn]} onPress={() => navigation.navigate('TeamList')}>
                <Text style={[styles.footText, { color: colors.primaryDark }]}>팀 목록</Text>
              </SpringButton>
            )}
          </StickyFooter>
        </>
      ) : (
        <>
          {/* SCREEN 4 · 유저 추천 리스트 */}
          <ScrollView contentContainerStyle={styles.body} showsVerticalScrollIndicator={false}>
            <PixelTitle size={18}>챌린지팀 유저 추천 리스트</PixelTitle>
            <Text style={styles.recSub}>AI 분석한 사용자의 성향 정보가 나옵니다.</Text>
            <SearchSortBar placeholder="아이디 또는 닉네임" sortLabel="닉네임" />

            {reloading ? (
              <View style={{ gap: 10 }}>
                {[0, 1, 2, 3].map((i) => (
                  <View key={i} style={styles.userCard}>
                    <Shimmer width={48} height={48} radius={24} />
                    <View style={{ flex: 1, gap: 8 }}>
                      <Shimmer width={'60%'} height={13} />
                      <Shimmer width={'85%'} height={11} />
                    </View>
                  </View>
                ))}
              </View>
            ) : (
              <View style={{ gap: 10 }}>
                {RECOMMEND_USERS.map((u, i) => (
                  <Animated.View
                    key={`${u.name}-${reloadKey}`}
                    entering={FadeInDown.delay(staggerDelay(i)).duration(450)}
                    style={styles.userCard}
                  >
                    <Pressable style={styles.userCardBody} onPress={() => navigation.navigate('UserDetail', { user: u })}>
                      <Avatar grad={u.grad} size={48} />
                      <View style={{ flex: 1, minWidth: 0 }}>
                        <Text style={styles.userName}>{u.name}</Text>
                        <Text style={styles.userInfo}>{u.info}</Text>
                      </View>
                    </Pressable>
                    <SpringButton style={styles.userInviteBtn} onPress={() => setConfirmUser(u.name)}>
                      <Text style={styles.userInviteText}>초대하기</Text>
                    </SpringButton>
                  </Animated.View>
                ))}
              </View>
            )}
          </ScrollView>

          <StickyFooter>
            <SpringButton style={styles.reloadBtn} onPress={onReload}>
              <Text style={styles.reloadText}>추천 다시받기</Text>
            </SpringButton>
          </StickyFooter>
        </>
      )}

      {/* SCREEN 3-A · 초대 이용불가 (팀원) — 라이트 팝업 (기능성 안내) */}
      <LightPopup visible={block} onClose={() => setBlock(false)} width={popupW}>
        <View style={styles.popupContent}>
          <Text style={styles.blockText}>유저 초대하기 기능은{'\n'}방장만 이용할 수 있습니다.</Text>
          <View style={styles.popupBtnRow}>
            <PopupTealBtn label="돌아가기" onPress={() => setBlock(false)} />
          </View>
        </View>
      </LightPopup>

      {/* SCREEN 4-A · 초대 확인 */}
      <GamePopup visible={!!confirmUser} onClose={() => setConfirmUser(null)} width={popupW}>
        <View style={styles.popupContent}>
          <PixelTitle size={16} color={POPUP_CREAM} style={{ textAlign: 'center', marginBottom: 20 }}>
            팀에 초대하시겠습니까?
          </PixelTitle>
          <View style={styles.popupBtnRow}>
            <PopupTealBtn
              label="예"
              onPress={() => {
                setConfirmUser(null);
                toast.show('초대 요청을 보냈습니다');
              }}
            />
            <PopupOutlineBtn label="아니오" onPress={() => setConfirmUser(null)} />
          </View>
        </View>
      </GamePopup>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.screenBg },
  body: { paddingHorizontal: 16, paddingTop: 14, paddingBottom: 140 },
  // notice banner
  notice: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: colors.parchment,
    borderWidth: 1,
    borderColor: colors.pixelBorder,
    borderRadius: 8,
    paddingHorizontal: 14,
    paddingVertical: 10,
    marginBottom: 14,
  },
  noticeLabel: { fontSize: 12, fontWeight: '700', color: colors.primaryDark, fontFamily: fonts.bodyB },
  noticeText: { flex: 1, fontSize: 13, color: colors.primaryDark, fontFamily: fonts.bodyR },
  teamSub: { fontSize: 13, color: INFO, marginTop: 2, marginBottom: 14, fontFamily: fonts.bodyR },
  // leader card
  leaderCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    backgroundColor: colors.parchment,
    borderWidth: 1,
    borderColor: colors.pixelBorder,
    borderRadius: 12,
    padding: 12,
    marginBottom: 16,
  },
  leaderImg: { width: 48, height: 48 },
  leaderName: { fontSize: 15, fontWeight: '600', color: colors.primaryDark, fontFamily: fonts.bodyM },
  leaderMeta: { fontSize: 13, color: colors.gold, fontFamily: fonts.bodyR },
  // member list
  memberList: {
    backgroundColor: colors.white,
    borderRadius: 12,
    overflow: 'hidden',
    marginBottom: 14,
    shadowColor: colors.primaryDark,
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.06,
    shadowRadius: 8,
    elevation: 2,
  },
  memberRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    paddingHorizontal: 14,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: CARD_DIVIDER,
  },
  memberInner: { flex: 1, flexDirection: 'row', alignItems: 'center', gap: 10 },
  memberName: { flex: 1, fontSize: 15, color: colors.primaryDark, fontFamily: fonts.bodyR },
  memberLv: { fontFamily: fonts.pixel, fontSize: 13, color: INFO },
  questLinkWrap: { alignItems: 'center', marginBottom: 6 },
  questLink: { fontSize: 14, color: colors.gold, textDecorationLine: 'underline', fontFamily: fonts.bodyM },
  // footer
  footerRow: { flexDirection: 'row', gap: 10 },
  footBtn: { flex: 1, height: 50, borderRadius: 8, alignItems: 'center', justifyContent: 'center' },
  inviteBtn: { backgroundColor: colors.xpGreen },
  leaveBtn: { backgroundColor: colors.screenBg, borderWidth: 1, borderColor: colors.pixelBorder },
  footText: { fontFamily: fonts.pixel, fontSize: 15 },
  // recommend list
  recSub: { fontSize: 13, color: INFO, marginTop: 2, marginBottom: 14, fontFamily: fonts.bodyR },
  userCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    backgroundColor: colors.white,
    borderWidth: 1,
    borderColor: colors.pixelBorder,
    borderRadius: 12,
    padding: 12,
    shadowColor: colors.pixelBorder,
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 2,
  },
  userCardBody: { flex: 1, flexDirection: 'row', alignItems: 'center', gap: 12, minWidth: 0 },
  userName: { fontSize: 15, fontWeight: '600', color: colors.primaryDark, fontFamily: fonts.bodyM },
  userInfo: { fontSize: 13, color: INFO, fontFamily: fonts.bodyR },
  userInviteBtn: { backgroundColor: colors.xpGreen, borderRadius: 8, paddingHorizontal: 14, paddingVertical: 8 },
  userInviteText: { fontFamily: fonts.pixel, fontSize: 13, color: colors.white },
  reloadBtn: {
    height: 52,
    borderRadius: 8,
    backgroundColor: colors.screenBg,
    borderWidth: 1.5,
    borderColor: colors.pixelBorder,
    alignItems: 'center',
    justifyContent: 'center',
  },
  reloadText: { fontFamily: fonts.pixel, fontSize: 16, color: colors.primaryDark },
  // popups
  popupContent: { alignSelf: 'stretch', width: '100%' },
  blockText: {
    textAlign: 'center',
    fontFamily: fonts.pixel,
    fontSize: 16,
    color: colors.primaryDark,
    lineHeight: 26,
    marginBottom: 20,
  },
  popupBtnRow: { flexDirection: 'row', gap: 10 },
});
