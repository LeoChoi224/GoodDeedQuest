/**
 * SCREEN 03·1 — 커뮤니티 메인 · 피드 (route: Feed, 커뮤니티 tab ROOT).
 *
 * [Backend 연동 범위]
 * 1. 개인화 추천 피드 조회 및 당겨서 새로고침
 * 2. 좋아요 토글 및 좋아요 사용자 목록 조회
 * 3. 댓글 목록 조회 및 댓글 작성
 * 4. 관심 없음 기록 후 현재 화면에서 게시글 숨김
 * 5. 게시글 신고 접수
 */
import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import {
  ActivityIndicator,
  FlatList,
  Image,
  Pressable,
  RefreshControl,
  StyleSheet,
  Text,
  TextInput,
  useWindowDimensions,
  View,
} from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { useFocusEffect } from '@react-navigation/native';
import Animated, { FadeInDown } from 'react-native-reanimated';
import { colors, fonts, gamePopup } from '../../theme';
import HazeBackground from '../../components/HazeBackground';
import MainHeader from '../../components/MainHeader';
import SpringButton from '../../components/SpringButton';
import BottomSheet from '../../components/BottomSheet';
import GamePopup from '../../components/GamePopup';
import Shimmer from '../../components/Shimmer';
import { useToast } from '../../components/Toast';
import { useVideoPlayer, VideoView } from 'expo-video';
import type { VideoSource } from 'expo-video';
import {
  CommunityComment,
  CommunityFeedItem,
  PostLikeUser,
  createCommunityPostComment,
  getRecommendedCommunityFeed,
  getMyCommunityPosts,
  getCommunityPostComments,
  getCommunityPostLikeUsers,
  markCommunityPostNotInterested,
  reportCommunityPost,
  toggleCommunityPostLike,
  deleteCommunityPost,
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
  EditIcon,
  TrashIcon,
} from './_parts';

const AVS: [string, string][] = [
  ['#4CAF50', '#2E7D32'],
  ['#5B9BD5', '#2E5A9B'],
  ['#E57373', '#B04A4A'],
  ['#FF9E5A', '#B96A28'],
  ['#B27BD0', '#7A4A9B'],
];

const COMMENT_MAX_LENGTH = 500;
const SHEET_PAGE_SIZE = 20;
const RECOMMENDATION_ROTATION_SIZE = 3;

function CommunityVideo({ uri }: { uri: string }) {
  const videoSource = useMemo<VideoSource>(
    () => ({
      uri,
      useCaching: true,
      contentType: 'progressive',
    }),
    [uri],
  );

  const player = useVideoPlayer(
    videoSource,
    (videoPlayer) => {
      videoPlayer.loop = true;

      videoPlayer.bufferOptions = {
        // 끊긴 후 재생을 재개하기 전에 6초를 확보
        minBufferForPlayback: 6,

        // 8초 영상 전체를 미리 받을 수 있도록 넉넉하게 설정
        preferredForwardBufferDuration: 30,

        // 8MB 제한을 제거하고 플레이어가 자동으로 결정
        maxBufferBytes: 0,

        // Android에서 용량보다 재생 시간 확보를 우선
        prioritizeTimeOverSizeThreshold: true,

        // iOS에서 끊김을 줄이기 위해 충분히 받은 후 재생
        waitsToMinimizeStalling: true,
      };
    },
  );

  return (
    <VideoView
      player={player}
      style={styles.photo}
      contentFit="cover"
      nativeControls
    />
  );
}

function CommunityMedia({ feed }: { feed: CommunityFeedItem }) {
  if (feed.media_type === 'VIDEO') {
    return <CommunityVideo uri={feed.media_url} />;
  }

  return (
    <Image
      source={{ uri: feed.media_url }}
      style={styles.photo}
      resizeMode="cover"
    />
  );
}

/**
 * Backend 추천 점수순 상위 후보는 유지하면서
 * 상위 3개의 노출 순서만 새로고침 횟수에 따라 순환합니다.
 */
function rotateRecommendedFeed(
  feeds: CommunityFeedItem[],
  rotationStep: number,
): CommunityFeedItem[] {
  const poolSize = Math.min(
    RECOMMENDATION_ROTATION_SIZE,
    feeds.length,
  );

  if (poolSize <= 1) {
    return feeds;
  }

  const offset = rotationStep % poolSize;

  if (offset === 0) {
    return feeds;
  }

  const topCandidates = feeds.slice(0, poolSize);

  return [
    ...topCandidates.slice(offset),
    ...topCandidates.slice(0, offset),
    ...feeds.slice(poolSize),
  ];
}

type LikeState = {
  liked: boolean;
  count: number;
  submitting: boolean;
};

export default function FeedScreen({ navigation, route }: any) {
  const toast = useToast();
  const isMyPostsView = route?.name === 'MyPosts';
  const recommendationRotationRef = useRef(0);

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [feedError, setFeedError] = useState<string | null>(null);
  const [feeds, setFeeds] = useState<CommunityFeedItem[]>([]);
  const [likes, setLikes] = useState<Record<string, LikeState>>({});
  const [hidden, setHidden] = useState<Record<string, boolean>>({});

  const [commentsPostId, setCommentsPostId] = useState<number | null>(null);
  const [comments, setComments] = useState<CommunityComment[]>([]);
  const [commentsLoading, setCommentsLoading] = useState(false);
  const [commentsLoadingMore, setCommentsLoadingMore] = useState(false);
  const [commentsHasMore, setCommentsHasMore] = useState(false);
  const [commentsOffset, setCommentsOffset] = useState(0);
  const [commentText, setCommentText] = useState('');
  const [commentSubmitting, setCommentSubmitting] = useState(false);

  const [likesPostId, setLikesPostId] = useState<number | null>(null);
  const [likeUsers, setLikeUsers] = useState<PostLikeUser[]>([]);
  const [likeUsersLoading, setLikeUsersLoading] = useState(false);
  const [likeUsersLoadingMore, setLikeUsersLoadingMore] = useState(false);
  const [likeUsersHasMore, setLikeUsersHasMore] = useState(false);
  const [likeUsersOffset, setLikeUsersOffset] = useState(0);

const [morePostId, setMorePostId] = useState<number | null>(null);
const [hidingPostId, setHidingPostId] = useState<number | null>(null);
const [reportPostId, setReportPostId] = useState<number | null>(null);
const [deletePostId, setDeletePostId] = useState<number | null>(null);
const [deletingPostId, setDeletingPostId] = useState<number | null>(null);

useFocusEffect(
  useCallback(() => {
    let cancelled = false;

    const loadFeed = async () => {
      try {
        setLoading(true);
        setFeedError(null);

        const result = isMyPostsView
          ? await getMyCommunityPosts()
          : await getRecommendedCommunityFeed();

        if (cancelled) {
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
        console.error(
          isMyPostsView
            ? '내 게시물 조회 실패:'
            : '커뮤니티 피드 조회 실패:',
          error,
        );

        if (!cancelled) {
          setFeedError(
            isMyPostsView
              ? '내 게시물을 불러오지 못했습니다.'
              : '피드를 불러오지 못했습니다.',
          );
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    loadFeed();

    return () => {
      cancelled = true;
    };
  }, [isMyPostsView]),
);

  const handleRefresh = async () => {
    if (refreshing) {
      return;
    }

    try {
      setRefreshing(true);

    const fetchedFeeds = isMyPostsView
      ? await getMyCommunityPosts(0, 20)
      : await getRecommendedCommunityFeed(0, 20);

    let nextFeeds = fetchedFeeds;

    if (!isMyPostsView) {
      recommendationRotationRef.current += 1;

      nextFeeds = rotateRecommendedFeed(
        fetchedFeeds,
        recommendationRotationRef.current,
      );
    }

    setFeeds(nextFeeds);
    setLikes(
      Object.fromEntries(
        nextFeeds.map((feed) => [
          String(feed.post_id),
          {
            liked: feed.is_liked,
            count: feed.like_count,
            submitting: false,
          },
        ]),
      ),
    );

      // 새 응답을 기준으로 화면의 임시 숨김 상태를 초기화합니다.
      // 관심 없음 게시글은 Backend 추천 후보에서 이미 제외됩니다.
      setHidden({});
      setFeedError(null);
    } catch (error) {
      console.error(
        isMyPostsView
          ? '내 게시물 새로고침 실패:'
          : '개인화 피드 새로고침 실패:',
        error,
      );

      // 새로고침 실패 시 현재 화면의 기존 게시글은 그대로 유지합니다.
      toast.show('새로고침에 실패했습니다');
    } finally {
      setRefreshing(false);
    }
  };

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
    setLikeUsersLoadingMore(false);
    setLikeUsersHasMore(false);
    setLikeUsersOffset(0);

    try {
      const result = await getCommunityPostLikeUsers(
        postId,
        0,
        SHEET_PAGE_SIZE,
      );

      setLikeUsers(result);
      setLikeUsersOffset(result.length);
      setLikeUsersHasMore(result.length === SHEET_PAGE_SIZE);
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
    setLikeUsersLoadingMore(false);
    setLikeUsersHasMore(false);
    setLikeUsersOffset(0);
  };

  const loadMoreLikeUsers = async () => {
    if (
      likesPostId === null ||
      likeUsersLoading ||
      likeUsersLoadingMore ||
      !likeUsersHasMore
    ) {
      return;
    }

    try {
      setLikeUsersLoadingMore(true);

      const result = await getCommunityPostLikeUsers(
        likesPostId,
        likeUsersOffset,
        SHEET_PAGE_SIZE,
      );

      setLikeUsers((current) => {
        const currentIds = new Set(current.map((user) => user.user_id));

        return [
          ...current,
          ...result.filter((user) => !currentIds.has(user.user_id)),
        ];
      });

      setLikeUsersOffset((current) => current + result.length);
      setLikeUsersHasMore(result.length === SHEET_PAGE_SIZE);
    } catch (error) {
      console.error('좋아요 사용자 추가 조회 실패:', error);
      toast.show('좋아요 목록을 더 불러오지 못했습니다');
    } finally {
      setLikeUsersLoadingMore(false);
    }
  };

  const openComments = async (postId: number) => {
    setCommentsPostId(postId);
    setComments([]);
    setCommentText('');
    setCommentsLoading(true);
    setCommentsLoadingMore(false);
    setCommentsHasMore(false);
    setCommentsOffset(0);

    try {
      const result = await getCommunityPostComments(
        postId,
        0,
        SHEET_PAGE_SIZE,
      );

      setComments(result);
      setCommentsOffset(result.length);
      setCommentsHasMore(result.length === SHEET_PAGE_SIZE);
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
    setCommentsLoadingMore(false);
    setCommentsHasMore(false);
    setCommentsOffset(0);
  };

  const loadMoreComments = async () => {
    if (
      commentsPostId === null ||
      commentsLoading ||
      commentsLoadingMore ||
      !commentsHasMore
    ) {
      return;
    }

    try {
      setCommentsLoadingMore(true);

      const result = await getCommunityPostComments(
        commentsPostId,
        commentsOffset,
        SHEET_PAGE_SIZE,
      );

      setComments((current) => {
        const commentsById = new Map(
          current.map((comment) => [comment.comment_id, comment]),
        );

        result.forEach((comment) => {
          commentsById.set(comment.comment_id, comment);
        });

        return Array.from(commentsById.values()).sort((left, right) => {
          const createdAtDifference =
            new Date(left.created_at).getTime() -
            new Date(right.created_at).getTime();

          return createdAtDifference !== 0
            ? createdAtDifference
            : left.comment_id - right.comment_id;
        });
      });

      setCommentsOffset((current) => current + result.length);
      setCommentsHasMore(result.length === SHEET_PAGE_SIZE);
    } catch (error) {
      console.error('댓글 추가 조회 실패:', error);
      toast.show('댓글을 더 불러오지 못했습니다');
    } finally {
      setCommentsLoadingMore(false);
    }
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

  const deletePost = async () => {
    if (deletePostId === null || deletingPostId !== null) {
      return;
    }

    const postId = deletePostId;

    try {
      setDeletingPostId(postId);
      await deleteCommunityPost(postId);

      setFeeds((currentFeeds) =>
        currentFeeds.filter((feed) => feed.post_id !== postId),
      );

      setLikes((currentLikes) => {
        const nextLikes = { ...currentLikes };
        delete nextLikes[String(postId)];
        return nextLikes;
      });

      setDeletePostId(null);
      toast.show('게시물이 삭제되었습니다');
    } catch (error) {
      console.error('커뮤니티 게시글 삭제 실패:', error);
      toast.show('게시글을 삭제하지 못했습니다');
    } finally {
      setDeletingPostId(null);
    }
  };

  return (
    <View style={styles.root}>
      <StatusBar style="light" />
      <HazeBackground />
      {isMyPostsView ? (
        <MainHeader
          showBack
          title="내 게시물"
          onBack={() => navigation.goBack()}
        />
      ) : (
        <>
          <MainHeader />

          <View style={styles.topActions}>
            <SpringButton
              style={[styles.actBtn, styles.actOutline]}
              onPress={() => navigation.navigate('MyPosts')}
            >
              <Text style={styles.actOutlineText}>▣ 내 게시물</Text>
            </SpringButton>

            <SpringButton
              style={[styles.actBtn, styles.actOutline]}
              onPress={() => navigation.navigate('CommunityTeamHome')}
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
        </>
      )}

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
          <Text style={styles.emptyText}>
            {isMyPostsView
              ? '아직 올린 게시물이 없어요'
              : '아직 게시물이 없어요'}
          </Text>
        </View>
      ) : (
        <FlatList
          data={visibleFeeds}
          keyExtractor={(feed) => String(feed.post_id)}
          contentContainerStyle={styles.listContent}
          showsVerticalScrollIndicator={false}
          initialNumToRender={1}
          maxToRenderPerBatch={1}
          windowSize={2}
          updateCellsBatchingPeriod={100}
          removeClippedSubviews
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={handleRefresh}
              colors={[colors.primaryDark]}
              tintColor={colors.primaryDark}
            />
          }
          renderItem={({ item: feed, index }) => {
            const feedKey = String(feed.post_id);

            const likeState = likes[feedKey] ?? {
              liked: feed.is_liked,
              count: feed.like_count,
              submitting: false,
            };

            const avatarGradient =
              AVS[Math.abs(feed.author.user_id) % AVS.length];

            return (
              <Animated.View
                entering={FadeInDown.delay(50 + index * 100).duration(380)}
                style={styles.card}
              >
                <View style={styles.cardHead}>
                  <Pressable
                    style={styles.authorBtn}
                    onPress={() =>
                      navigation.navigate('UserDetail', {
                        userId: feed.author.user_id,
                        user: {
                          user_id: feed.author.user_id,
                          name: feed.author.nickname,
                          grad: avatarGradient,
                        },
                      })
                    }
                  >
                    <Avatar
                      grad={avatarGradient}
                      imageUrl={feed.author.profile_image_url}
                    />

                    <Text style={styles.userName}>
                      {feed.author.nickname}
                    </Text>
                  </Pressable>

                  <Pressable
                    onPress={() => setMorePostId(feed.post_id)}
                    hitSlop={6}
                    style={styles.dotsBtn}
                  >
                    <DotsIcon />
                  </Pressable>
                </View>

                <CommunityMedia feed={feed} />

                <View style={styles.cardBody}>
                  <View style={styles.actionRow}>
                    <View style={styles.likeGroup}>
                      <View
                        pointerEvents={
                          likeState.submitting ? 'none' : 'auto'
                        }
                        style={
                          likeState.submitting
                            ? styles.disabledAction
                            : undefined
                        }
                      >
                        <HeartButton
                          liked={likeState.liked}
                          onToggle={() =>
                            handleToggleLike(feed.post_id)
                          }
                        />
                      </View>

                      <Pressable
                        onPress={() =>
                          openLikeUsers(feed.post_id)
                        }
                        hitSlop={6}
                      >
                        <Text style={styles.likeCount}>
                          {likeState.count}개
                        </Text>
                      </Pressable>
                    </View>

                    <Pressable
                      style={styles.commentGroup}
                      onPress={() =>
                        openComments(feed.post_id)
                      }
                      hitSlop={6}
                    >
                      <CommentIcon />

                      <Text style={styles.commentCount}>
                        {feed.comment_count}
                      </Text>
                    </Pressable>
                  </View>

                  <Text style={styles.caption}>
                    <Text style={styles.captionUser}>
                      {feed.author.nickname}
                    </Text>

                    {feed.caption
                      ? ` ${feed.caption}`
                      : ''}
                  </Text>

                  <Pressable
                    onPress={() =>
                      openComments(feed.post_id)
                    }
                    hitSlop={4}
                  >
                    <Text style={styles.viewComments}>
                      댓글 {feed.comment_count}개 모두 보기
                    </Text>
                  </Pressable>
                </View>
              </Animated.View>
            );
          }}
        />
      )}

      <BottomSheet
        visible={commentsPostId !== null}
        onClose={closeComments}
        contentStyle={styles.communityListSheet}
      >
        <SheetTitle
          text={`댓글 ${
            commentsPostId !== null
              ? feeds.find((feed) => feed.post_id === commentsPostId)
                  ?.comment_count ?? comments.length
              : 0
          }개`}
        />

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
          <FlatList
            data={comments}
            keyExtractor={(comment) => String(comment.comment_id)}
            style={styles.commentScroll}
            contentContainerStyle={styles.sheetList}
            keyboardShouldPersistTaps="handled"
            showsVerticalScrollIndicator={false}
            onEndReached={loadMoreComments}
            onEndReachedThreshold={0.25}
            ListFooterComponent={
              commentsLoadingMore ? (
                <ActivityIndicator style={styles.sheetFooterLoading} />
              ) : null
            }
            renderItem={({ item: comment }) => {
              const commentGradient =
                AVS[Math.abs(comment.author.user_id) % AVS.length];

              return (
                <Pressable
                  style={styles.commentRow}
                  onPress={() => {
                    closeComments();

                    navigation.navigate('UserDetail', {
                      userId: comment.author.user_id,
                      user: {
                        user_id: comment.author.user_id,
                        name: comment.author.nickname,
                        grad: commentGradient,
                      },
                    });
                  }}
                >
                  <Avatar
                    grad={commentGradient}
                    imageUrl={comment.author.profile_image_url}
                  />

                  <View style={styles.commentTextWrap}>
                    <Text style={styles.rowUser}>
                      {comment.author.nickname}
                    </Text>
                    <Text style={styles.commentText}>
                      {comment.content}
                    </Text>
                  </View>
                </Pressable>
              );
            }}
          />
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
        contentStyle={styles.communityListSheet}
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
          <FlatList
            data={likeUsers}
            keyExtractor={(user) => String(user.user_id)}
            style={styles.likerScroll}
            contentContainerStyle={styles.sheetList}
            showsVerticalScrollIndicator={false}
            onEndReached={loadMoreLikeUsers}
            onEndReachedThreshold={0.25}
            ListFooterComponent={
              likeUsersLoadingMore ? (
                <ActivityIndicator style={styles.sheetFooterLoading} />
              ) : null
            }
            renderItem={({ item: user }) => {
              const userGradient = AVS[Math.abs(user.user_id) % AVS.length];

              return (
                <Pressable
                  style={styles.likerRow}
                  onPress={() => {
                    closeLikeUsers();

                    navigation.navigate('UserDetail', {
                      userId: user.user_id,
                      user: {
                        user_id: user.user_id,
                        name: user.nickname,
                        grad: userGradient,
                      },
                    });
                  }}
                >
                  <Avatar
                    grad={userGradient}
                    imageUrl={user.profile_image_url}
                  />
                  <Text style={styles.likerUser}>{user.nickname}</Text>
                </Pressable>
              );
            }}
          />
        )}

        <SheetCloseChevron onPress={closeLikeUsers} />
      </BottomSheet>

      <BottomSheet
        visible={morePostId !== null}
        onClose={() => setMorePostId(null)}
      >
        {isMyPostsView ? (
          <>
            <Pressable
              style={[styles.moreRow, styles.moreDivider]}
              onPress={() => {
                const post = feeds.find(
                  (feed) => feed.post_id === morePostId,
                );

                setMorePostId(null);

                if (post) {
                  navigation.navigate('NewPost', { post });
                }
              }}
            >
              <EditIcon />
              <Text style={styles.moreText}>수정하기</Text>
            </Pressable>

            <Pressable
              style={styles.moreRow}
              onPress={() => {
                const postId = morePostId;
                setMorePostId(null);
                setDeletePostId(postId);
              }}
            >
              <TrashIcon />
              <Text style={[styles.moreText, styles.moreDanger]}>
                삭제하기
              </Text>
            </Pressable>
          </>
        ) : (
          <>
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
              <Text style={[styles.moreText, styles.moreDanger]}>
                신고하기
              </Text>
            </Pressable>
          </>
        )}
      </BottomSheet>

      <DeletePostPopup
        visible={deletePostId !== null}
        submitting={deletingPostId !== null}
        onClose={() => {
          if (deletingPostId === null) {
            setDeletePostId(null);
          }
        }}
        onConfirm={deletePost}
      />

      <ReportPopup
        visible={reportPostId !== null}
        onClose={() => setReportPostId(null)}
        onSubmit={submitReport}
      />
    </View>
  );
}

function DeletePostPopup({
  visible,
  submitting,
  onClose,
  onConfirm,
}: {
  visible: boolean;
  submitting: boolean;
  onClose: () => void;
  onConfirm: () => Promise<void>;
}) {
  const { width } = useWindowDimensions();

  return (
    <GamePopup
      visible={visible}
      onClose={onClose}
      dismissOnBackdrop={!submitting}
      width={Math.min(345, width - 48)}
      style={dp.frame}
    >
      <Text style={dp.title}>게시물을 삭제할까요?</Text>
      <Text style={dp.description}>
        삭제한 게시물은 다시 복구할 수 없습니다.
      </Text>

      <View style={dp.buttonRow}>
        <Pressable
          disabled={submitting}
          onPress={onConfirm}
          style={[dp.button, dp.deleteButton]}
        >
          {submitting ? (
            <ActivityIndicator size="small" color={colors.white} />
          ) : (
            <Text style={dp.deleteText}>삭제하기</Text>
          )}
        </Pressable>

        <Pressable
          disabled={submitting}
          onPress={onClose}
          style={[dp.button, dp.cancelButton]}
        >
          <Text style={dp.cancelText}>취소</Text>
        </Pressable>
      </View>
    </GamePopup>
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
  communityListSheet: {
    height: '50%',
  },
  sheetList: {
    paddingTop: 4,
    paddingBottom: 8,
  },
  sheetLoading: {
    flex: 1,
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
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  sheetEmptyText: {
    fontSize: 13,
    color: colors.textSecondary,
    fontFamily: fonts.bodyR,
  },
  commentScroll: {
    flex: 1,
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
    flex: 1,
  },
  sheetFooterLoading: {
    marginVertical: 14,
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

const dp = StyleSheet.create({
  frame: {
    borderColor: colors.gold,
  },
  title: {
    fontFamily: fonts.pixel,
    fontSize: 17,
    color: gamePopup.cream,
    textAlign: 'center',
  },
  description: {
    marginTop: 12,
    fontSize: 13,
    lineHeight: 20,
    color: '#B9C9BD',
    textAlign: 'center',
    fontFamily: fonts.bodyR,
  },
  buttonRow: {
    alignSelf: 'stretch',
    flexDirection: 'row',
    gap: 10,
    marginTop: 22,
  },
  button: {
    flex: 1,
    height: 44,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
  },
  deleteButton: {
    backgroundColor: colors.danger,
  },
  deleteText: {
    color: colors.white,
    fontSize: 14,
    fontWeight: '700',
    fontFamily: fonts.bodyB,
  },
  cancelButton: {
    borderWidth: 1,
    borderColor: 'rgba(242,215,131,0.5)',
  },
  cancelText: {
    color: gamePopup.cream,
    fontSize: 14,
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