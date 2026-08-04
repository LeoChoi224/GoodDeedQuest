import React, { useCallback, useState } from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { useFocusEffect } from '@react-navigation/native';
import HazeBackground from '../../components/HazeBackground';
import MainHeader from '../../components/MainHeader';
import SpringButton from '../../components/SpringButton';
import EmptyState from '../../components/EmptyState';
import GamePopup from '../../components/GamePopup';
import { useToast } from '../../components/Toast';
import { colors, fonts, gamePopup } from '../../theme';
import {
  getChallengeErrorMessage,
  getMyInvites,
  getMyTeams,
  respondTeamInvite,
  ReceivedTeamInvite,
  TeamListItem,
} from '../../api/challenge';
import {
  CatIcon,
  IconChevRight,
  PixelTitle,
  PopupGoldBtn,
  PopupTealBtn,
  StickyFooter,
} from './_parts';

function teamCategory(team: TeamListItem): string {
  const text = `${team.name} ${team.notification}`;

  if (text.includes('환경')) return 'environment';
  if (text.includes('봉사')) return 'volunteer';
  if (text.includes('동물')) return 'animal';
  if (text.includes('나눔')) return 'sharing';

  return 'community';
}

export default function TeamHomeScreen({ navigation }: any) {
  const toast = useToast();

  const [teams, setTeams] = useState<TeamListItem[]>([]);
  const [invites, setInvites] = useState<ReceivedTeamInvite[]>([]);
  const [loading, setLoading] = useState(false);
  const [invitePopupVisible, setInvitePopupVisible] = useState(false);
  const [processingId, setProcessingId] = useState<number | null>(null);

  const goTeam = (
    screen: string,
    params?: Record<string, unknown>,
  ) => {
    navigation.navigate('TeamChallenge', {
      screen,
      params,
    });
  };

  const loadTeamHome = useCallback(async () => {
    setLoading(true);

    try {
      const [myTeams, myInvites] = await Promise.all([
        getMyTeams({ size: 100 }),
        getMyInvites(1, 100),
      ]);

      setTeams(myTeams);
      setInvites(myInvites);
    } catch (error) {
      toast.show(getChallengeErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useFocusEffect(
    useCallback(() => {
      void loadTeamHome();
    }, [loadTeamHome]),
  );

  const openInvitePopup = () => {
    setInvitePopupVisible(true);
    void loadTeamHome();
  };

  const respond = async (
    inviteId: number,
    status: 'ACCEPTED' | 'REJECTED',
  ) => {
    setProcessingId(inviteId);

    try {
      await respondTeamInvite(inviteId, status);

      toast.show(
        status === 'ACCEPTED'
          ? '팀 초대를 수락했습니다'
          : '팀 초대를 거절했습니다',
      );

      await loadTeamHome();
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
            <PopupGoldBtn label="방 만들기" onPress={() => goTeam('TeamList', { openCreate: true, })} />
          </View>
        </View>

        <View style={styles.teamSection}>
          <PixelTitle size={17} style={styles.sectionTitle}>
            참여 중인 방
          </PixelTitle>

          {loading ? (
            <Text style={styles.loadingText}>
              참여 중인 방을 불러오는 중...
            </Text>
          ) : teams.length === 0 ? (
            <EmptyState
              icon="🧭"
              message="아직 참여 중인 방이 없어요"
              subMessage="방 찾기 또는 방 만들기를 이용해보세요"
            />
          ) : (
            <View style={styles.teamList}>
              {teams.map((team) => (
                <SpringButton
                  key={team.team_id}
                  pressScale={0.98}
                  style={styles.teamCard}
                  onPress={() =>
                    goTeam('TeamDetail', {
                      teamId: team.team_id,
                    })
                  }
                >
                  <CatIcon
                    category={teamCategory(team)}
                    size={44}
                  />

                  <View style={styles.teamInfo}>
                    <Text
                      style={styles.teamName}
                      numberOfLines={1}
                    >
                      {team.name}
                    </Text>

                    <Text
                      style={styles.teamMeta}
                      numberOfLines={1}
                    >
                      {team.region} · {team.current_members}/
                      {team.max_members}명
                    </Text>
                  </View>

                  <IconChevRight />
                </SpringButton>
              ))}
            </View>
          )}
        </View>
      </ScrollView>

      <StickyFooter>
        <SpringButton
          style={styles.inviteOpenButton}
          onPress={openInvitePopup}
        >
          <Text style={styles.inviteOpenText}>
            받은 팀 초대
          </Text>

          <View style={styles.inviteCountBadge}>
            <Text style={styles.inviteCountText}>
              {invites.length}
            </Text>
          </View>
        </SpringButton>
      </StickyFooter>

      <GamePopup
        visible={invitePopupVisible}
        onClose={() => setInvitePopupVisible(false)}
        title="받은 팀 초대"
      >
        <View style={styles.popupContent}>
          {loading ? (
            <Text style={styles.popupMessage}>
              초대 목록을 불러오는 중...
            </Text>
          ) : invites.length === 0 ? (
            <View style={styles.popupEmpty}>
              <Text style={styles.popupEmptyIcon}>✉️</Text>
              <Text style={styles.popupMessage}>
                대기 중인 팀 초대가 없어요
              </Text>
            </View>
          ) : (
            <ScrollView
              style={styles.inviteList}
              contentContainerStyle={styles.inviteListContent}
              showsVerticalScrollIndicator={false}
              nestedScrollEnabled
            >
              {invites.map((invite) => {
                const processing =
                  processingId === invite.invite_id;

                return (
                  <View
                    key={invite.invite_id}
                    style={styles.inviteCard}
                  >
                    <View style={styles.inviteInfo}>
                      <Text
                        style={styles.inviteTitle}
                        numberOfLines={1}
                      >
                        {invite.team_name}
                      </Text>

                      <Text
                        style={styles.inviteMeta}
                        numberOfLines={1}
                      >
                        {invite.inviter_nickname}님의 초대
                      </Text>
                    </View>

                    <View style={styles.inviteActions}>
                      <SpringButton
                        disabled={processing}
                        style={[
                          styles.popupButton,
                          styles.acceptButton,
                          processing &&
                          styles.processingButton,
                        ]}
                        onPress={() =>
                          void respond(
                            invite.invite_id,
                            'ACCEPTED',
                          )
                        }
                      >
                        <Text style={styles.acceptText}>
                          {processing ? '처리 중' : '수락'}
                        </Text>
                      </SpringButton>

                      <SpringButton
                        disabled={processing}
                        style={[
                          styles.popupButton,
                          styles.rejectButton,
                          processing &&
                          styles.processingButton,
                        ]}
                        onPress={() =>
                          void respond(
                            invite.invite_id,
                            'REJECTED',
                          )
                        }
                      >
                        <Text style={styles.rejectText}>
                          거절
                        </Text>
                      </SpringButton>
                    </View>
                  </View>
                );
              })}
            </ScrollView>
          )}
        </View>
      </GamePopup>
    </View>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: colors.screenBg,
  },
  body: {
    paddingHorizontal: 20,
    paddingTop: 20,
    paddingBottom: 140,
  },
  hero: {
    marginTop: 12,
    alignItems: 'center',
  },
  title: {
    textAlign: 'center',
  },
  sub: {
    marginTop: 10,
    color: colors.textMuted,
    fontFamily: fonts.bodyR,
    textAlign: 'center',
  },
  buttons: {
    width: '100%',
    flexDirection: 'row',
    gap: 10,
    marginTop: 28,
  },
  teamSection: {
    marginTop: 36,
  },
  sectionTitle: {
    marginBottom: 12,
  },
  loadingText: {
    paddingVertical: 40,
    color: colors.textMuted,
    fontFamily: fonts.bodyR,
    textAlign: 'center',
  },
  teamList: {
    gap: 10,
  },
  teamCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    padding: 12,
    backgroundColor: colors.white,
    borderWidth: 1,
    borderColor: colors.pixelBorder,
    borderRadius: 12,
  },
  teamInfo: {
    flex: 1,
    minWidth: 0,
  },
  teamName: {
    color: colors.primaryDark,
    fontFamily: fonts.bodyM,
    fontSize: 15,
  },
  teamMeta: {
    marginTop: 4,
    color: colors.textMuted,
    fontFamily: fonts.bodyR,
    fontSize: 12,
  },
  inviteOpenButton: {
    minHeight: 52,
    paddingHorizontal: 18,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
    backgroundColor: colors.primaryDark,
    borderWidth: 1.5,
    borderColor: colors.gold,
    borderRadius: 12,
  },
  inviteOpenText: {
    color: colors.parchment,
    fontFamily: fonts.pixel,
    fontSize: 15,
  },
  inviteCountBadge: {
    minWidth: 24,
    height: 24,
    paddingHorizontal: 7,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.gold,
    borderRadius: 12,
  },
  inviteCountText: {
    color: colors.primaryDark,
    fontFamily: fonts.bodyB,
    fontSize: 12,
  },
  popupContent: {
    width: '100%',
  },
  popupMessage: {
    paddingVertical: 20,
    color: gamePopup.cream,
    fontFamily: fonts.bodyR,
    textAlign: 'center',
  },
  popupEmpty: {
    alignItems: 'center',
  },
  popupEmptyIcon: {
    marginTop: 4,
    fontSize: 36,
  },
  inviteList: {
    width: '100%',
    maxHeight: 390,
  },
  inviteListContent: {
    gap: 10,
  },
  inviteCard: {
    padding: 12,
    backgroundColor: 'rgba(255,248,231,0.08)',
    borderWidth: 1,
    borderColor: 'rgba(242,215,131,0.35)',
    borderRadius: 12,
  },
  inviteInfo: {
    marginBottom: 10,
  },
  inviteTitle: {
    color: gamePopup.cream,
    fontFamily: fonts.bodyM,
    fontSize: 14,
  },
  inviteMeta: {
    marginTop: 3,
    color: 'rgba(245,239,216,0.65)',
    fontFamily: fonts.bodyR,
    fontSize: 11,
  },
  inviteActions: {
    flexDirection: 'row',
    gap: 8,
  },
  popupButton: {
    flex: 1,
    minHeight: 40,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 8,
  },
  acceptButton: {
    backgroundColor: colors.gold,
  },
  rejectButton: {
    borderWidth: 1,
    borderColor: 'rgba(242,215,131,0.5)',
  },
  processingButton: {
    opacity: 0.55,
  },
  acceptText: {
    color: colors.primaryDark,
    fontFamily: fonts.pixel,
    fontSize: 12,
  },
  rejectText: {
    color: gamePopup.cream,
    fontFamily: fonts.pixel,
    fontSize: 12,
  },
});
