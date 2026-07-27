import React, { useCallback, useMemo, useState } from 'react';
import { View, Text, StyleSheet, ScrollView, useWindowDimensions } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { useFocusEffect } from '@react-navigation/native';
import Animated, { FadeInDown } from 'react-native-reanimated';
import HazeBackground from '../../components/HazeBackground';
import MainHeader from '../../components/MainHeader';
import SpringButton from '../../components/SpringButton';
import GamePopup from '../../components/GamePopup';
import LightPopup from '../../components/LightPopup';
import EmptyState from '../../components/EmptyState';
import { useToast } from '../../components/Toast';
import { colors, fonts } from '../../theme';
import {
  createTeamInvite,
  getChallengeErrorMessage,
  getMyTeams,
  getTeamDetail,
  getTeamMembers,
  getTeamRecommendations,
  joinTeam,
  leaveTeam,
  RecommendedUser,
  TeamDetail,
  TeamMember,
} from '../../api/challenge';
import {
  Avatar,
  AVATARS,
  IconLock,
  IconMega,
  PixelTitle,
  PopupOutlineBtn,
  PopupTealBtn,
  SearchSortBar,
  StarPulse,
  StickyFooter,
  INFO,
  POPUP_CREAM,
  staggerDelay,
} from './_parts';

export default function TeamDetailScreen({ navigation, route }: any) {
  const toast = useToast();
  const { width } = useWindowDimensions();
  const teamId = Number(route?.params?.teamId);
  const initialPassword = route?.params?.joinPassword as string | undefined;
  const [team, setTeam] = useState<TeamDetail | null>(null);
  const [members, setMembers] = useState<TeamMember[]>([]);
  const [recommendations, setRecommendations] = useState<RecommendedUser[]>([]);
  const [isMember, setIsMember] = useState(false);
  const [loading, setLoading] = useState(false);
  const [view, setView] = useState<'detail' | 'recommend'>('detail');
  const [confirmUser, setConfirmUser] = useState<RecommendedUser | null>(null);
  const [confirmLeave, setConfirmLeave] = useState(false);
  const [joining, setJoining] = useState(false);
  const [reloading, setReloading] = useState(false);

  const popupW = Math.min(360, width - 48);

  const load = useCallback(async () => {
    if (!Number.isInteger(teamId) || teamId <= 0) {
      toast.show('올바른 팀 정보가 없습니다.');
      navigation.goBack();
      return;
    }
    setLoading(true);
    try {
      const [detail, teamMembers] = await Promise.all([getTeamDetail(teamId), getTeamMembers(teamId)]);
      setTeam(detail);
      setMembers(teamMembers);
      try {
        const myTeams = await getMyTeams({ size: 100 });
        setIsMember(myTeams.some((item) => item.team_id === teamId));
      } catch {
        setIsMember(false);
      }
    } catch (error) {
      toast.show(getChallengeErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }, [navigation, teamId, toast]);

  useFocusEffect(useCallback(() => { void load(); }, [load]));

  const leader = useMemo(() => members.find((member) => member.role_in_team === 'LEADER'), [members]);
  const normalMembers = useMemo(() => members.filter((member) => member.role_in_team !== 'LEADER'), [members]);

  const onJoin = async () => {
    setJoining(true);
    try {
      await joinTeam(teamId, initialPassword);
      toast.show('팀에 참가했습니다');
      await load();
    } catch (error) {
      toast.show(getChallengeErrorMessage(error));
    } finally {
      setJoining(false);
    }
  };

  const onLeave = async () => {
    setConfirmLeave(false);
    try {
      await leaveTeam(teamId);
      toast.show('팀에서 나갔습니다');
      navigation.navigate('TeamList');
    } catch (error) {
      toast.show(getChallengeErrorMessage(error));
    }
  };

  const loadRecommendations = async () => {
    setReloading(true);
    try {
      const result = await getTeamRecommendations(teamId, 10);
      setRecommendations(result.recommendations);
      setView('recommend');
      if (result.warnings.length) toast.show(result.warnings[0]);
    } catch (error) {
      toast.show(getChallengeErrorMessage(error));
    } finally {
      setReloading(false);
    }
  };

  const invite = async () => {
    if (!confirmUser) return;
    const user = confirmUser;
    setConfirmUser(null);
    try {
      await createTeamInvite(teamId, user.user_id);
      toast.show(`${user.nickname ?? `사용자 #${user.user_id}`}님에게 초대를 보냈습니다`);
    } catch (error) {
      toast.show(getChallengeErrorMessage(error));
    }
  };

  if (loading && !team) {
    return <View style={styles.root}><HazeBackground /><MainHeader showBack title="팀 상세" onBack={() => navigation.goBack()} /><Text style={styles.loading}>팀 정보를 불러오는 중...</Text></View>;
  }

  return (
    <View style={styles.root}>
      <StatusBar style="light" />
      <HazeBackground />
      <MainHeader showBack title={view === 'detail' ? '팀 상세' : 'AI 유저 추천'} onBack={() => view === 'recommend' ? setView('detail') : navigation.goBack()} />

      {view === 'detail' ? <>
        <ScrollView contentContainerStyle={styles.body} showsVerticalScrollIndicator={false}>
          {team ? <>
            <View style={styles.notice}><IconMega /><Text style={styles.noticeText}>{team.notification}</Text></View>
            <View style={styles.titleRow}>
              <PixelTitle size={21}>{team.name}</PixelTitle>
              {!team.is_public ? <IconLock /> : null}
            </View>
            <Text style={styles.teamSub}>{team.region} · 퀘스트 #{team.quest_id} · {team.current_members}/{team.max_members}명</Text>
            <Text style={styles.status}>상태: {team.status}</Text>

            <PixelTitle size={14} style={{ marginBottom: 8 }}>방장</PixelTitle>
            {leader ? <View style={styles.leaderCard}>
              <Avatar grad={AVATARS[0]} size={48} />
              <View style={{ flex: 1 }}><Text style={styles.leaderName}>사용자 #{leader.user_id}</Text><Text style={styles.leaderMeta}>팀장</Text></View>
              <StarPulse />
            </View> : <Text style={styles.emptyText}>팀장 정보를 찾을 수 없습니다.</Text>}

            <PixelTitle size={14} style={{ marginBottom: 8 }}>팀원</PixelTitle>
            <View style={styles.memberList}>
              {normalMembers.length === 0 ? <Text style={styles.emptyText}>아직 참가한 팀원이 없습니다.</Text> : normalMembers.map((member, i) => (
                <Animated.View key={member.team_member_id} entering={FadeInDown.delay(staggerDelay(i)).duration(400)} style={styles.memberRow}>
                  <Avatar grad={AVATARS[(i + 1) % AVATARS.length]} size={34} />
                  <Text style={styles.memberName}>사용자 #{member.user_id}</Text>
                  <Text style={styles.memberRole}>{member.role_in_team}</Text>
                </Animated.View>
              ))}
            </View>
          </> : <EmptyState icon="⚠️" message="팀 정보를 불러오지 못했습니다" />}
        </ScrollView>

        <StickyFooter style={styles.footerRow}>
          {!isMember ? <SpringButton disabled={joining} style={[styles.footBtn, styles.joinBtn]} onPress={() => void onJoin()}>
            <Text style={[styles.footText, { color: colors.white }]}>{joining ? '참가 중...' : '팀 참가하기'}</Text>
          </SpringButton> : <>
            <SpringButton style={[styles.footBtn, styles.inviteBtn]} onPress={() => void loadRecommendations()}>
              <Text style={[styles.footText, { color: colors.white }]}>{reloading ? '분석 중...' : 'AI 유저 추천'}</Text>
            </SpringButton>
            <SpringButton style={[styles.footBtn, styles.leaveBtn]} onPress={() => setConfirmLeave(true)}>
              <Text style={[styles.footText, { color: colors.primaryDark }]}>팀 나가기</Text>
            </SpringButton>
          </>}
        </StickyFooter>
      </> : <>
        <ScrollView contentContainerStyle={styles.body} showsVerticalScrollIndicator={false}>
          <PixelTitle size={18}>챌린지팀 유저 추천 리스트</PixelTitle>
          <Text style={styles.recSub}>규칙 기반 점수와 AI 추천 이유를 함께 확인할 수 있습니다.</Text>
          <SearchSortBar placeholder="추천 결과" sortLabel="점수순" />
          {recommendations.length === 0 ? <EmptyState icon="🤖" message="추천 가능한 사용자가 없어요" /> : <View style={{ gap: 10 }}>
            {recommendations.map((user, i) => (
              <Animated.View key={user.user_id} entering={FadeInDown.delay(staggerDelay(i)).duration(450)} style={styles.userCard}>
                <Avatar grad={AVATARS[i % AVATARS.length]} size={48} />
                <View style={{ flex: 1, minWidth: 0 }}>
                  <Text style={styles.userName}>#{user.rank} {user.nickname ?? `사용자 ${user.user_id}`}</Text>
                  <Text style={styles.score}>{user.score.total_score.toFixed(1)}점 · LV.{user.current_level}</Text>
                  <Text style={styles.userInfo}>{user.recommendation_reason}</Text>
                </View>
                <SpringButton style={styles.userInviteBtn} onPress={() => setConfirmUser(user)}><Text style={styles.userInviteText}>초대</Text></SpringButton>
              </Animated.View>
            ))}
          </View>}
        </ScrollView>
        <StickyFooter><SpringButton disabled={reloading} style={styles.reloadBtn} onPress={() => void loadRecommendations()}><Text style={styles.reloadText}>{reloading ? '추천 분석 중...' : '추천 다시받기'}</Text></SpringButton></StickyFooter>
      </>}

      <GamePopup visible={!!confirmUser} onClose={() => setConfirmUser(null)} width={popupW}>
        <View style={styles.popupContent}>
          <PixelTitle size={16} color={POPUP_CREAM} style={{ textAlign: 'center', marginBottom: 20 }}>팀에 초대하시겠습니까?</PixelTitle>
          <View style={styles.popupBtnRow}><PopupTealBtn label="예" onPress={() => void invite()} /><PopupOutlineBtn label="아니오" onPress={() => setConfirmUser(null)} /></View>
        </View>
      </GamePopup>
      <LightPopup visible={confirmLeave} onClose={() => setConfirmLeave(false)} width={popupW}>
        <View style={styles.popupContent}>
          <Text style={styles.leaveText}>정말 팀에서 나가시겠습니까?{leader ? '\n팀장이라면 가장 먼저 참가한 팀원에게 권한이 위임됩니다.' : ''}</Text>
          <View style={styles.popupBtnRow}><PopupTealBtn label="나가기" onPress={() => void onLeave()} /><PopupOutlineBtn label="취소" onPress={() => setConfirmLeave(false)} /></View>
        </View>
      </LightPopup>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.screenBg },
  loading: { textAlign: 'center', marginTop: 80, color: colors.textMuted, fontFamily: fonts.bodyR },
  body: { paddingHorizontal: 16, paddingTop: 14, paddingBottom: 140 },
  notice: { flexDirection: 'row', alignItems: 'center', gap: 8, backgroundColor: colors.parchment, borderWidth: 1, borderColor: colors.pixelBorder, borderRadius: 8, padding: 12, marginBottom: 14 },
  noticeText: { flex: 1, fontSize: 13, color: colors.primaryDark, fontFamily: fonts.bodyR },
  titleRow: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  teamSub: { fontSize: 13, color: INFO, marginTop: 4, fontFamily: fonts.bodyR },
  status: { fontSize: 12, color: colors.gold, marginTop: 4, marginBottom: 14, fontFamily: fonts.bodyM },
  leaderCard: { flexDirection: 'row', alignItems: 'center', gap: 12, backgroundColor: colors.parchment, borderWidth: 1, borderColor: colors.pixelBorder, borderRadius: 12, padding: 12, marginBottom: 16 },
  leaderName: { fontSize: 15, fontWeight: '600', color: colors.primaryDark, fontFamily: fonts.bodyM },
  leaderMeta: { fontSize: 13, color: colors.gold, fontFamily: fonts.bodyR },
  memberList: { backgroundColor: colors.white, borderRadius: 12, overflow: 'hidden', marginBottom: 14 },
  memberRow: { flexDirection: 'row', alignItems: 'center', gap: 10, padding: 12, borderBottomWidth: 1, borderBottomColor: colors.pixelBorder },
  memberName: { flex: 1, fontSize: 15, color: colors.primaryDark, fontFamily: fonts.bodyR },
  memberRole: { fontSize: 11, color: INFO, fontFamily: fonts.pixel },
  emptyText: { padding: 14, color: colors.textMuted, fontFamily: fonts.bodyR },
  footerRow: { flexDirection: 'row', gap: 10 },
  footBtn: { flex: 1, height: 50, borderRadius: 8, alignItems: 'center', justifyContent: 'center' },
  inviteBtn: { backgroundColor: colors.xpGreen },
  joinBtn: { backgroundColor: colors.xpGreen },
  leaveBtn: { backgroundColor: colors.screenBg, borderWidth: 1, borderColor: colors.pixelBorder },
  footText: { fontFamily: fonts.pixel, fontSize: 15 },
  recSub: { fontSize: 13, color: INFO, marginTop: 2, marginBottom: 14, fontFamily: fonts.bodyR },
  userCard: { flexDirection: 'row', alignItems: 'center', gap: 12, backgroundColor: colors.white, borderWidth: 1, borderColor: colors.pixelBorder, borderRadius: 12, padding: 12 },
  userName: { fontSize: 15, fontWeight: '600', color: colors.primaryDark, fontFamily: fonts.bodyM },
  score: { fontSize: 12, color: colors.gold, fontFamily: fonts.bodyB, marginTop: 2 },
  userInfo: { fontSize: 12, color: INFO, fontFamily: fonts.bodyR, marginTop: 3 },
  userInviteBtn: { backgroundColor: colors.xpGreen, borderRadius: 8, paddingHorizontal: 12, paddingVertical: 8 },
  userInviteText: { fontFamily: fonts.pixel, fontSize: 12, color: colors.white },
  reloadBtn: { height: 52, borderRadius: 8, backgroundColor: colors.screenBg, borderWidth: 1.5, borderColor: colors.pixelBorder, alignItems: 'center', justifyContent: 'center' },
  reloadText: { fontFamily: fonts.pixel, fontSize: 16, color: colors.primaryDark },
  popupContent: { alignSelf: 'stretch', width: '100%' },
  popupBtnRow: { flexDirection: 'row', gap: 10 },
  leaveText: { textAlign: 'center', color: colors.primaryDark, fontFamily: fonts.bodyR, lineHeight: 22, marginBottom: 18 },
});
