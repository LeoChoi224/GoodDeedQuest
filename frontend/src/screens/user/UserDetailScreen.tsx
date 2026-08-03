/**
 * UserDetailScreen (route: UserDetail)
 * 마이페이지와 동일한 UI로 다른 사용자의 공개 정보를 표시합니다.
 * 관리자 목록에서 진입한 경우 활성·비활성 전환 버튼을 추가로 표시합니다.
 */
import React, { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Image,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { StatusBar } from 'expo-status-bar';
import Animated, { FadeInDown } from 'react-native-reanimated';

import HazeBackground from '../../components/HazeBackground';
import MainHeader from '../../components/MainHeader';
import SpringButton from '../../components/SpringButton';
import GamePopup, { PopupButtons } from '../../components/GamePopup';
import { useToast } from '../../components/Toast';
import {
  getCommunityUserProfile,
  getCommunityUserQuestAchievements,
  type CommunityUserProfile,
  type CommunityUserQuestAchievement,
} from '../../api/community';
import {
  colors,
  fonts,
  radii,
  CATEGORY_ICONS,
  brand,
} from '../../theme';
import { ConicAvatar } from '../mypage/_parts';
import { getFullImageUrl } from '../shop/_parts';
import { adminApi, getAdminErrorMessage } from '../admin/adminApi';

function formatShortDate(iso: string): string {
  const date = new Date(iso);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');

  return `${year}-${month}-${day}`;
}

function formatCompletedAt(iso: string): string {
  const date = new Date(iso);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');

  return `${year}.${month}.${day} ${hours}:${minutes}`;
}

export default function UserDetailScreen({ navigation, route }: any) {
  const toast = useToast();

  const initialUser = route?.params?.user ?? {};
  const userId = Number(route?.params?.userId ?? initialUser.user_id);
  const moderation = Boolean(route?.params?.moderation);

  const [profile, setProfile] = useState<CommunityUserProfile | null>(null);
  const [profileLoading, setProfileLoading] = useState(true);
  const [profileError, setProfileError] = useState(false);

  const [achievements, setAchievements] = useState<
    CommunityUserQuestAchievement[]
  >([]);
  const [achievementsLoading, setAchievementsLoading] = useState(true);
  const [achievementsError, setAchievementsError] = useState(false);

  const [selected, setSelected] =
    useState<CommunityUserQuestAchievement | null>(null);

  const [confirmBlock, setConfirmBlock] = useState(false);
  const [moderationSubmitting, setModerationSubmitting] = useState(false);
  const [isActive, setIsActive] = useState(initialUser.is_active ?? true);

  useEffect(() => {
    let cancelled = false;

    if (!Number.isInteger(userId) || userId <= 0) {
      setProfileLoading(false);
      setProfileError(true);
      setAchievementsLoading(false);
      setAchievementsError(true);
      return;
    }

    const loadProfile = async () => {
      setProfileLoading(true);
      setProfileError(false);

      try {
        const data = await getCommunityUserProfile(userId);

        if (!cancelled) {
          setProfile(data);
        }
      } catch (error) {
        console.error('사용자 공개 프로필 조회 실패:', error);

        if (!cancelled) {
          setProfileError(true);
        }
      } finally {
        if (!cancelled) {
          setProfileLoading(false);
        }
      }
    };

    const loadAchievements = async () => {
      setAchievementsLoading(true);
      setAchievementsError(false);

      try {
        const data = await getCommunityUserQuestAchievements(userId);

        if (!cancelled) {
          setAchievements(data);
        }
      } catch (error) {
        console.error('사용자 달성 퀘스트 조회 실패:', error);

        if (!cancelled) {
          setAchievementsError(true);
        }
      } finally {
        if (!cancelled) {
          setAchievementsLoading(false);
        }
      }
    };

    void loadProfile();
    void loadAchievements();

    return () => {
      cancelled = true;
    };
  }, [userId]);

  const updateActiveStatus = async () => {
    if (
      moderationSubmitting ||
      !Number.isInteger(userId) ||
      userId <= 0
    ) {
      return;
    }

    const nextIsActive = !isActive;

    try {
      setModerationSubmitting(true);

      const updatedUser = await adminApi.updateUserActiveStatus(
        userId,
        nextIsActive,
      );

      setIsActive(updatedUser.is_active);
      setConfirmBlock(false);

      toast.show(
        updatedUser.is_active
          ? '차단이 해제되었습니다'
          : `${
              profile?.nickname ??
              initialUser.nickname ??
              initialUser.name ??
              '사용자'
            }님을 차단했어요`,
      );

      navigation.goBack();
    } catch (error) {
      toast.show(getAdminErrorMessage(error));
    } finally {
      setModerationSubmitting(false);
    }
  };

  return (
    <View style={styles.root}>
      <StatusBar style="light" />
      <HazeBackground />

      <MainHeader
        showBack
        title="유저 정보"
        onBack={() => navigation.goBack()}
      />

      <ScrollView
        style={styles.scroll}
        contentContainerStyle={styles.body}
        showsVerticalScrollIndicator={false}
      >
        {/* 마이페이지와 동일한 가로형 프로필 카드 */}
        <Animated.View
          entering={FadeInDown.duration(360)}
          style={styles.profileCard}
        >
          <ConicAvatar
            size={64}
            imageUri={profile?.profile_image_url ?? null}
            borderImageUrl={
              profile?.equipped_border_image_url
                ? getFullImageUrl(profile.equipped_border_image_url)
                : null
            }
          />

          <View style={styles.profileInfo}>
            {profileLoading ? (
              <ActivityIndicator
                color={colors.primaryDark}
                style={styles.profileInfoLoading}
              />
            ) : profileError || !profile ? (
              <Text style={styles.name}>프로필을 불러오지 못했어요</Text>
            ) : (
              <>
                <Text style={styles.name}>{profile.nickname}</Text>

                <Text style={styles.title}>{profile.title}</Text>

                <View style={styles.metaRow}>
                  <Text style={styles.lv}>LV.{profile.current_level}</Text>

                  <Text style={styles.streak}>
                    🔥 {profile.daily_streak}일째 연속접속
                  </Text>
                </View>
              </>
            )}
          </View>
        </Animated.View>

        <Text style={styles.sectionTitle}>퀘스트 달성업적 및 타임라인</Text>

        {/* 마이페이지와 동일한 타임라인 카드 */}
        <View style={styles.timelineCard}>
          {achievementsLoading ? (
            <View style={styles.timelineStateBox}>
              <ActivityIndicator color={colors.primaryDark} />
            </View>
          ) : achievementsError ? (
            <View style={styles.timelineStateBox}>
              <Text style={styles.timelineStateText}>
                달성 내역을 불러오지 못했어요
              </Text>
            </View>
          ) : achievements.length === 0 ? (
            <View style={styles.timelineStateBox}>
              <Text style={styles.timelineStateText}>
                달성한 퀘스트가 없습니다
              </Text>
            </View>
          ) : (
            <ScrollView
              style={styles.timelineScroll}
              nestedScrollEnabled
              showsVerticalScrollIndicator={false}
            >
              {achievements.map((achievement, index) => (
                <Animated.View
                  key={achievement.submission_id}
                  entering={FadeInDown.delay(50 + index * 70).duration(450)}
                >
                  <SpringButton
                    style={[
                      styles.achievementRow,
                      index === achievements.length - 1 &&
                        styles.achievementRowLast,
                    ]}
                    onPress={() => setSelected(achievement)}
                    pressScale={0.99}
                  >
                    <Image
                      source={
                        CATEGORY_ICONS[achievement.category_code] ??
                        CATEGORY_ICONS.other
                      }
                      style={styles.achievementIcon}
                    />

                    <Text style={styles.achievementName}>
                      {achievement.title}
                    </Text>

                    <Text style={styles.achievementDate}>
                      {formatShortDate(achievement.completed_at)}
                    </Text>
                  </SpringButton>
                </Animated.View>
              ))}
            </ScrollView>
          )}
        </View>

        {/* 관리자 목록에서 진입했을 때만 표시 */}
        {moderation ? (
          <SpringButton
            disabled={moderationSubmitting}
            style={[
              styles.moderationButton,
              isActive ? styles.blockButton : styles.unblockButton,
            ]}
            onPress={() => setConfirmBlock(true)}
          >
            {moderationSubmitting ? (
              <ActivityIndicator
                color={isActive ? colors.danger : colors.primaryDark}
              />
            ) : (
              <Text
                style={[
                  styles.moderationText,
                  {
                    color: isActive ? colors.danger : colors.primaryDark,
                  },
                ]}
              >
                {isActive ? '차단하기' : '차단 해제하기'}
              </Text>
            )}
          </SpringButton>
        ) : null}
      </ScrollView>

      {/* 달성 퀘스트 상세 팝업 */}
      <GamePopup visible={selected !== null} onClose={() => setSelected(null)}>
        <Image source={brand.appIconCheck} style={styles.popupCheck} />

        {selected ? (
          <>
            <Text style={styles.popupTitle}>{selected.title}</Text>

            <Text style={styles.popupDescription}>
              {selected.description}
            </Text>

            <Text style={styles.popupTime}>
              퀘스트 완료 시간 : {formatCompletedAt(selected.completed_at)}
            </Text>

            <View style={styles.chipRow}>
              <Text style={[styles.chip, styles.experienceChip]}>
                경험치 +{selected.reward_exp ?? 0}
              </Text>

              <Text style={[styles.chip, styles.pointChip]}>
                포인트 +{selected.reward_point ?? 0}
              </Text>
            </View>

            <SpringButton
              style={styles.popupButton}
              onPress={() => setSelected(null)}
            >
              <Text style={styles.popupButtonText}>확인 완료</Text>
            </SpringButton>
          </>
        ) : null}
      </GamePopup>

      {/* 관리자 차단·해제 확인 팝업 */}
      <GamePopup
        visible={confirmBlock}
        onClose={() => {
          if (!moderationSubmitting) {
            setConfirmBlock(false);
          }
        }}
        dismissOnBackdrop={!moderationSubmitting}
        title={isActive ? '차단하시겠습니까?' : '차단을 해제하시겠습니까?'}
      >
        <PopupButtons
          primaryLabel={moderationSubmitting ? '처리 중...' : '예'}
          onPrimary={() => {
            void updateActiveStatus();
          }}
          secondaryLabel="아니오"
          onSecondary={() => {
            if (!moderationSubmitting) {
              setConfirmBlock(false);
            }
          }}
        />
      </GamePopup>
    </View>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: colors.screenBg,
  },
  scroll: {
    flex: 1,
  },
  body: {
    padding: 16,
    paddingBottom: 28,
  },

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
    shadowOffset: {
      width: 0,
      height: 4,
    },
    shadowOpacity: 0.12,
    shadowRadius: 14,
    elevation: 3,
  },
  profileInfo: {
    flex: 1,
    minWidth: 0,
  },
  profileInfoLoading: {
    alignSelf: 'flex-start',
  },
  name: {
    fontSize: 18,
    fontWeight: '600',
    color: colors.primaryDark,
    fontFamily: fonts.bodyM,
  },
  title: {
    fontSize: 13,
    color: colors.gold,
    fontWeight: '600',
    marginTop: 1,
    marginBottom: 3,
    fontFamily: fonts.bodyM,
  },
  metaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  lv: {
    fontFamily: fonts.pixel,
    fontSize: 15,
    color: colors.primaryDark,
  },
  streak: {
    fontSize: 12,
    color: colors.xpGreen,
    fontWeight: '600',
    fontFamily: fonts.bodyM,
  },

  sectionTitle: {
    fontFamily: fonts.pixel,
    fontSize: 16,
    color: colors.primaryDark,
    marginBottom: 12,
  },

  timelineCard: {
    backgroundColor: colors.white,
    borderRadius: 12,
    marginBottom: 14,
    overflow: 'hidden',
    shadowColor: '#033236',
    shadowOffset: {
      width: 0,
      height: 3,
    },
    shadowOpacity: 0.06,
    shadowRadius: 10,
    elevation: 2,
  },
  timelineScroll: {
    maxHeight: 320,
  },
  timelineStateBox: {
    paddingVertical: 32,
    alignItems: 'center',
    justifyContent: 'center',
  },
  timelineStateText: {
    fontSize: 13,
    color: '#888',
    fontFamily: fonts.bodyM,
  },
  achievementRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    paddingVertical: 12,
    paddingHorizontal: 14,
    borderBottomWidth: 1,
    borderBottomColor: '#EEF1F0',
    backgroundColor: colors.white,
  },
  achievementRowLast: {
    borderBottomWidth: 0,
  },
  achievementIcon: {
    width: 40,
    height: 40,
    borderRadius: 9,
  },
  achievementName: {
    flex: 1,
    fontSize: 15,
    fontWeight: '600',
    color: colors.primaryDark,
    fontFamily: fonts.bodyM,
  },
  achievementDate: {
    fontSize: 12,
    color: '#888',
    fontFamily: fonts.bodyR,
  },

  moderationButton: {
    height: 52,
    borderRadius: radii.button,
    backgroundColor: colors.white,
    borderWidth: 1.5,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 6,
  },
  blockButton: {
    borderColor: colors.danger,
  },
  unblockButton: {
    borderColor: colors.primaryDark,
  },
  moderationText: {
    fontFamily: fonts.bodyB,
    fontSize: 15,
    fontWeight: '700',
  },

  popupCheck: {
    width: 72,
    height: 72,
    marginBottom: 14,
  },
  popupTitle: {
    fontFamily: fonts.pixel,
    fontSize: 20,
    color: '#F5ECCB',
    textAlign: 'center',
    marginBottom: 8,
  },
  popupDescription: {
    textAlign: 'center',
    fontSize: 14,
    color: '#B9C9BD',
    lineHeight: 21,
    marginBottom: 14,
    fontFamily: fonts.bodyR,
  },
  popupTime: {
    textAlign: 'center',
    fontSize: 13,
    color: '#8FA79A',
    marginBottom: 16,
    fontFamily: fonts.bodyR,
  },
  chipRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 10,
    marginBottom: 20,
  },
  chip: {
    borderRadius: 24,
    paddingVertical: 6,
    paddingHorizontal: 14,
    fontSize: 13,
    fontWeight: '700',
    overflow: 'hidden',
    fontFamily: fonts.bodyB,
  },
  experienceChip: {
    backgroundColor: colors.xpGreen,
    color: colors.white,
  },
  pointChip: {
    backgroundColor: colors.gold,
    color: colors.primaryDark,
  },
  popupButton: {
    alignSelf: 'stretch',
    height: 48,
    borderRadius: 8,
    backgroundColor: colors.primaryDark,
    alignItems: 'center',
    justifyContent: 'center',
  },
  popupButtonText: {
    color: colors.parchment,
    fontFamily: fonts.pixel,
    fontSize: 16,
  },
});