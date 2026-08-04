/**
 * SCREEN 03·6 — 새 피드 작성 (route: NewPost, back).
 *
 * 실제 Backend API를 사용해 최근 승인 퀘스트 인증 내역을 조회하고,
 * 선택한 인증의 미디어와 본문으로 커뮤니티 게시글을 생성합니다.
 */
import React, { useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  Image,
  KeyboardAvoidingView,
  Modal,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Animated, { FadeIn, FadeOut, ZoomIn } from 'react-native-reanimated';
import { colors, fonts, radii, shadow } from '../../theme';
import HazeBackground from '../../components/HazeBackground';
import MainHeader from '../../components/MainHeader';
import SpringButton from '../../components/SpringButton';
import { useToast } from '../../components/Toast';
import { WhiteCheck } from './_parts';
import { useVideoPlayer, VideoView } from 'expo-video';
import {
  CommunityFeedItem,
  createCommunityPost,
  getRecentQuestSubmissions,
  RecentQuestSubmission,
  updateCommunityPost,
} from '../../api/community';


const BODY_MAX = 500;

type SelectableQuestMedia = {
  selectionKey: string;
  submission_id: number;
  quest_id: number;
  media_index: number;
  media_url: string;
  media_type: 'PHOTO' | 'VIDEO';
  submitted_at: string;
};

function toSelectableQuestMedia(
  submission: RecentQuestSubmission,
): SelectableQuestMedia[] {
  const mediaItems: SelectableQuestMedia[] = [];
  const primaryUrl = submission.media_url?.trim();

  if (primaryUrl) {
    mediaItems.push({
      selectionKey: `${submission.submission_id}:0`,
      submission_id: submission.submission_id,
      quest_id: submission.quest_id,
      media_index: 0,
      media_url: primaryUrl,
      media_type: submission.media_type ?? 'PHOTO',
      submitted_at: submission.submitted_at,
    });
  }

  (submission.extra_media_urls ?? []).forEach(
    (extraMediaUrl, extraIndex) => {
      if (
        typeof extraMediaUrl !== 'string'
        || !extraMediaUrl.trim()
      ) {
        return;
      }

      const mediaIndex = extraIndex + 1;

      mediaItems.push({
        selectionKey: `${submission.submission_id}:${mediaIndex}`,
        submission_id: submission.submission_id,
        quest_id: submission.quest_id,
        media_index: mediaIndex,
        media_url: extraMediaUrl.trim(),
        media_type: 'PHOTO',
        submitted_at: submission.submitted_at,
      });
    },
  );

  return mediaItems;
}

function QuestMediaPreview({
  uri,
  mediaType,
  style,
  nativeControls = false,
}: {
  uri: string;
  mediaType: RecentQuestSubmission['media_type'];
  style: any;
  nativeControls?: boolean;
}) {
  const isVideo = mediaType === 'VIDEO';
  const player = useVideoPlayer(isVideo ? uri : null, (videoPlayer) => {
    videoPlayer.loop = true;
    videoPlayer.muted = true;
  });

  if (isVideo) {
    return (
      <VideoView
        player={player}
        style={style}
        contentFit="cover"
        nativeControls={nativeControls}
      />
    );
  }

  return <Image source={{ uri }} style={style} resizeMode="cover" />;
}

export default function NewPostScreen({ navigation, route }: any) {
  const insets = useSafeAreaInsets();
  const toast = useToast();

  const editPost = route?.params?.post as CommunityFeedItem | undefined;
  const isEditMode = editPost != null;

  const [modalOpen, setModalOpen] = useState(!isEditMode);
  const [mediaItems, setMediaItems] = useState<SelectableQuestMedia[]>([]);
  const [selected, setSelected] = useState<SelectableQuestMedia | null>(null);
  const [body, setBody] = useState(editPost?.caption ?? '');

  const [loadingSubmissions, setLoadingSubmissions] = useState(!isEditMode);
  const [submissionError, setSubmissionError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  const mediaUrl = editPost?.media_url ?? selected?.media_url ?? null;
  const mediaType = editPost?.media_type ?? selected?.media_type ?? null;
  const hasMedia = mediaUrl != null;
  const canUpload = hasMedia && !uploading;

  // 최근 승인된 퀘스트 인증 내역을 Backend에서 조회합니다.
  useEffect(() => {
    if (isEditMode) {
      return;
    }

    let mounted = true;

    const loadSubmissions = async () => {
      try {
        setLoadingSubmissions(true);
        setSubmissionError(null);

        const result = await getRecentQuestSubmissions();

        if (!mounted) {
          return;
        }

        // 미디어 URL이 있는 인증만 게시글 작성 후보로 표시합니다.
        setMediaItems(
          result.flatMap(toSelectableQuestMedia),
        );
      } catch (error) {
        console.error('최근 퀘스트 인증 조회 실패:', error);

        if (mounted) {
          setSubmissionError('퀘스트 인증 내역을 불러오지 못했습니다.');
        }
      } finally {
        if (mounted) {
          setLoadingSubmissions(false);
        }
      }
    };

    loadSubmissions();

    return () => {
      mounted = false;
    };
  }, [isEditMode]);

  // 선택한 인증과 본문을 이용해 실제 커뮤니티 게시글을 생성합니다.
  const onUpload = async () => {
    if (!mediaUrl || uploading) {
      return;
    }

    try {
      setUploading(true);

      if (isEditMode) {
        await updateCommunityPost(editPost.post_id, {
          caption: body.trim() || null,
        });

        toast.show('게시물이 수정되었습니다');
      } else {
        if (!selected) {
          return;
        }

        await createCommunityPost({
          submission_id: selected.submission_id,
          selected_media_index: selected.media_index,
          caption: body.trim() || null,
        });

        toast.show('게시되었습니다');
      }

      navigation.goBack();
    } catch (error) {
      console.error(
        isEditMode
          ? '커뮤니티 게시글 수정 실패:'
          : '커뮤니티 게시글 생성 실패:',
        error,
      );

      const axiosError = error as {
        code?: string;
        message?: string;
        response?: {
          status?: number;
          data?: unknown;
        };
      };

      const statusCode = axiosError.response?.status;
      const isRequestTimeout =
        axiosError.code === 'ECONNABORTED'
        || axiosError.code === 'ETIMEDOUT'
        || axiosError.message
          ?.toLowerCase()
          .includes('timeout') === true;

      console.error(
        '커뮤니티 API 오류 상세:',
        axiosError.code,
        statusCode,
        axiosError.response?.data,
      );

      // FUNC-02: 이미 게시글에 사용된 인증은 목록에서 제거합니다.
      if (!isEditMode && statusCode === 409) {
        if (selected) {
          setMediaItems((current) =>
            current.filter(
              (item) =>
                item.submission_id !== selected.submission_id,
            ),
          );
        }

        setSelected(null);
        setModalOpen(true);
        toast.show('이미 커뮤니티에 등록한 인증입니다');
        return;
      }

      // Backend에서 FFmpeg 제한 시간을 초과한 경우입니다.
      if (!isEditMode && statusCode === 504) {
        toast.show(
          '동영상 최적화 시간이 초과되었습니다. 다시 시도해주세요',
        );
        return;
      }

      // Axios 또는 네트워크 계층에서 응답 대기 시간이 초과된 경우입니다.
      if (!isEditMode && isRequestTimeout) {
        toast.show(
          selected?.media_type === 'VIDEO'
            ? '동영상 처리가 지연되고 있습니다. 잠시 후 피드에서 등록 여부를 확인해주세요'
            : '게시글 처리가 지연되고 있습니다. 잠시 후 다시 확인해주세요',
        );
        return;
      }

      toast.show(
        isEditMode
          ? '게시글을 수정하지 못했습니다'
          : '게시글을 업로드하지 못했습니다',
      );
    } finally {
      setUploading(false);
    }
  };

    return (
      <View style={styles.root}>
        <StatusBar style="light" />
        <HazeBackground />
        <MainHeader
          showBack
          title={isEditMode ? '게시물 수정' : '새 피드작성'}
          onBack={() => navigation.goBack()}
        />

        <KeyboardAvoidingView
          style={styles.flex}
          behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        >
          <ScrollView
            contentContainerStyle={styles.body}
            showsVerticalScrollIndicator={false}
            keyboardShouldPersistTaps="handled"
          >
            {/* 선택한 실제 인증 미디어를 표시합니다. */}
            <Pressable
              disabled={isEditMode}
              onPress={() => setModalOpen(true)}
            >
              {mediaUrl ? (
                <QuestMediaPreview
                  uri={mediaUrl}
                  mediaType={mediaType}
                  style={styles.mediaFilled}
                  nativeControls={mediaType === 'VIDEO'}
                />
              ) : (
                <View style={styles.mediaEmpty}>
                  <Text style={styles.mediaEmptyText}>미디어를 선택하세요</Text>
                </View>
              )}
            </Pressable>

            {/* 게시글 본문을 입력합니다. */}
            <View style={styles.field}>
              <TextInput
                value={body}
                onChangeText={setBody}
                placeholder="오늘의 선행을 공유해보세요"
                placeholderTextColor={colors.textMuted}
                multiline
                maxLength={BODY_MAX}
                style={styles.input}
              />
            </View>

            <Text style={styles.counter}>
              {body.length}/{BODY_MAX}
            </Text>
          </ScrollView>

          {/* 미디어를 선택한 경우에만 실제 업로드를 허용합니다. */}
          <View style={[styles.footer, { paddingBottom: insets.bottom + 16 }]}>
            <SpringButton
              onPress={onUpload}
              active={canUpload}
              disabled={!canUpload}
              bgColors={[colors.disabled, colors.primaryDark]}
              style={[styles.uploadBtn, canUpload && shadow.button]}
            >
              {uploading ? (
                <ActivityIndicator color={colors.white} />
              ) : (
                <Text style={styles.uploadText}>
                  {isEditMode ? '수정 완료' : '업로드하기'}
                </Text>
              )}
            </SpringButton>
          </View>
        </KeyboardAvoidingView>

        {/* 실제 승인 퀘스트 인증 내역 선택 팝업입니다. */}
        {!isEditMode ? (
          <LoadVerifyModal
            visible={modalOpen}
            mediaItems={mediaItems}
            selectedKey={selected?.selectionKey ?? null}
            loading={loadingSubmissions}
            error={submissionError}
            onClose={() => setModalOpen(false)}
            onLoad={(mediaItem) => {
              setSelected(mediaItem);
              setModalOpen(false);
            }}
          />
        ) : null}
      </View>
    );
  }

  /* ---------- 퀘스트 인증 내역 불러오기 ---------- */
  function LoadVerifyModal({
    visible,
    mediaItems,
    selectedKey,
    loading,
    error,
    onClose,
    onLoad,
  }: {
    visible: boolean;
    mediaItems: SelectableQuestMedia[];
    selectedKey: string | null;
    loading: boolean;
    error: string | null;
    onClose: () => void;
    onLoad: (mediaItem: SelectableQuestMedia) => void;
  }) {
    const [temporarySelectedKey, setTemporarySelectedKey] =
      useState<string | null>(selectedKey);

    useEffect(() => {
      if (visible) {
        setTemporarySelectedKey(selectedKey);
      }
    }, [selectedKey, visible]);

    const chosen = useMemo(
      () =>
        mediaItems.find(
          (item) =>
            item.selectionKey === temporarySelectedKey,
        ) ?? null,
      [mediaItems, temporarySelectedKey],
    );

    return (
      <Modal
        visible={visible}
        transparent
        animationType="none"
        onRequestClose={onClose}
        statusBarTranslucent
      >
        <View style={modalStyles.center}>
          <Animated.View
            entering={FadeIn.duration(180)}
            exiting={FadeOut.duration(160)}
            style={StyleSheet.absoluteFill}
          >
            <Pressable
              style={modalStyles.backdrop}
              onPress={onClose}
            />
          </Animated.View>

          <Animated.View
            entering={ZoomIn.duration(200)}
            exiting={FadeOut.duration(140)}
            style={modalStyles.card}
          >
            <Text style={modalStyles.title}>
              퀘스트 인증 내역 불러오기
            </Text>

            {loading ? (
              <View style={modalStyles.stateWrap}>
                <ActivityIndicator color={colors.primaryDark} />
                <Text style={modalStyles.stateText}>
                  인증 내역을 불러오는 중입니다
                </Text>
              </View>
            ) : error ? (
              <View style={modalStyles.stateWrap}>
                <Text style={modalStyles.errorText}>
                  {error}
                </Text>
              </View>
            ) : mediaItems.length === 0 ? (
              <View style={modalStyles.stateWrap}>
                <Text style={modalStyles.stateText}>
                  게시글에 사용할 승인 인증 미디어가 없습니다
                </Text>
              </View>
            ) : (
              <ScrollView
                style={modalStyles.gridScroll}
                contentContainerStyle={modalStyles.grid}
                showsVerticalScrollIndicator={false}
              >
                {mediaItems.map((item) => {
                  const isSelected =
                    temporarySelectedKey === item.selectionKey;

                  return (
                    <Pressable
                      key={item.selectionKey}
                      style={modalStyles.cellWrap}
                      onPress={() =>
                        setTemporarySelectedKey(
                          item.selectionKey,
                        )
                      }
                    >
                      <View
                        pointerEvents="none"
                        style={modalStyles.cell}
                      >
                        <QuestMediaPreview
                          uri={item.media_url}
                          mediaType={item.media_type}
                          style={modalStyles.cellImage}
                        />

                        {isSelected ? (
                          <View style={modalStyles.checkBadge}>
                            <WhiteCheck size={14} />
                          </View>
                        ) : null}

                        <View style={modalStyles.questBadge}>
                          <Text style={modalStyles.questBadgeText}>
                            Quest #{item.quest_id}
                          </Text>
                        </View>
                      </View>
                    </Pressable>
                  );
                })}
              </ScrollView>
            )}

            <View style={modalStyles.btnRow}>
              <SpringButton
                onPress={() => chosen && onLoad(chosen)}
                active={chosen !== null}
                disabled={chosen === null}
                style={[
                  modalStyles.btn,
                  chosen
                    ? modalStyles.load
                    : modalStyles.loadDisabled,
                ]}
              >
                <Text style={modalStyles.loadText}>
                  불러오기
                </Text>
              </SpringButton>

              <SpringButton
                onPress={onClose}
                style={[
                  modalStyles.btn,
                  modalStyles.cancel,
                ]}
              >
                <Text style={modalStyles.cancelText}>
                  취소
                </Text>
              </SpringButton>
            </View>
          </Animated.View>
        </View>
      </Modal>
    );
  }

  const styles = StyleSheet.create({
    root: {
      flex: 1,
      backgroundColor: colors.screenBg,
    },
    flex: {
      flex: 1,
    },
    body: {
      padding: 16,
      paddingBottom: 120,
    },

    mediaEmpty: {
      width: '100%',
      aspectRatio: 1,
      borderRadius: 14,
      borderWidth: 2,
      borderStyle: 'dashed',
      borderColor: '#C9D6CE',
      backgroundColor: 'rgba(255,255,255,0.5)',
      alignItems: 'center',
      justifyContent: 'center',
    },
    mediaEmptyText: {
      fontSize: 13,
      color: colors.textMuted,
      fontFamily: fonts.bodyR,
    },
    mediaFilled: {
      width: '100%',
      aspectRatio: 1,
      borderRadius: 14,
      backgroundColor: colors.inputBorder,
    },

    field: {
      marginTop: 16,
      borderRadius: radii.input,
      borderWidth: 1,
      borderColor: colors.inputBorder,
      backgroundColor: colors.white,
    },
    input: {
      minHeight: 120,
      padding: 14,
      fontSize: 15,
      color: colors.textPrimary,
      fontFamily: fonts.bodyR,
      textAlignVertical: 'top',
    },
    counter: {
      alignSelf: 'flex-end',
      marginTop: 6,
      fontSize: 12,
      color: colors.textMuted,
      fontFamily: fonts.bodyR,
    },

    footer: {
      position: 'absolute',
      right: 0,
      bottom: 0,
      left: 0,
      paddingHorizontal: 20,
      paddingTop: 12,
      backgroundColor: colors.screenBg,
    },
    uploadBtn: {
      height: 52,
      borderRadius: radii.button,
      alignItems: 'center',
      justifyContent: 'center',
    },
    uploadText: {
      color: colors.white,
      fontSize: 16,
      fontWeight: '700',
      fontFamily: fonts.bodyB,
    },
  });

  const modalStyles = StyleSheet.create({
    center: {
      flex: 1,
      alignItems: 'center',
      justifyContent: 'center',
      padding: 16,
    },
    backdrop: {
      flex: 1,
      backgroundColor: 'rgba(0,0,0,0.45)',
    },
    card: {
      width: '100%',
      maxWidth: 361,
      maxHeight: '82%',
      backgroundColor: colors.white,
      borderRadius: 14,
      padding: 16,
      ...shadow.card,
      shadowOpacity: 0.35,
      shadowRadius: 50,
    },
    title: {
      textAlign: 'center',
      fontSize: 15,
      fontWeight: '700',
      color: colors.textPrimary,
      marginBottom: 14,
      fontFamily: fonts.bodyB,
    },
    stateWrap: {
      minHeight: 220,
      alignItems: 'center',
      justifyContent: 'center',
      gap: 12,
    },
    stateText: {
      paddingHorizontal: 20,
      textAlign: 'center',
      fontSize: 13,
      color: colors.textMuted,
      fontFamily: fonts.bodyR,
    },
    errorText: {
      paddingHorizontal: 20,
      textAlign: 'center',
      fontSize: 13,
      color: colors.danger,
      fontFamily: fonts.bodyR,
    },
    gridScroll: {
      flexGrow: 0,
      maxHeight: 440,
      marginBottom: 16,
    },
    grid: {
      flexDirection: 'row',
      flexWrap: 'wrap',
      marginHorizontal: -3,
    },
    cellWrap: {
      width: '50%',
      padding: 3,
    },
    cell: {
      width: '100%',
      aspectRatio: 1,
      borderRadius: 10,
      overflow: 'hidden',
      backgroundColor: colors.inputBorder,
    },
    cellImage: {
      width: '100%',
      height: '100%',
    },
    checkBadge: {
      position: 'absolute',
      top: 6,
      right: 6,
      width: 22,
      height: 22,
      borderRadius: 11,
      backgroundColor: colors.primaryDark,
      alignItems: 'center',
      justifyContent: 'center',
    },
    questBadge: {
      position: 'absolute',
      bottom: 6,
      left: 6,
      paddingHorizontal: 7,
      height: 22,
      borderRadius: 11,
      backgroundColor: 'rgba(0,0,0,0.5)',
      alignItems: 'center',
      justifyContent: 'center',
    },
    questBadgeText: {
      color: colors.white,
      fontSize: 10,
      fontFamily: fonts.bodyM,
    },
    btnRow: {
      flexDirection: 'row',
      gap: 10,
    },
    btn: {
      flex: 1,
      height: 44,
      borderRadius: 10,
      alignItems: 'center',
      justifyContent: 'center',
    },
    load: {
      backgroundColor: colors.primaryDark,
    },
    loadDisabled: {
      backgroundColor: colors.disabled,
    },
    loadText: {
      color: colors.white,
      fontSize: 14,
      fontWeight: '700',
      fontFamily: fonts.bodyB,
    },
    cancel: {
      backgroundColor: colors.googleBg,
    },
    cancelText: {
      color: colors.textPrimary,
      fontSize: 14,
      fontWeight: '600',
      fontFamily: fonts.bodyM,
    },
  });