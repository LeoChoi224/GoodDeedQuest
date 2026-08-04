import React, {
  useCallback,
  useEffect,
  useRef,
  useState,
} from 'react';
import {
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { useFocusEffect } from '@react-navigation/native';

import BottomSheet from '../../components/BottomSheet';
import GdqInput from '../../components/GdqInput';
import HazeBackground from '../../components/HazeBackground';
import MainHeader from '../../components/MainHeader';
import SegmentedTabs from '../../components/SegmentedTabs';
import SpringButton from '../../components/SpringButton';
import { useToast } from '../../components/Toast';
import { colors, fonts } from '../../theme';

import {
  createTeam,
  getChallengeErrorMessage,
} from '../../api/challenge';

import {
  difficultyLabel,
  getQuests,
  getTodayRecommendation,
  type Quest,
} from '../../api/quest';

import {
  CatIcon,
  IconChevDown,
  IconChevRight,
  PixelTitle,
} from './_parts';

import useTeamHomeBack from './useTeamHomeBack';

type QuestSource = 'today' | 'all';

export default function TeamListScreen({
  navigation,
  route,
}: any) {
  const toast = useToast();
  const { goTeamHome } = useTeamHomeBack(navigation);

  const [sheet, setSheet] = useState(true);
  const [creating, setCreating] = useState(false);

  const [name, setName] = useState('');

  const [quests, setQuests] = useState<Quest[]>([]);
  const [questsLoading, setQuestsLoading] =
    useState(false);

  const [questSource, setQuestSource] =
    useState<QuestSource>('today');

  const [selectedQuestId, setSelectedQuestId] =
    useState<number | null>(null);

  const [questPickerOpen, setQuestPickerOpen] =
    useState(false);

  const [region, setRegion] = useState('');

  const [notification, setNotification] =
    useState('잘 부탁드립니다.');

  const [maxMembers, setMaxMembers] = useState('4');
  const [vis, setVis] = useState(0);
  const [pw, setPw] = useState('');

  /**
   * QuestRegister에서 새 퀘스트를 등록한 뒤 돌아왔을 때
   * 선택해야 하는 퀘스트 ID를 임시로 보관합니다.
   */
  const returnedQuestIdRef =
    useRef<number | null>(null);

  const selectedQuest =
    quests.find(
      (quest) =>
        quest.quest_id === selectedQuestId,
    ) ?? null;

  /**
   * 오늘의 추천 퀘스트와 전체 퀘스트를 함께 조회합니다.
   *
   * 1. 오늘 추천이 있으면 추천 목록을 우선 표시
   * 2. 오늘 추천이 없으면 전체 퀘스트 표시
   * 3. 새로 등록한 퀘스트가 추천에 없으면
   *    전체 목록에서 찾아 추천 목록 끝에 추가
   */
  const loadQuestOptions = useCallback(async () => {
    setQuestsLoading(true);

    try {
      const [todayResult, allResult] =
        await Promise.all([
          getTodayRecommendation()
            .then((data) => ({
              ok: true as const,
              data: data ?? [],
            }))
            .catch(() => ({
              ok: false as const,
              data: [] as Quest[],
            })),

          getQuests()
            .then((data) => ({
              ok: true as const,
              data,
            }))
            .catch(() => ({
              ok: false as const,
              data: [] as Quest[],
            })),
        ]);

      const todayRows = todayResult.data;
      const allRows = allResult.data;

      const hasTodayRecommendations =
        todayRows.length > 0;

      /**
       * 오늘 추천과 전체 목록이 모두 실패했거나,
       * 오늘 추천이 없는데 전체 목록까지 실패한 경우입니다.
       */
      if (
        (!todayResult.ok && !allResult.ok)
        || (
          !hasTodayRecommendations
          && !allResult.ok
        )
      ) {
        throw new Error('퀘스트 목록 조회 실패');
      }

      let rows = hasTodayRecommendations
        ? [...todayRows]
        : [...allRows];

      const returnedQuestId =
        returnedQuestIdRef.current;

      /**
       * 새로 등록한 퀘스트는 오늘 추천 결과에
       * 바로 포함되지 않을 수 있습니다.
       *
       * 이 경우 전체 퀘스트에서 찾아
       * 현재 선택 목록 마지막에 추가합니다.
       */
      if (
        returnedQuestId !== null
        && !rows.some(
          (quest) =>
            quest.quest_id === returnedQuestId,
        )
      ) {
        const returnedQuest = allRows.find(
          (quest) =>
            quest.quest_id === returnedQuestId,
        );

        if (returnedQuest) {
          rows = [...rows, returnedQuest];
        }
      }

      setQuestSource(
        hasTodayRecommendations
          ? 'today'
          : 'all',
      );

      setQuests(rows);

      setSelectedQuestId((currentQuestId) => {
        const nextQuestId =
          returnedQuestId ?? currentQuestId;

        if (nextQuestId === null) {
          return null;
        }

        const stillExists = rows.some(
          (quest) =>
            quest.quest_id === nextQuestId,
        );

        return stillExists
          ? nextQuestId
          : null;
      });

      /**
       * 새로 등록한 퀘스트를 정상적으로 찾았다면
       * 임시 ID를 초기화합니다.
       */
      if (
        returnedQuestId !== null
        && rows.some(
          (quest) =>
            quest.quest_id === returnedQuestId,
        )
      ) {
        returnedQuestIdRef.current = null;
      }

      if (rows.length === 0) {
        setQuestPickerOpen(false);
      }
    } catch {
      setQuests([]);
      setSelectedQuestId(null);
      setQuestPickerOpen(false);

      toast.show(
        '오늘의 추천 퀘스트를 불러오지 못했습니다.',
      );
    } finally {
      setQuestsLoading(false);
    }
  }, [toast]);

  /**
   * 팀 생성 화면으로 돌아올 때마다
   * 방 만들기 BottomSheet를 다시 엽니다.
   */
  useFocusEffect(
    useCallback(() => {
      setSheet(true);
    }, []),
  );

  /**
   * QuestRegister에서 전달한 퀘스트 ID를 처리합니다.
   *
   * QuestRegisterScreen에서 아래 형태로 돌아옵니다.
   *
   * navigation.popTo('TeamList', {
   *   openCreate: true,
   *   selectedQuestId: result.quest_id,
   * });
   */
  useEffect(() => {
    const returnedQuestId = Number(
      route?.params?.selectedQuestId,
    );

    const hasReturnedQuestId =
      Number.isInteger(returnedQuestId)
      && returnedQuestId > 0;

    if (
      !route?.params?.openCreate
      && !hasReturnedQuestId
    ) {
      return;
    }

    if (hasReturnedQuestId) {
      returnedQuestIdRef.current =
        returnedQuestId;

      setSelectedQuestId(returnedQuestId);
    }

    setSheet(true);

    navigation.setParams({
      openCreate: false,
      selectedQuestId: undefined,
    });
  }, [
    navigation,
    route?.params?.openCreate,
    route?.params?.selectedQuestId,
  ]);

  /**
   * 방 만들기 BottomSheet가 열릴 때마다
   * 오늘의 추천 목록을 최신 상태로 조회합니다.
   */
  useEffect(() => {
    if (!sheet) {
      setQuestPickerOpen(false);
      return;
    }

    void loadQuestOptions();
  }, [loadQuestOptions, sheet]);

  const resetForm = () => {
    setName('');
    setSelectedQuestId(null);
    setQuestPickerOpen(false);
    setRegion('');
    setNotification('잘 부탁드립니다.');
    setMaxMembers('4');
    setVis(0);
    setPw('');

    returnedQuestIdRef.current = null;
  };

  const closeCreateScreen = () => {
    setSheet(false);
    resetForm();
    goTeamHome();
  };

  /**
   * 현재 팀 생성 입력값은 초기화하지 않고
   * 퀘스트 등록 화면으로 이동합니다.
   */
  const openQuestRegister = () => {
    setQuestPickerOpen(false);
    setSheet(false);

    navigation.navigate('QuestRegister', {
      returnToTeamCreate: true,
    });
  };

  const onCreate = async () => {
    const parsedMax = Number(maxMembers);

    if (
      !name.trim()
      || !selectedQuest
      || !region.trim()
    ) {
      toast.show(
        '팀 이름, 수행 퀘스트, 활동 지역을 확인해주세요.',
      );
      return;
    }

    if (
      !Number.isInteger(parsedMax)
      || parsedMax < 2
      || parsedMax > 10
    ) {
      toast.show(
        '최대 인원은 2명부터 10명까지 가능합니다.',
      );
      return;
    }

    if (
      vis === 1
      && pw.trim().length < 4
    ) {
      toast.show(
        '비공개 팀 비밀번호는 4자 이상 입력해주세요.',
      );
      return;
    }

    setCreating(true);

    try {
      const team = await createTeam({
        quest_id: selectedQuest.quest_id,
        name: name.trim(),
        password:
          vis === 1
            ? pw.trim()
            : null,
        notification:
          notification.trim()
          || '잘 부탁드립니다.',
        region: region.trim(),
        is_public: vis === 0,
        max_members: parsedMax,
      });

      setSheet(false);
      resetForm();

      toast.show('팀이 생성되었습니다');

      navigation.navigate('TeamDetail', {
        teamId: team.team_id,
      });
    } catch (error) {
      toast.show(
        getChallengeErrorMessage(error),
      );
    } finally {
      setCreating(false);
    }
  };

  return (
    <View style={styles.root}>
      <StatusBar style="light" />

      <HazeBackground />

      <MainHeader
        showBack
        title="방 만들기"
        onBack={closeCreateScreen}
      />

      <View style={styles.createHost}>
        <PixelTitle
          size={18}
          style={styles.createHostTitle}
        >
          새로운 챌린지 팀 만들기
        </PixelTitle>

        <Text style={styles.createHostText}>
          함께할 퀘스트와 팀 정보를 설정해주세요.
        </Text>
      </View>

      <BottomSheet
        visible={sheet}
        onClose={closeCreateScreen}
        title="새 챌린지 팀 만들기"
      >
        <ScrollView
          style={{ maxHeight: 560 }}
          contentContainerStyle={styles.form}
          keyboardShouldPersistTaps="handled"
        >
          <Text style={styles.label}>
            팀 이름 *
          </Text>

          <GdqInput
            value={name}
            onChangeText={setName}
            placeholder="팀 이름"
          />

          <Text style={styles.label}>
            {questSource === 'today'
              ? '오늘의 추천 퀘스트 *'
              : '수행 퀘스트 *'}
          </Text>

          <SpringButton
            disabled={
              questsLoading
              || quests.length === 0
            }
            pressScale={0.98}
            style={[
              styles.questSelectButton,
              selectedQuest
                && styles.questSelectButtonActive,
              (
                questsLoading
                || quests.length === 0
              )
                && styles.questSelectButtonDisabled,
            ]}
            onPress={() =>
              setQuestPickerOpen(
                (previous) => !previous,
              )
            }
          >
            {selectedQuest ? (
              <CatIcon
                category={
                  selectedQuest.category_code
                }
                size={40}
              />
            ) : null}

            <View style={styles.questSelectInfo}>
              <Text
                numberOfLines={1}
                style={[
                  styles.questSelectTitle,
                  !selectedQuest
                    && styles.questSelectPlaceholder,
                ]}
              >
                {selectedQuest
                  ? selectedQuest.quest_title
                  : questsLoading
                    ? '오늘의 추천 불러오는 중...'
                    : quests.length === 0
                      ? '선택 가능한 퀘스트가 없습니다'
                      : '퀘스트를 선택해주세요'}
              </Text>

              {selectedQuest ? (
                <Text
                  numberOfLines={1}
                  style={styles.questSelectMeta}
                >
                  {selectedQuest.category_name}
                  {' · '}
                  {difficultyLabel(
                    selectedQuest.difficulty,
                  )}
                </Text>
              ) : (
                <Text style={styles.questSelectMeta}>
                  {questSource === 'today'
                    ? '홈의 오늘의 추천 목록과 동일하게 표시됩니다'
                    : '오늘 추천이 없어 전체 퀘스트를 표시합니다'}
                </Text>
              )}
            </View>

            <IconChevDown
              size={18}
              color={colors.primaryDark}
            />
          </SpringButton>

          {questPickerOpen ? (
            <View style={styles.questOptionBox}>
              <ScrollView
                style={styles.questOptionScroll}
                contentContainerStyle={
                  styles.questOptionContent
                }
                nestedScrollEnabled
                keyboardShouldPersistTaps="handled"
              >
                {quests.map((quest) => {
                  const active =
                    selectedQuestId
                    === quest.quest_id;

                  return (
                    <SpringButton
                      key={quest.quest_id}
                      pressScale={0.98}
                      style={[
                        styles.questOption,
                        active
                          && styles.questOptionActive,
                      ]}
                      onPress={() => {
                        setSelectedQuestId(
                          quest.quest_id,
                        );

                        setQuestPickerOpen(false);
                      }}
                    >
                      <CatIcon
                        category={
                          quest.category_code
                        }
                        size={38}
                      />

                      <View
                        style={
                          styles.questOptionInfo
                        }
                      >
                        <Text
                          numberOfLines={1}
                          style={
                            styles.questOptionTitle
                          }
                        >
                          {quest.quest_title}
                        </Text>

                        <Text
                          numberOfLines={1}
                          style={
                            styles.questOptionMeta
                          }
                        >
                          {quest.category_name}
                          {' · '}
                          {difficultyLabel(
                            quest.difficulty,
                          )}
                        </Text>
                      </View>

                      <View
                        style={[
                          styles.questRadio,
                          active
                            && styles.questRadioActive,
                        ]}
                      >
                        {active ? (
                          <View
                            style={
                              styles.questRadioInner
                            }
                          />
                        ) : null}
                      </View>
                    </SpringButton>
                  );
                })}
              </ScrollView>
            </View>
          ) : null}

          <SpringButton
            pressScale={0.98}
            style={styles.questRegisterLink}
            onPress={openQuestRegister}
          >
            <Text
              style={styles.questRegisterText}
            >
              원하는 퀘스트가 없나요? 새 퀘스트 등록
            </Text>

            <IconChevRight
              size={16}
              color={colors.xpGreen}
            />
          </SpringButton>

          <Text style={styles.label}>
            활동 지역 *
          </Text>

          <GdqInput
            value={region}
            onChangeText={setRegion}
            placeholder="예: 서울 마포구"
          />

          <Text style={styles.label}>
            팀 공지
          </Text>

          <GdqInput
            value={notification}
            onChangeText={setNotification}
            placeholder="팀원에게 안내할 내용"
          />

          <Text style={styles.label}>
            최대 인원 (2~10)
          </Text>

          <GdqInput
            value={maxMembers}
            onChangeText={setMaxMembers}
            keyboardType="number-pad"
            placeholder="4"
          />

          <Text style={styles.label}>
            공개 설정
          </Text>

          <SegmentedTabs
            tabs={['공개', '비공개']}
            index={vis}
            onChange={setVis}
          />

          {vis === 1 ? (
            <>
              <Text style={styles.label}>
                비밀번호 *
              </Text>

              <GdqInput
                value={pw}
                onChangeText={setPw}
                secureTextEntry
                placeholder="4~20자"
              />
            </>
          ) : null}

          <SpringButton
            disabled={creating}
            style={styles.createBtn}
            onPress={() => void onCreate()}
          >
            <Text style={styles.createText}>
              {creating
                ? '생성 중...'
                : '팀 생성하기'}
            </Text>
          </SpringButton>
        </ScrollView>
      </BottomSheet>
    </View>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: colors.screenBg,
  },

  createHost: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 24,
    paddingBottom: 80,
  },

  createHostTitle: {
    textAlign: 'center',
  },

  createHostText: {
    marginTop: 10,
    color: colors.textMuted,
    fontFamily: fonts.bodyR,
    textAlign: 'center',
  },

  form: {
    gap: 8,
    paddingBottom: 24,
  },

  label: {
    marginTop: 8,
    color: colors.primaryDark,
    fontFamily: fonts.bodyB,
    fontSize: 13,
  },

  questSelectButton: {
    minHeight: 64,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    paddingHorizontal: 12,
    paddingVertical: 10,
    backgroundColor: colors.white,
    borderWidth: 1,
    borderColor: colors.pixelBorder,
    borderRadius: 10,
  },

  questSelectButtonActive: {
    borderWidth: 1.5,
    borderColor: colors.xpGreen,
  },

  questSelectButtonDisabled: {
    opacity: 0.65,
    backgroundColor: colors.screenBg,
  },

  questSelectInfo: {
    flex: 1,
    minWidth: 0,
  },

  questSelectTitle: {
    color: colors.primaryDark,
    fontFamily: fonts.bodyB,
    fontSize: 14,
  },

  questSelectPlaceholder: {
    color: colors.textMuted,
    fontFamily: fonts.bodyR,
  },

  questSelectMeta: {
    marginTop: 3,
    color: colors.textMuted,
    fontFamily: fonts.bodyR,
    fontSize: 11,
  },

  questOptionBox: {
    maxHeight: 230,
    backgroundColor: colors.white,
    borderWidth: 1,
    borderColor: colors.pixelBorder,
    borderRadius: 10,
    overflow: 'hidden',
  },

  questOptionScroll: {
    maxHeight: 228,
  },

  questOptionContent: {
    padding: 6,
    gap: 4,
  },

  questOption: {
    minHeight: 58,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    paddingHorizontal: 8,
    paddingVertical: 7,
    borderRadius: 8,
  },

  questOptionActive: {
    backgroundColor: colors.screenBg,
  },

  questOptionInfo: {
    flex: 1,
    minWidth: 0,
  },

  questOptionTitle: {
    color: colors.primaryDark,
    fontFamily: fonts.bodyM,
    fontSize: 13,
  },

  questOptionMeta: {
    marginTop: 2,
    color: colors.textMuted,
    fontFamily: fonts.bodyR,
    fontSize: 11,
  },

  questRadio: {
    width: 20,
    height: 20,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1.5,
    borderColor: colors.pixelBorder,
    borderRadius: 10,
  },

  questRadioActive: {
    borderColor: colors.xpGreen,
  },

  questRadioInner: {
    width: 10,
    height: 10,
    backgroundColor: colors.xpGreen,
    borderRadius: 5,
  },

  questRegisterLink: {
    minHeight: 40,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 10,
    borderRadius: 8,
    backgroundColor: colors.screenBg,
  },

  questRegisterText: {
    flex: 1,
    color: colors.xpGreen,
    fontFamily: fonts.bodyB,
    fontSize: 12,
  },

  createBtn: {
    height: 50,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 16,
    backgroundColor: colors.xpGreen,
    borderRadius: 8,
  },

  createText: {
    color: colors.white,
    fontFamily: fonts.pixel,
    fontSize: 16,
  },
});