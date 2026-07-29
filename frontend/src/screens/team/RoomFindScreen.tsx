import React, { useCallback, useMemo, useState } from 'react';
import { View, Text, StyleSheet, ScrollView, useWindowDimensions } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { useFocusEffect } from '@react-navigation/native';
import Animated, { FadeInDown } from 'react-native-reanimated';
import HazeBackground from '../../components/HazeBackground';
import MainHeader from '../../components/MainHeader';
import SpringButton from '../../components/SpringButton';
import GdqInput from '../../components/GdqInput';
import LightPopup from '../../components/LightPopup';
import Shake from '../../components/Shake';
import EmptyState from '../../components/EmptyState';
import { useToast } from '../../components/Toast';
import { colors, fonts } from '../../theme';
import {
  getChallengeErrorMessage,
  getTeams,
  TeamListItem,
  TeamSort,
} from '../../api/challenge';
import {
  PixelTitle,
  CatIcon,
  IconLock,
  StickyFooter,
  PopupTealBtn,
  ERR_TEXT,
  ERR_BORDER,
  INFO,
  staggerDelay,
} from './_parts';

function categoryFor(team: TeamListItem): string {
  const text = `${team.name} ${team.notification}`.toLowerCase();
  if (text.includes('동물')) return 'animal';
  if (text.includes('환경') || text.includes('플로깅')) return 'environment';
  if (text.includes('봉사')) return 'volunteer';
  if (text.includes('나눔')) return 'sharing';
  return 'community';
}

export default function RoomFindScreen({ navigation }: any) {
  const toast = useToast();
  const { width } = useWindowDimensions();
  const [teams, setTeams] = useState<TeamListItem[]>([]);
  const [search, setSearch] = useState('');
  const [sortBy, setSortBy] = useState<TeamSort>('latest');
  const [loading, setLoading] = useState(false);
  const [pwTeam, setPwTeam] = useState<TeamListItem | null>(null);
  const [pw, setPw] = useState('');
  const [err, setErr] = useState(false);
  const [shake, setShake] = useState(0);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setTeams(await getTeams({ search: search.trim() || undefined, sort_by: sortBy, size: 100 }));
    } catch (error) {
      toast.show(getChallengeErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }, [search, sortBy, toast]);

  useFocusEffect(useCallback(() => { void load(); }, [load]));
  const visibleTeams = useMemo(() => teams.filter((team) => team.status === 'RECRUITING'), [teams]);

  const openTeam = (team: TeamListItem) => {
    if (!team.is_public) {
      setPw('');
      setErr(false);
      setPwTeam(team);
      return;
    }
    navigation.navigate('TeamDetail', { teamId: team.team_id });
  };

  const submitPw = () => {
    if (!pwTeam) return;
    if (pw.trim().length < 4) {
      setErr(true);
      setShake((value) => value + 1);
      return;
    }
    const teamId = pwTeam.team_id;
    setPwTeam(null);
    navigation.navigate('TeamDetail', { teamId, joinPassword: pw.trim() });
  };

  return (
    <View style={styles.root}>
      <StatusBar style="light" />
      <HazeBackground />
      <MainHeader showBack title="방 찾기" onBack={() => navigation.goBack()} />
      <ScrollView contentContainerStyle={styles.body} showsVerticalScrollIndicator={false}>
      <View style={styles.searchRow}>
        <View style={styles.searchInputWrap}>
          <GdqInput
            value={search}
            onChangeText={setSearch}
            placeholder="방 이름 검색"
          />
        </View>

        <SpringButton
          style={styles.searchBtn}
          onPress={() => void load()}
        >
          <Text style={styles.searchText}>검색</Text>
        </SpringButton>
      </View>
        <SpringButton style={styles.sortBtn} onPress={() => setSortBy((v) => v === 'latest' ? 'name' : 'latest')}>
          <Text style={styles.sortText}>{sortBy === 'latest' ? '최신순' : '이름순'}</Text>
        </SpringButton>
        <PixelTitle size={16} style={{ marginBottom: 12 }}>모집 중인 방</PixelTitle>
        {loading ? <Text style={styles.loading}>불러오는 중...</Text> : visibleTeams.length === 0 ? (
          <EmptyState icon="📜" message="현재 참여 가능한 방이 없어요" subMessage="방 만들기로 새 팀을 시작해보세요" />
        ) : <View style={{ gap: 10 }}>
          {visibleTeams.map((team, i) => (
            <Animated.View key={team.team_id} entering={FadeInDown.delay(staggerDelay(i)).duration(450)}>
              <SpringButton onPress={() => openTeam(team)} pressScale={0.98} style={styles.card}>
                <CatIcon category={categoryFor(team)} />
                <View style={styles.cardBody}>
                  <Text style={styles.roomName}>{team.name}</Text>
                  <Text style={styles.roomInfo}>{team.region} · 퀘스트 #{team.quest_id}</Text>
                  <Text style={styles.roomCount}>({team.current_members}/{team.max_members})</Text>
                </View>
                {!team.is_public ? <View style={styles.lock}><IconLock /></View> : null}
              </SpringButton>
            </Animated.View>
          ))}
        </View>}
      </ScrollView>
      <StickyFooter>
        <SpringButton style={styles.makeBtn} onPress={() => navigation.navigate('TeamList', { openCreate: true })}>
          <Text style={styles.makeText}>방 만들기</Text>
        </SpringButton>
      </StickyFooter>
      <LightPopup visible={!!pwTeam} onClose={() => setPwTeam(null)} width={Math.min(360, width - 48)}>
        <View style={styles.pwContent}>
          {err ? <Text style={styles.pwErr}>비밀번호는 4자 이상 입력해주세요.</Text> : null}
          <PixelTitle size={16} color={colors.primaryDark} style={styles.pwTitle}>비밀번호 입력</PixelTitle>
          <Shake trigger={shake}>
            <View style={[styles.pwRing, err && { borderColor: ERR_BORDER }]}>
              <GdqInput value={pw} onChangeText={(value) => { setPw(value); setErr(false); }} secureTextEntry autoFocus placeholder="••••" style={styles.pwInput} />
            </View>
          </Shake>
          <View style={styles.pwBtnRow}><PopupTealBtn label="상세 보기" onPress={submitPw} /></View>
        </View>
      </LightPopup>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.screenBg },
  body: { paddingHorizontal: 16, paddingTop: 14, paddingBottom: 130 },
  searchRow: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 8,
  },
  searchInputWrap: {
    flex: 1,
    minWidth: 0,
  },
  searchBtn: {
    backgroundColor: colors.primaryDark,
    borderRadius: 8,
    paddingHorizontal: 16,
    justifyContent: 'center',
  },
  searchText: { color: colors.white, fontFamily: fonts.pixel },
  sortBtn: { alignSelf: 'flex-end', paddingVertical: 8, paddingHorizontal: 12, marginBottom: 12 },
  sortText: { color: colors.primaryDark, fontFamily: fonts.bodyB, fontSize: 12 },
  loading: { textAlign: 'center', marginTop: 40, color: colors.textMuted, fontFamily: fonts.bodyR },
  card: { flexDirection: 'row', alignItems: 'center', gap: 12, backgroundColor: colors.white, borderWidth: 1, borderColor: colors.pixelBorder, borderRadius: 12, padding: 12 },
  cardBody: { flex: 1, minWidth: 0 },
  roomName: { fontSize: 15, fontWeight: '600', color: colors.primaryDark, fontFamily: fonts.bodyM },
  roomInfo: { fontSize: 13, color: INFO, marginTop: 1, marginBottom: 3, fontFamily: fonts.bodyR },
  roomCount: { fontFamily: fonts.pixel, fontSize: 12, color: colors.gold },
  lock: { position: 'absolute', top: 10, right: 10 },
  makeBtn: { height: 52, borderRadius: 8, backgroundColor: colors.gold, alignItems: 'center', justifyContent: 'center' },
  makeText: { fontFamily: fonts.pixel, fontSize: 18, color: colors.primaryDark },
  pwContent: { alignSelf: 'stretch', width: '100%' },
  pwErr: { textAlign: 'center', fontSize: 13, color: ERR_TEXT, marginBottom: 8, fontFamily: fonts.bodyR },
  pwTitle: { textAlign: 'center', marginBottom: 16 },
  pwRing: { borderWidth: 1.5, borderColor: 'transparent', borderRadius: 14, padding: 3 },
  pwInput: { textAlign: 'center', letterSpacing: 6 },
  pwBtnRow: { flexDirection: 'row', marginTop: 16 },
});
