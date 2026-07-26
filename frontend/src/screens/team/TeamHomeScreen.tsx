import React, { useCallback, useState } from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { useFocusEffect } from '@react-navigation/native';
import HazeBackground from '../../components/HazeBackground';
import MainHeader from '../../components/MainHeader';
import SpringButton from '../../components/SpringButton';
import EmptyState from '../../components/EmptyState';
import { useToast } from '../../components/Toast';
import { colors, fonts } from '../../theme';
import {
  getChallengeErrorMessage,
  getMyInvites,
  respondTeamInvite,
  TeamInvite,
} from '../../api/challenge';
import { PopupGoldBtn, PopupTealBtn, PixelTitle } from './_parts';

export default function TeamHomeScreen({ navigation }: any) {
  const toast = useToast();
  const [invites, setInvites] = useState<TeamInvite[]>([]);
  const [loading, setLoading] = useState(false);
  const [processingId, setProcessingId] = useState<number | null>(null);

  const goTeam = (screen: string) => navigation.navigate('TeamChallenge', { screen });

  const loadInvites = useCallback(async () => {
    setLoading(true);
    try {
      setInvites(await getMyInvites());
    } catch {
      setInvites([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useFocusEffect(useCallback(() => { void loadInvites(); }, [loadInvites]));

  const respond = async (inviteId: number, status: 'ACCEPTED' | 'REJECTED') => {
    setProcessingId(inviteId);
    try {
      await respondTeamInvite(inviteId, status);
      toast.show(status === 'ACCEPTED' ? '팀 초대를 수락했습니다' : '팀 초대를 거절했습니다');
      await loadInvites();
    } catch (error) {
      toast.show(getChallengeErrorMessage(error));
    } finally {
      setProcessingId(null);
    }
  };

  return (
    <View style={styles.root}>
      <StatusBar style="light" />
      <HazeBackground />
      <MainHeader showBack={navigation.canGoBack()} />
      <ScrollView contentContainerStyle={styles.body} showsVerticalScrollIndicator={false}>
        <View style={styles.hero}>
          <PixelTitle size={24} style={styles.title}>함께하면 더 큰 선행!</PixelTitle>
          <Text style={styles.sub}>챌린지 팀을 찾거나 직접 만들어보세요.</Text>
          <View style={styles.buttons}>
            <PopupTealBtn label="방 찾기" onPress={() => goTeam('RoomFind')} />
            <PopupGoldBtn label="방 만들기" onPress={() => goTeam('TeamList')} />
          </View>
        </View>

        <View style={styles.inviteSection}>
          <PixelTitle size={17} style={{ marginBottom: 10 }}>받은 팀 초대</PixelTitle>
          {loading ? (
            <Text style={styles.muted}>초대 목록을 불러오는 중...</Text>
          ) : invites.length === 0 ? (
            <EmptyState icon="✉️" message="대기 중인 팀 초대가 없어요" />
          ) : invites.map((invite) => (
            <View key={invite.invite_id} style={styles.inviteCard}>
              <View style={{ flex: 1 }}>
                <Text style={styles.inviteTitle}>팀 #{invite.team_id} 초대</Text>
                <Text style={styles.muted}>초대 번호 #{invite.invite_id}</Text>
              </View>
              <SpringButton
                disabled={processingId === invite.invite_id}
                style={[styles.smallBtn, styles.accept]}
                onPress={() => void respond(invite.invite_id, 'ACCEPTED')}
              >
                <Text style={styles.smallText}>수락</Text>
              </SpringButton>
              <SpringButton
                disabled={processingId === invite.invite_id}
                style={[styles.smallBtn, styles.reject]}
                onPress={() => void respond(invite.invite_id, 'REJECTED')}
              >
                <Text style={[styles.smallText, { color: colors.primaryDark }]}>거절</Text>
              </SpringButton>
            </View>
          ))}
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.screenBg },
  body: { padding: 20, paddingBottom: 48 },
  hero: { marginTop: 32, alignItems: 'center' },
  title: { textAlign: 'center' },
  sub: { marginTop: 10, color: colors.textMuted, fontFamily: fonts.bodyR, textAlign: 'center' },
  buttons: { width: '100%', flexDirection: 'row', gap: 10, marginTop: 28 },
  inviteSection: { marginTop: 42 },
  inviteCard: { flexDirection: 'row', alignItems: 'center', gap: 8, padding: 12, marginBottom: 8, backgroundColor: colors.white, borderWidth: 1, borderColor: colors.pixelBorder, borderRadius: 12 },
  inviteTitle: { fontFamily: fonts.bodyM, color: colors.primaryDark },
  muted: { color: colors.textMuted, fontFamily: fonts.bodyR, fontSize: 12 },
  smallBtn: { paddingHorizontal: 12, paddingVertical: 8, borderRadius: 8 },
  accept: { backgroundColor: colors.xpGreen },
  reject: { backgroundColor: colors.screenBg, borderWidth: 1, borderColor: colors.pixelBorder },
  smallText: { color: colors.white, fontFamily: fonts.pixel, fontSize: 12 },
});
