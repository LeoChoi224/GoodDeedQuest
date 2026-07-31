import React, { useCallback, useEffect, useState } from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { useFocusEffect } from '@react-navigation/native';
import Animated, { FadeInDown } from 'react-native-reanimated';
import HazeBackground from '../../components/HazeBackground';
import MainHeader from '../../components/MainHeader';
import SpringButton from '../../components/SpringButton';
import GdqInput from '../../components/GdqInput';
import BottomSheet from '../../components/BottomSheet';
import SegmentedTabs from '../../components/SegmentedTabs';
import EmptyState from '../../components/EmptyState';
import { useToast } from '../../components/Toast';
import { colors, fonts } from '../../theme';
import {
  createTeam,
  getChallengeErrorMessage,
  getMyTeams,
  TeamListItem,
} from '../../api/challenge';
import { PixelTitle, CatIcon, IconChevRight, StickyFooter, INFO, staggerDelay } from './_parts';

function teamCategory(team: TeamListItem): string {
  const text = `${team.name} ${team.notification}`;
  if (text.includes('환경')) return 'environment';
  if (text.includes('봉사')) return 'volunteer';
  if (text.includes('동물')) return 'animal';
  if (text.includes('나눔')) return 'sharing';
  return 'community';
}

export default function TeamListScreen({ navigation, route }: any) {
  const toast = useToast();
  const [teams, setTeams] = useState<TeamListItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [sheet, setSheet] = useState(false);
  const [creating, setCreating] = useState(false);
  const [name, setName] = useState('');
  const [questId, setQuestId] = useState('');
  const [region, setRegion] = useState('');
  const [notification, setNotification] = useState('잘 부탁드립니다.');
  const [maxMembers, setMaxMembers] = useState('4');
  const [vis, setVis] = useState(0);
  const [pw, setPw] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setTeams(await getMyTeams({ size: 100 }));
    } catch (error) {
      toast.show(getChallengeErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useFocusEffect(useCallback(() => { void load(); }, [load]));

  useEffect(() => {
    if (!route?.params?.openCreate) {
      return;
    }

    setSheet(true);
    navigation.setParams({
      openCreate: false,
    });
  }, [navigation, route?.params?.openCreate]);

  const reset = () => {
    setName(''); setQuestId(''); setRegion(''); setNotification('잘 부탁드립니다.');
    setMaxMembers('4'); setVis(0); setPw('');
  };

  const onCreate = async () => {
    const parsedQuestId = Number(questId);
    const parsedMax = Number(maxMembers);
    if (!name.trim() || !Number.isInteger(parsedQuestId) || parsedQuestId <= 0 || !region.trim()) {
      toast.show('팀 이름, 퀘스트 ID, 활동 지역을 확인해주세요.');
      return;
    }
    if (!Number.isInteger(parsedMax) || parsedMax < 2 || parsedMax > 10) {
      toast.show('최대 인원은 2명부터 10명까지 가능합니다.');
      return;
    }
    if (vis === 1 && pw.trim().length < 4) {
      toast.show('비공개 팀 비밀번호는 4자 이상 입력해주세요.');
      return;
    }

    setCreating(true);
    try {
      const team = await createTeam({
        quest_id: parsedQuestId,
        name: name.trim(),
        password: vis === 1 ? pw.trim() : null,
        notification: notification.trim() || '잘 부탁드립니다.',
        region: region.trim(),
        is_public: vis === 0,
        max_members: parsedMax,
      });
      setSheet(false);
      reset();
      toast.show('팀이 생성되었습니다');
      navigation.navigate('TeamDetail', { teamId: team.team_id });
    } catch (error) {
      toast.show(getChallengeErrorMessage(error));
    } finally {
      setCreating(false);
    }
  };

  return (
    <View style={styles.root}>
      <StatusBar style="light" />
      <HazeBackground />
      <MainHeader showBack title="내 팀" onBack={() => navigation.goBack()} />
      <ScrollView contentContainerStyle={styles.body} showsVerticalScrollIndicator={false}>
        <PixelTitle size={18} style={{ marginBottom: 12 }}>참여 중인 팀</PixelTitle>
        {loading ? <Text style={styles.loading}>불러오는 중...</Text> : teams.length === 0 ? (
          <EmptyState icon="🧭" message="아직 참여 중인 팀이 없어요" subMessage="방 찾기 또는 방 만들기를 이용해보세요" />
        ) : <View style={{ gap: 10 }}>
          {teams.map((team, i) => (
            <Animated.View key={team.team_id} entering={FadeInDown.delay(staggerDelay(i)).duration(450)}>
              <SpringButton pressScale={0.98} style={styles.card} onPress={() => navigation.navigate('TeamDetail', { teamId: team.team_id })}>
                <CatIcon category={teamCategory(team)} />
                <View style={{ flex: 1, minWidth: 0 }}>
                  <Text style={styles.name}>{team.name}</Text>
                  <Text style={styles.info}>{team.region} · {team.current_members}/{team.max_members}명</Text>
                </View>
                <IconChevRight />
              </SpringButton>
            </Animated.View>
          ))}
        </View>}
      </ScrollView>
      <StickyFooter style={styles.footerRow}>
        <SpringButton style={[styles.footerBtn, styles.findBtn]} onPress={() => navigation.navigate('RoomFind')}>
          <Text style={[styles.footerText, { color: colors.primaryDark }]}>방 찾기</Text>
        </SpringButton>
        <SpringButton style={[styles.footerBtn, styles.makeBtn]} onPress={() => setSheet(true)}>
          <Text style={[styles.footerText, { color: colors.white }]}>방 만들기</Text>
        </SpringButton>
      </StickyFooter>

      <BottomSheet visible={sheet} onClose={() => setSheet(false)} title="새 챌린지 팀 만들기">
        <ScrollView style={{ maxHeight: 560 }} contentContainerStyle={styles.form} keyboardShouldPersistTaps="handled">
          <Text style={styles.label}>팀 이름 *</Text>
          <GdqInput value={name} onChangeText={setName} placeholder="팀 이름" />
          <Text style={styles.label}>퀘스트 ID *</Text>
          <GdqInput value={questId} onChangeText={setQuestId} keyboardType="number-pad" placeholder="예: 1" />
          <Text style={styles.label}>활동 지역 *</Text>
          <GdqInput value={region} onChangeText={setRegion} placeholder="예: 서울 마포구" />
          <Text style={styles.label}>팀 공지</Text>
          <GdqInput value={notification} onChangeText={setNotification} placeholder="팀원에게 안내할 내용" />
          <Text style={styles.label}>최대 인원 (2~10)</Text>
          <GdqInput value={maxMembers} onChangeText={setMaxMembers} keyboardType="number-pad" placeholder="4" />
          <Text style={styles.label}>공개 설정</Text>
          <SegmentedTabs tabs={['공개', '비공개']} index={vis} onChange={setVis} />
          {vis === 1 ? <>
            <Text style={styles.label}>비밀번호 *</Text>
            <GdqInput value={pw} onChangeText={setPw} secureTextEntry placeholder="4~20자" />
          </> : null}
          <SpringButton disabled={creating} style={styles.createBtn} onPress={() => void onCreate()}>
            <Text style={styles.createText}>{creating ? '생성 중...' : '팀 생성하기'}</Text>
          </SpringButton>
        </ScrollView>
      </BottomSheet>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.screenBg },
  body: { paddingHorizontal: 16, paddingTop: 14, paddingBottom: 140 },
  loading: { textAlign: 'center', color: colors.textMuted, marginTop: 40, fontFamily: fonts.bodyR },
  card: { flexDirection: 'row', alignItems: 'center', gap: 12, backgroundColor: colors.white, borderWidth: 1, borderColor: colors.pixelBorder, borderRadius: 12, padding: 12 },
  name: { fontSize: 15, fontWeight: '600', color: colors.primaryDark, fontFamily: fonts.bodyM },
  info: { fontSize: 13, color: INFO, marginTop: 3, fontFamily: fonts.bodyR },
  footerRow: { flexDirection: 'row', gap: 10 },
  footerBtn: { flex: 1, height: 52, borderRadius: 8, alignItems: 'center', justifyContent: 'center' },
  findBtn: { backgroundColor: colors.screenBg, borderWidth: 1, borderColor: colors.pixelBorder },
  makeBtn: { backgroundColor: colors.xpGreen },
  footerText: { fontFamily: fonts.pixel, fontSize: 16 },
  form: { gap: 8, paddingBottom: 24 },
  label: { marginTop: 8, fontFamily: fonts.bodyB, color: colors.primaryDark, fontSize: 13 },
  createBtn: { height: 50, borderRadius: 8, backgroundColor: colors.xpGreen, alignItems: 'center', justifyContent: 'center', marginTop: 16 },
  createText: { color: colors.white, fontFamily: fonts.pixel, fontSize: 16 },
});
