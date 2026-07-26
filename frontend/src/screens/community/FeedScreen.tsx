/**
 * SCREEN 03·1 — 커뮤니티 메인 · 피드 (route: Feed, 커뮤니티 tab ROOT).
 *
 * [Backend 연동 범위]
 * 1. 기본 피드 조회
 * 2. 좋아요 토글 및 좋아요 사용자 목록 조회
 * 3. 댓글 목록 조회 및 댓글 작성
 * 4. 관심 없음 기록 후 현재 화면에서 게시글 숨김
 * 5. 게시글 신고 접수
 */
import React, { useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  Image,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  useWindowDimensions,
  View,
} from 'react-native';
import { StatusBar } from 'expo-status-bar';
import Animated, { FadeInDown } from 'react-native-reanimated';
import { colors, fonts, gamePopup } from '../../theme';
import HazeBackground from '../../components/HazeBackground';
import MainHeader from '../../components/MainHeader';
import SpringButton from '../../components/SpringButton';
import BottomSheet from '../../components/BottomSheet';
import GamePopup from '../../components/GamePopup';
import Shimmer from '../../components/Shimmer';
import { useToast } from '../../components/Toast';
import {
  CommunityComment,
  CommunityFeedItem,
  PostLikeUser,
  createCommunityPostComment,
  getCommunityFeed,
  getCommunityPostComments,
  getCommunityPostLikeUsers,
  markCommunityPostNotInterested,
  reportCommunityPost,
  toggleCommunityPostLike,
} from '../../api/community';
import {
  Avatar,
  CommentIcon,
  DotsIcon,
  HeartButton,
  SheetCloseChevron,
  SheetTitle,
  SirenIcon,
  XCircleIcon,
} from './_parts';

const AVS: [string, string][] = [
  ['#4CAF50', '#2E7D32'],
  ['#5B9BD5', '#2E5A9B'],
  ['#E57373', '#B04A4A'],
  ['#FF9E5A', '#B96A28'],
  ['#B27BD0', '#7A4A9B'],
];

const COMMENT_MAX_LENGTH = 500;

type LikeState = {
  liked: boolean;
  count: number;
  submitting: boolean;
};

export default function FeedScreen({ navigation }: any) {
  const toast = useToast();

  const [loading, setLoading] = useState(true);
  const [feedError, setFeedError] = useState<string | null>(null);
  const [feeds, setFeeds] = useState<CommunityFeedItem[]>([]);
  const [likes, setLikes] = useState<Record<string, LikeState>>({});
  const [hidden, setHidden] = useState<Record<string, boolean>>({});

  const [commentsPostId, setCommentsPostId] = useState<number | null>(null);
  const [comments, setComments] = useState<CommunityComment[]>([]);
  const [commentsLoading, setCommentsLoading] = useState(false);
  const [commentText, setCommentText] = useState('');
  const [commentSubmitting, setCommentSubmitting] = useState(false);

  const [likesPostId, setLikesPostId] = useState<number | null>(null);
  const [likeUsers, setLikeUsers] = useState<PostLikeUser[]>([]);
  const [likeUsersLoading, setLikeUsersLoading] = useState(false);

  const [morePostId, setMorePostId] = useState<number | null>(null);
  const [hidingPostId, setHidingPostId] = useState<number | null>(null);
  const [reportPostId, setReportPostId] = useState<number | null>(null);

  useEffect(() => {
    let mounted = true;

    const loadFeed = async () => {
      try {
        setLoading(true);
        setFeedError(null);

        const result = await getCommunityFeed();

        if (!mounted) {
          return;
        }

        setFeeds(result);
        setLikes(
          Object.fromEntries(
            result.map((feed) => [
              String(feed.post_id),
              {
                liked: feed.is_liked,
                count: feed.like_count,
                submitting: false,
              },
            ]),
          ),
        );
      } catch (error) {
        console.error('커뮤니티 피드 조회 실패:', error);

        if (mounted) {
          setFeedError('피드를 불러오지 못했습니다.');
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };

    loadFeed();

    return () => {
      mounted = false;
    };
  }, []);

  const visibleFeeds = useMemo(
    () => feeds.filter((feed) => !hidden[String(feed.post_id)]),
    [feeds, hidden],
  );

  const updateFeedCommentCount = (postId: number, difference: number) => {
    setFeeds((currentFeeds) =>
      currentFeeds.map((feed) =>
        feed.post_id === postId
          ? {
              ...feed,
              comment_count: Math.max(0, feed.comment_count + difference),
            }
          : feed,
      ),
    );
  };

  const handleToggleLike = async (postId: number) => {
    const key = String(postId);
    const currentLike = likes[key];

    if (!currentLike || currentLike.submitting) {
      return;
    }

    setLikes((current) => ({
      ...current,
      [key]: {
        ...current[key],
        submitting: true,
      },
    }));

    try {
      const result = await toggleCommunityPostLike(postId);

      setLikes((current) => ({
        ...current,
        [key]: {
          liked: result.is_liked,
          count: result.like_count,
          submitting: false,
        },
      }));
    } catch (error) {
      console.error('좋아요 토글 실패:', error);
      setLikes((current) => ({
        ...current,
        [key]: {
          ...current[key],
          submitting: false,
        },
      }));
      toast.show('좋아요 처리에 실패했습니다');
    }
  };

  const openLikeUsers = async (postId: number) => {
    setLikesPostId(postId);
    setLikeUsers([]);
    setLikeUsersLoading(true);

    try {
      const result = await getCommunityPostLikeUsers(postId);
      setLikeUsers(result);
    } catch (error) {
      console.error('좋아요 사용자 목록 조회 실패:', error);
      toast.show('좋아요 목록을 불러오지 못했습니다');
    } finally {
      setLikeUsersLoading(false);
    }
  };

  const closeLikeUsers = () => {
    setLikesPostId(null);
    setLikeUsers([]);
    setLikeUsersLoading(false);
  };

  const openComments = async (postId: number) => {
    setCommentsPostId(postId);
    setComments([]);
    setCommentText('');
    setCommentsLoading(true);

    try {
      const result = await getCommunityPostComments(postId);
      setComments(result);
    } catch (error) {
      console.error('댓글 목록 조회 실패:', error);
      toast.show('댓글을 불러오지 못했습니다');
    } finally {
      setCommentsLoading(false);
    }
  };

  const closeComments = () => {
    if (commentSubmitting) {
      return;
    }

    setCommentsPostId(null);
    setComments([]);
    setCommentText('');
    setCommentsLoading(false);
  };

  const submitComment = async () => {
    if (commentsPostId === null || commentSubmitting) {
      return;
    }

    const content = commentText.trim();

    if (!content) {
      return;
    }

    try {
      setCommentSubmitting(true);
      const createdComment = await createCommunityPostComment(
        commentsPostId,
        content,
      );

      setComments((current) => [...current, createdComment]);
      setCommentText('');
      updateFeedCommentCount(commentsPostId, 1);
      toast.show('댓글이 등록되었습니다');
    } catch (error) {
      console.error('댓글 작성 실패:', error);
      toast.show('댓글 등록에 실패했습니다');
    } finally {
      setCommentSubmitting(false);
    }
  };

  const hideFeed = async (postId: number) => {
    if (hidingPostId !== null) {
      return;
    }

    setMorePostId(null);
    setHidingPostId(postId);

    try {
      await markCommunityPostNotInterested(postId);
      setHidden((current) => ({
        ...current,
        [String(postId)]: true,
      }));
      toast.show('숨겼어요');
    } catch (error) {
      console.error('관심 없음 처리 실패:', error);
      toast.show('관심 없음 처리에 실패했습니다');
    } finally {
      setHidingPostId(null);
    }
  };

  const submitReport = async (reason: string) => {
    if (reportPostId === null) {
      return;
    }

    try {
      await reportCommunityPost(reportPostId, {
        reason,
      });

      setReportPostId(null);
      toast.show('신고가 접수되었습니다');
    } catch (error) {
      console.error('게시글 신고 실패:', error);
      toast.show('신고 접수에 실패했습니다');
      throw error;
    }
  };

  return (
    <View style={styles.root}>
      <StatusBar style="light" />
      <HazeBackground />
      <MainHeader />

      <View style={styles.topActions}>
        <SpringButton
          style={[styles.actBtn, styles.actOutline]}
          onPress={() => navigation.navigate('TeamHome')}
        >
          <Text style={styles.actOutlineText}>⚔ 팀 챌린지</Text>
        </SpringButton>
        <SpringButton
          style={[styles.actBtn, styles.actFill]}
          onPress={() => navigation.navigate('NewPost')}
        >
          <Text style={styles.actFillText}>✎ 피드 작성</Text>
        </SpringButton>
      </View>

      {loading ? (
        <View style={styles.skeletonWrap}>
          {[0, 1].map((index) => (
            <View key={index} style={styles.card}>
              <View style={styles.cardHead}>
                <Shimmer width={36} height={36} radius={18} />
                <Shimmer
                  width={110}
                  height={12}
                  radius={6}
                  style={{ marginLeft: 10 }}
                />
              </View>
              <Shimmer
                width="100%"
                height={0}
                radius={0}
                style={styles.skelPhoto}
              />
              <View style={styles.cardBody}>
                <Shimmer width={140} height={12} radius={6} />
                <Shimmer
                  width="86%"
                  height={12}
                  radius={6}
                  style={{ marginTop: 10 }}
                />
              </View>
            </View>
          ))}
        </View>
      ) : feedError ? (
        <View style={styles.empty}>
          <Text style={styles.emptyText}>{feedError}</Text>
        </View>
      ) : visibleFeeds.length === 0 ? (
        <View style={styles.empty}>
          <Text style={styles.emptyText}>아직 게시물이 없어요</Text>
        </View>
      ) : (
        <ScrollView
          contentContainerStyle={styles.listContent}
          showsVerticalScrollIndicator={false}
        >
          {visibleFeeds.map((feed, index) => {
            const feedKey = String(feed.post_id);
            const likeState = likes[feedKey] ?? {
              liked: feed.is_liked,
              count: feed.like_count,
              submitting: false,
            };
            const avatarGradient = AVS[Math.abs(feed.author.user_id) % AVS.length];

            return (
              <Animated.View
                key={feed.post_id}
                entering={FadeInDown.delay(50 + index * 100).duration(380)}
                style={styles.card}
              >
                <View style={styles.cardHead}>
                  <Pressable
                    style={styles.authorBtn}
                    onPress={() =>
                      navigation.navigate('UserDetail', {
                        user: {
                          name: feed.author.nickname,
                          grad: avatarGradient,
                        },
                      })
                    }
                  >
                    <Avatar grad={avatarGradient} />
                    <Text style={styles.userName}>{feed.author.nickname}</Text>
                  </Pressable>
                  <Pressable
                    onPress={() => setMorePostId(feed.post_id)}
                    hitSlop={6}
                    style={styles.dotsBtn}
                  >
                    <DotsIcon />
                  </Pressable>
                </View>

                <Image
                  source={{ uri: feed.media_url }}
                  style={styles.photo}
                  resizeMode="cover"
                />

                <View style={styles.cardBody}>
                  <View style={styles.actionRow}>
                    <View style={styles.likeGroup}>
                      <View
                        pointerEvents={likeState.submitting ? 'none' : 'auto'}
                        style={likeState.submitting ? styles.disabledAction : undefined}
                      >
                        <HeartButton
                          liked={likeState.liked}
                          onToggle={() => handleToggleLike(feed.post_id)}
                        />
                      </View>
                      <Pressable
                        onPress={() => openLikeUsers(feed.post_id)}
                        hitSlop={6}
                      >
                        <Text style={styles.likeCount}>{likeState.count}개</Text>
                      </Pressable>
                    </View>
                    <Pressable
                      style={styles.commentGroup}
                      onPress={() => openComments(feed.post_id)}
                      hitSlop={6}
                    >
                      <CommentIcon />
                      <Text style={styles.commentCount}>{feed.comment_count}</Text>
                    </Pressable>
                  </View>

                  <Text style={styles.caption}>
                    <Text style={styles.captionUser}>{feed.author.nickname}</Text>
                    {feed.caption ? ` ${feed.caption}` : ''}
                  </Text>

                  <Pressable
                    onPress={() => openComments(feed.post_id)}
                    hitSlop={4}
                  >
                    <Text style={styles.viewComments}>
                      댓글 {feed.comment_count}개 모두 보기
                    </Text>
                  </Pressable>
                </View>
              </Animated.View>
            );
          })}
        </ScrollView>
      )}

      <BottomSheet
        visible={commentsPostId !== null}
        onClose={closeComments}
      >
        <SheetTitle text={`댓글 ${comments.length}개`} />

        {commentsLoading ? (
          <View style={styles.sheetLoading}>
            <ActivityIndicator />
            <Text style={styles.sheetLoadingText}>댓글을 불러오는 중입니다</Text>
          </View>
        ) : comments.length === 0 ? (
          <View style={styles.sheetEmpty}>
            <Text style={styles.sheetEmptyText}>아직 댓글이 없습니다</Text>
          </View>
        ) : (
          <ScrollView
            style={styles.commentScroll}
            keyboardShouldPersistTaps="handled"
            showsVerticalScrollIndicator={false}
          >
            <View style={styles.sheetList}>
              {comments.map((comment) => {
                const commentGradient =
                  AVS[Math.abs(comment.author.user_id) % AVS.length];

                return (
                  <Pressable
                    key={comment.comment_id}
                    style={styles.commentRow}
                    onPress={() => {
                      closeComments();
                      navigation.navigate('UserDetail', {
                        user: {
                          name: comment.author.nickname,
                          grad: commentGradient,
                        },
                      });
                    }}
                  >
                    <Avatar grad={commentGradient} />
                    <View style={styles.commentTextWrap}>
                      <Text style={styles.rowUser}>
                        {comment.author.nickname}
                      </Text>
                      <Text style={styles.commentText}>{comment.content}</Text>
                    </View>
                  </Pressable>
                );
              })}
            </View>
          </ScrollView>
        )}

        <View style={styles.commentComposer}>
          <TextInput
            value={commentText}
            onChangeText={setCommentText}
            placeholder="댓글을 입력해주세요"
            placeholderTextColor={colors.textSecondary}
            maxLength={COMMENT_MAX_LENGTH}
            editable={!commentSubmitting}
            style={styles.commentInput}
            returnKeyType="send"
            onSubmitEditing={submitComment}
          />
          <Pressable
            disabled={!commentText.trim() || commentSubmitting}
            onPress={submitComment}
            style={[
              styles.commentSubmit,
              (!commentText.trim() || commentSubmitting) &&
                styles.commentSubmitDisabled,
            ]}
          >
            {commentSubmitting ? (
              <ActivityIndicator size="small" color={colors.white} />
            ) : (
              <Text style={styles.commentSubmitText}>등록</Text>
            )}
          </Pressable>
        </View>

        <SheetCloseChevron onPress={closeComments} />
      </BottomSheet>

      <BottomSheet
        visible={likesPostId !== null}
        onClose={closeLikeUsers}
      >
        <SheetTitle
          text={`좋아요 ${
            likesPostId !== null
              ? likes[String(likesPostId)]?.count ?? 0
              : 0
          }개`}
        />

        {likeUsersLoading ? (
          <View style={styles.sheetLoading}>
            <ActivityIndicator />
            <Text style={styles.sheetLoadingText}>
              좋아요 목록을 불러오는 중입니다
            </Text>
          </View>
        ) : likeUsers.length === 0 ? (
          <View style={styles.sheetEmpty}>
            <Text style={styles.sheetEmptyText}>아직 좋아요가 없습니다</Text>
          </View>
        ) : (
          <ScrollView
            style={styles.likerScroll}
            showsVerticalScrollIndicator={false}
          >
            <View style={styles.sheetList}>
              {likeUsers.map((user) => {
                const userGradient = AVS[Math.abs(user.user_id) % AVS.length];

                return (
                  <Pressable
                    key={user.user_id}
                    style={styles.likerRow}
                    onPress={() => {
                      closeLikeUsers();
                      navigation.navigate('UserDetail', {
                        user: {
                          name: user.nickname,
                          grad: userGradient,
                        },
                      });
                    }}
                  >
                    <Avatar grad={userGradient} />
                    <Text style={styles.likerUser}>{user.nickname}</Text>
                  </Pressable>
                );
              })}
            </View>
          </ScrollView>
        )}

        <SheetCloseChevron onPress={closeLikeUsers} />
      </BottomSheet>

      <BottomSheet
        visible={morePostId !== null}
        onClose={() => setMorePostId(null)}
      >
        <Pressable
          disabled={hidingPostId !== null}
          style={[styles.moreRow, styles.moreDivider]}
          onPress={() => {
            if (morePostId !== null) {
              hideFeed(morePostId);
            }
          }}
        >
          <XCircleIcon />
          <Text style={styles.moreText}>관심없음</Text>
        </Pressable>
        <Pressable
          style={styles.moreRow}
          onPress={() => {
            const postId = morePostId;
            setMorePostId(null);
            setReportPostId(postId);
          }}
        >
          <SirenIcon />
          <Text style={[styles.moreText, styles.moreDanger]}>신고하기</Text>
        </Pressable>
      </BottomSheet>

      <ReportPopup
        visible={reportPostId !== null}
        onClose={() => setReportPostId(null)}
        onSubmit={submitReport}
      />
    </View>
  );
}

function ReportPopup({
  visible,
  onClose,
  onSubmit,
}: {
  visible: boolean;
  onClose: () => void;
  onSubmit: (reason: string) => Promise<void>;
}) {
  const { width } = useWindowDimensions();
  const [reason, setReason] = useState('');
  const [focused, setFocused] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const filled = reason.trim().length > 0;

  useEffect(() => {
    if (!visible) {
      setReason('');
      setFocused(false);
      setSubmitting(false);
    }
  }, [visible]);

  const close = () => {
    if (submitting) {
      return;
    }

    setReason('');
    setFocused(false);
    onClose();
  };

  const submit = async () => {
    const trimmedReason = reason.trim();

    if (!trimmedReason || submitting) {
      return;
    }

    try {
      setSubmitting(true);
      await onSubmit(trimmedReason);
      setReason('');
      setFocused(false);
    } catch (error) {
      console.error('게시글 신고 실패:', error);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <GamePopup
      visible={visible}
      onClose={close}
      width={Math.min(345, width - 48)}
      style={rp.frame}
    >
      <View style={rp.body}>
        <Text style={rp.title}>이 게시물을 신고하는 이유</Text>
        <Text style={rp.desc}>
          회원님의 신고는 익명으로 처리됩니다. 누군가 위급한 상황에 있다고
          생각된다면 즉시 현지 응급 서비스 기관에 연락하시기 바랍니다.
        </Text>

        <View
          style={[
            rp.field,
            {
              borderColor: focused
                ? colors.primaryDark
                : 'rgba(212,160,23,0.4)',
              borderWidth: focused ? 2 : 1.5,
            },
          ]}
        >
          <TextInput
            value={reason}
            onChangeText={setReason}
            onFocus={() => setFocused(true)}
            onBlur={() => setFocused(false)}
            placeholder="신고 사유를 입력해주세요."
            placeholderTextColor="rgba(245,236,203,0.45)"
            multiline
            maxLength={200}
            editable={!submitting}
            style={rp.input}
          />
        </View>
        <Text style={rp.counter}>{reason.length}/200</Text>

        <View style={rp.btnRow}>
          <Pressable
            disabled={!filled || submitting}
            onPress={submit}
            style={[
              rp.btn,
              filled && !submitting ? rp.reportOn : rp.reportOff,
            ]}
          >
            {submitting ? (
              <ActivityIndicator size="small" color={colors.white} />
            ) : (
              <Text style={rp.reportText}>신고하기</Text>
            )}
          </Pressable>
          <Pressable
            disabled={submitting}
            onPress={close}
            style={[rp.btn, rp.cancel]}
          >
            <Text style={rp.cancelText}>취소</Text>
          </Pressable>
        </View>
      </View>
    </GamePopup>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: colors.screenBg,
  },
  topActions: {
    flexDirection: 'row',
    gap: 10,
    paddingHorizontal: 16,
    paddingVertical: 10,
    backgroundColor: colors.white,
    borderBottomWidth: 1,
    borderBottomColor: colors.inputBorder,
  },
  actBtn: {
    flex: 1,
    height: 42,
    borderRadius: 999,
    alignItems: 'center',
    justifyContent: 'center',
  },
  actOutline: {
    borderWidth: 1.5,
    borderColor: colors.primaryDark,
    backgroundColor: colors.white,
  },
  actOutlineText: {
    fontSize: 14,
    fontWeight: '700',
    color: colors.primaryDark,
    fontFamily: fonts.bodyB,
  },
  actFill: {
    backgroundColor: colors.primaryDark,
  },
  actFillText: {
    fontSize: 14,
    fontWeight: '700',
    color: colors.parchment,
    fontFamily: fonts.bodyB,
  },
  listContent: {
    paddingTop: 12,
    paddingBottom: 20,
  },
  skeletonWrap: {
    paddingTop: 12,
  },
  card: {
    backgroundColor: colors.white,
    marginBottom: 8,
  },
  cardHead: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 11,
    paddingHorizontal: 14,
  },
  authorBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
  },
  userName: {
    flex: 1,
    marginLeft: 10,
    fontSize: 13,
    fontWeight: '700',
    color: colors.textPrimary,
    fontFamily: fonts.bodyB,
  },
  dotsBtn: {
    width: 32,
    height: 32,
    alignItems: 'center',
    justifyContent: 'center',
  },
  photo: {
    width: '100%',
    aspectRatio: 1,
  },
  skelPhoto: {
    aspectRatio: 1,
    height: undefined,
  },
  cardBody: {
    paddingHorizontal: 14,
    paddingTop: 12,
    paddingBottom: 14,
  },
  actionRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
  },
  likeGroup: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginRight: 16,
  },
  disabledAction: {
    opacity: 0.55,
  },
  likeCount: {
    fontSize: 13,
    fontWeight: '600',
    color: colors.textPrimary,
    fontFamily: fonts.bodyM,
  },
  commentGroup: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  commentCount: {
    fontSize: 13,
    color: colors.textPrimary,
    fontFamily: fonts.bodyR,
  },
  caption: {
    fontSize: 13,
    color: colors.textPrimary,
    lineHeight: 20,
    fontFamily: fonts.bodyR,
  },
  captionUser: {
    fontWeight: '700',
    fontFamily: fonts.bodyB,
  },
  viewComments: {
    fontSize: 13,
    color: colors.textSecondary,
    marginTop: 6,
    fontFamily: fonts.bodyR,
  },
  empty: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  emptyText: {
    fontSize: 14,
    color: colors.textSecondary,
    fontFamily: fonts.bodyM,
  },
  sheetList: {
    paddingTop: 4,
  },
  sheetLoading: {
    minHeight: 130,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
  },
  sheetLoadingText: {
    fontSize: 13,
    color: colors.textSecondary,
    fontFamily: fonts.bodyR,
  },
  sheetEmpty: {
    minHeight: 110,
    alignItems: 'center',
    justifyContent: 'center',
  },
  sheetEmptyText: {
    fontSize: 13,
    color: colors.textSecondary,
    fontFamily: fonts.bodyR,
  },
  commentScroll: {
    maxHeight: 280,
  },
  commentRow: {
    flexDirection: 'row',
    gap: 10,
    paddingVertical: 13,
  },
  commentTextWrap: {
    flex: 1,
  },
  rowUser: {
    fontSize: 13,
    fontWeight: '700',
    color: colors.textPrimary,
    fontFamily: fonts.bodyB,
  },
  commentText: {
    fontSize: 13,
    color: colors.textPrimary,
    marginTop: 2,
    fontFamily: fonts.bodyR,
    lineHeight: 19,
  },
  commentComposer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginTop: 10,
    marginBottom: 4,
  },
  commentInput: {
    flex: 1,
    height: 44,
    borderWidth: 1,
    borderColor: colors.inputBorder,
    borderRadius: 12,
    paddingHorizontal: 12,
    fontSize: 13,
    color: colors.textPrimary,
    backgroundColor: colors.white,
    fontFamily: fonts.bodyR,
  },
  commentSubmit: {
    width: 58,
    height: 44,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.primaryDark,
  },
  commentSubmitDisabled: {
    opacity: 0.4,
  },
  commentSubmitText: {
    fontSize: 13,
    fontWeight: '700',
    color: colors.white,
    fontFamily: fonts.bodyB,
  },
  likerScroll: {
    maxHeight: 330,
  },
  likerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    paddingVertical: 10,
  },
  likerUser: {
    fontSize: 14,
    fontWeight: '700',
    color: colors.textPrimary,
    fontFamily: fonts.bodyB,
  },
  moreRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 14,
    height: 56,
    marginHorizontal: -20,
    paddingHorizontal: 20,
  },
  moreDivider: {
    borderBottomWidth: 1,
    borderBottomColor: colors.inputBorder,
  },
  moreText: {
    fontSize: 15,
    color: colors.textPrimary,
    fontFamily: fonts.bodyR,
  },
  moreDanger: {
    color: colors.danger,
    fontWeight: '700',
    fontFamily: fonts.bodyB,
  },
});

const rp = StyleSheet.create({
  frame: {
    borderColor: colors.gold,
  },
  body: {
    width: '100%',
  },
  title: {
    fontFamily: fonts.pixel,
    fontSize: 16,
    color: '#F5ECCB',
    textAlign: 'center',
    marginBottom: 12,
  },
  desc: {
    fontSize: 13,
    color: '#B9C9BD',
    textAlign: 'center',
    lineHeight: 21,
    marginBottom: 18,
  },
  field: {
    borderRadius: 10,
    backgroundColor: 'rgba(255,255,255,0.08)',
  },
  input: {
    height: 100,
    padding: 12,
    fontSize: 14,
    color: '#F5ECCB',
    fontFamily: fonts.bodyR,
    textAlignVertical: 'top',
  },
  counter: {
    alignSelf: 'flex-end',
    marginTop: 6,
    fontSize: 11,
    color: 'rgba(245,236,203,0.55)',
    fontFamily: fonts.bodyR,
  },
  btnRow: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 12,
  },
  btn: {
    flex: 1,
    height: 48,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
  },
  reportOn: {
    backgroundColor: colors.danger,
    borderWidth: 1.5,
    borderColor: '#FF8A8A',
  },
  reportOff: {
    backgroundColor: colors.disabled,
    borderWidth: 1.5,
    borderColor: 'rgba(255,255,255,0.25)',
  },
  reportText: {
    color: colors.white,
    fontSize: 14,
    fontFamily: fonts.pixel,
  },
  cancel: {
    backgroundColor: 'rgba(255,248,231,0.1)',
    borderWidth: 1,
    borderColor: '#5C6B60',
  },
  cancelText: {
    color: gamePopup.cream,
    fontSize: 14,
    fontFamily: fonts.pixel,
  },
});