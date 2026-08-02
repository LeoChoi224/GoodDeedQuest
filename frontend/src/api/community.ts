import api from './client';

export type CommunityAuthor = {
  user_id: number;
  nickname: string;
  profile_image_url: string | null;
};

export type CommunityComment = {
  comment_id: number;
  post_id: number;
  content: string;
  created_at: string;
  updated_at: string;
  author: CommunityAuthor;
};

export type CommunityFeedItem = {
  post_id: number;
  submission_id: number;
  media_url: string;
  media_type: 'PHOTO' | 'VIDEO';
  caption: string | null;
  created_at: string;
  updated_at: string;
  author: CommunityAuthor;
  like_count: number;
  comment_count: number;
  is_liked: boolean;
  comment_previews: CommunityComment[];
};

export type RecentQuestSubmission = {
  submission_id: number;
  quest_id: number;
  media_url: string | null;
  media_type: 'PHOTO' | 'VIDEO' | null;
  submitted_at: string;
};

export type CommunityPostCreateRequest = {
  submission_id: number;
  caption?: string | null;
};

export type CommunityPostUpdateRequest = {
  caption: string | null;
};

export type CommunityUserProfile = {
  nickname: string;
  title: string;
  current_level: number;
  daily_streak: number;
  profile_image_url: string | null;
  equipped_border_image_url: string | null;
};

export type CommunityUserQuestAchievement = {
  submission_id: number;
  quest_id: number;
  title: string;
  description: string;
  category_code: string;
  completed_at: string;
  reward_point: number | null;
  reward_exp: number | null;
};

/**
 * 로그인한 사용자가 작성한 게시글의 본문을 수정합니다.
 */
export async function updateCommunityPost(
  postId: number,
  request: CommunityPostUpdateRequest,
): Promise<CommunityPost> {
  const response = await api.patch<CommunityPost>(
    `/community/posts/${postId}`,
    request,
  );

  return response.data;
}

/**
 * 로그인한 사용자가 작성한 게시글을 삭제합니다.
 */
export async function deleteCommunityPost(postId: number): Promise<void> {
  await api.delete(`/community/posts/${postId}`);
}

export type CommunityPost = {
  post_id: number;
  user_id: number;
  submission_id: number;
  media_url: string;
  media_type: 'PHOTO' | 'VIDEO';
  caption: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

/**
 * 로그인한 사용자의 기본 커뮤니티 피드를 최신순으로 조회합니다.
 */
export async function getCommunityFeed(
  skip = 0,
  limit = 20,
): Promise<CommunityFeedItem[]> {
  const response = await api.get<CommunityFeedItem[]>('/community/posts', {
    params: {
      skip,
      limit,
    },
  });

  return response.data;
}

/**
 * 로그인한 사용자의 관심 정보와 게시글 점수를 반영한 개인화 피드를 조회합니다.
 */
export async function getRecommendedCommunityFeed(
  skip = 0,
  limit = 20,
): Promise<CommunityFeedItem[]> {
  const response = await api.get<CommunityFeedItem[]>(
    '/community/posts/recommended',
    {
      params: {
        skip,
        limit,
      },
    },
  );

  return response.data;
}

/**
 * 로그인한 사용자가 작성한 커뮤니티 게시글만 최신순으로 조회합니다.
 */
export async function getMyCommunityPosts(
  skip = 0,
  limit = 20,
): Promise<CommunityFeedItem[]> {
  const response = await api.get<CommunityFeedItem[]>(
    '/community/posts/mine',
    {
      params: {
        skip,
        limit,
      },
    },
  );

  return response.data;
}

export async function getCommunityUserProfile(
  userId: number,
): Promise<CommunityUserProfile> {
  const response = await api.get<CommunityUserProfile>(
    `/community/users/${userId}/profile`,
  );

  return response.data;
}

export async function getCommunityUserQuestAchievements(
  userId: number,
): Promise<CommunityUserQuestAchievement[]> {
  const response = await api.get<CommunityUserQuestAchievement[]>(
    `/community/users/${userId}/quests/achievements`,
  );

  return response.data;
}

/**
 * 커뮤니티 게시글 작성에 사용할 최근 승인 퀘스트 인증 목록을 조회합니다.
 */
export async function getRecentQuestSubmissions(
  skip = 0,
  limit = 20,
): Promise<RecentQuestSubmission[]> {
  const response = await api.get<RecentQuestSubmission[]>(
    '/community/quest-submissions/recent',
    {
      params: {
        skip,
        limit,
      },
    },
  );

  return response.data;
}

/**
 * 선택한 승인 퀘스트 인증을 이용해 커뮤니티 게시글을 생성합니다.
 */
export async function createCommunityPost(
  request: CommunityPostCreateRequest,
): Promise<CommunityPost> {
  const response = await api.post<CommunityPost>(
    '/community/posts',
    request,
  );

  return response.data;
}

export type PostLikeToggleResult = {
  post_id: number;
  is_liked: boolean;
  like_count: number;
};

export type PostLikeUser = {
  user_id: number;
  nickname: string;
  profile_image_url: string | null;
};

export type FeedHiddenPreference = {
  hidden_id: number;
  user_id: number;
  post_id: number;
  created_at: string;
  updated_at: string;
};

export type CommunityReportCreateRequest = {
  reason: string;
};

export type CommunityReport = {
  report_id: number;
  reporter_id: number;
  post_id: number | null;
  reason: string;
  status: string;
  created_at: string;
};

/**
 * 게시글 좋아요를 토글합니다.
 */
export async function toggleCommunityPostLike(
  postId: number,
): Promise<PostLikeToggleResult> {
  const response = await api.post<PostLikeToggleResult>(
    `/community/posts/${postId}/likes/toggle`,
  );

  return response.data;
}

/**
 * 게시글을 좋아요 한 사용자 목록을 조회합니다.
 */
export async function getCommunityPostLikeUsers(
  postId: number,
  skip = 0,
  limit = 100,
): Promise<PostLikeUser[]> {
  const response = await api.get<PostLikeUser[]>(
    `/community/posts/${postId}/likes`,
    {
      params: {
        skip,
        limit,
      },
    },
  );

  return response.data;
}

/**
 * 게시글 댓글 전체 목록을 오래된 순서부터 조회합니다.
 */
export async function getCommunityPostComments(
  postId: number,
  skip = 0,
  limit = 100,
): Promise<CommunityComment[]> {
  const response = await api.get<CommunityComment[]>(
    `/community/posts/${postId}/comments`,
    {
      params: {
        skip,
        limit,
      },
    },
  );

  return response.data;
}

/**
 * 게시글에 새 댓글을 작성합니다.
 */
export async function createCommunityPostComment(
  postId: number,
  content: string,
): Promise<CommunityComment> {
  const response = await api.post<CommunityComment>(
    `/community/posts/${postId}/comments`,
    {
      content,
    },
  );

  return response.data;
}

/**
 * 게시글을 관심 없음으로 기록합니다.
 */
export async function markCommunityPostNotInterested(
  postId: number,
): Promise<FeedHiddenPreference> {
  const response = await api.post<FeedHiddenPreference>(
    `/community/posts/${postId}/not-interested`,
  );

  return response.data;
}

/**
 * 게시글 신고를 접수합니다.
 */
export async function reportCommunityPost(
  postId: number,
  request: CommunityReportCreateRequest,
): Promise<CommunityReport> {
  const response = await api.post<CommunityReport>(
    `/community/posts/${postId}/reports`,
    request,
  );

  return response.data;
}