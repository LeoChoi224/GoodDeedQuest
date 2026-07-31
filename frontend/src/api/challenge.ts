import axios from 'axios';
import api from './client';

export type TeamStatus = 'RECRUITING' | 'ACTIVE' | 'EXPIRED' | 'DISBANDED';
export type TeamInviteStatus = 'PENDING' | 'ACCEPTED' | 'REJECTED' | 'EXPIRED';
export type TeamMemberRole = 'MEMBER' | 'LEADER';
export type TeamSort = 'latest' | 'oldest' | 'name';

type APIEnvelope<T> = {
  success?: boolean;
  message?: string;
  data: T;
};

export type Team = {
  team_id: number;
  leader_id: number;
  quest_id: number;
  name: string;
  notification: string;
  region: string;
  is_public: boolean;
  max_members: number;
  status: TeamStatus;
  expires_at: string | null;
  created_at: string;
  updated_at: string;
};

export type TeamListItem = Team & { current_members: number };
export type TeamDetail = Team & { current_members: number };

export type TeamMember = {
  team_member_id: number;
  team_id: number;
  user_id: number;
  role_in_team: TeamMemberRole;
  joined_at: string;
  updated_at: string;
};

export type TeamCreateRequest = {
  quest_id: number;
  name: string;
  password?: string | null;
  notification: string;
  region: string;
  is_public: boolean;
  max_members: number;
  expires_at?: string | null;
};

export type TeamInvite = {
  invite_id: number;
  team_id: number;
  user_id: number;
  status: TeamInviteStatus;
  expires_at: string | null;
  created_at: string;
  updated_at: string;
};

export type RecommendationScore = {
  category_score: number;
  difficulty_score: number;
  active_time_score: number;
  region_score: number;
  embedding_score: number;
  daily_streak_score: number;
  user_level_score: number;
  trust_score: number;
  total_score: number;
};

export type RecommendedUser = {
  user_id: number;
  nickname: string | null;
  profile_image_url: string | null;
  region_id: number | null;
  region: string | null;
  preferred_categories: Array<number | string>;
  preferred_difficulty: string | null;
  active_time: Array<number | string>;
  current_level: number;
  daily_streak: number;
  score: RecommendationScore;
  recommendation_reason: string;
  reason_source: 'LLM' | 'FALLBACK';
  rank: number;
  trust_score: number;
};

export type TeamRecommendationResult = {
  team_id: number;
  quest_id: number;
  recommendations: RecommendedUser[];
  requested_top_k: number;
  recommendation_count: number;
  warnings: string[];
};

function unwrap<T>(payload: T | APIEnvelope<T>): T {
  if (payload && typeof payload === 'object' && 'data' in payload) {
    return (payload as APIEnvelope<T>).data;
  }
  return payload as T;
}

export function getChallengeErrorMessage(error: unknown): string {
  if (!axios.isAxiosError(error)) return '알 수 없는 오류가 발생했습니다.';
  const detail = error.response?.data?.detail;
  const message = error.response?.data?.message;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail.map((item) => item?.msg).filter(Boolean).join('\n') || '입력값을 확인해주세요.';
  }
  if (typeof message === 'string') return message;
  if (error.code == 'ECONNABORTED') {return 'AI 추천 분석 시간이 초과되었습니다. 잠시 후 다시 시도해주세요.';}
  if (!error.response) {return '서버에 연결할 수 없습니다. Backend 실행 상태를 확인해주세요.';}
  return '요청을 처리하지 못했습니다.';
}

export async function getTeams(params: {
  quest_id?: number;
  status?: TeamStatus;
  is_public?: boolean;
  region?: string;
  search?: string;
  sort_by?: TeamSort;
  page?: number;
  size?: number;
} = {}): Promise<TeamListItem[]> {
  const response = await api.get<TeamListItem[] | APIEnvelope<TeamListItem[]>>('/challenges/teams', { params });
  return unwrap(response.data);
}

export async function getMyTeams(params: { status?: TeamStatus; page?: number; size?: number } = {}): Promise<TeamListItem[]> {
  const response = await api.get<TeamListItem[] | APIEnvelope<TeamListItem[]>>('/challenges/my-teams', { params });
  return unwrap(response.data);
}

export async function getTeamDetail(teamId: number): Promise<TeamDetail> {
  const response = await api.get<TeamDetail | APIEnvelope<TeamDetail>>(`/challenges/teams/${teamId}`);
  return unwrap(response.data);
}

export async function getTeamMembers(teamId: number): Promise<TeamMember[]> {
  const response = await api.get<TeamMember[] | APIEnvelope<TeamMember[]>>(`/challenges/teams/${teamId}/members`);
  return unwrap(response.data);
}

export async function createTeam(request: TeamCreateRequest): Promise<Team> {
  const response = await api.post<Team | APIEnvelope<Team>>('/challenges/teams', request);
  return unwrap(response.data);
}

export async function joinTeam(teamId: number, password?: string): Promise<TeamMember> {
  const body = password ? { password } : undefined;
  const response = await api.post<TeamMember | APIEnvelope<TeamMember>>(`/challenges/teams/${teamId}/join`, body);
  return unwrap(response.data);
}

export async function leaveTeam(teamId: number): Promise<void> {
  await api.delete(`/challenges/teams/${teamId}/leave`);
}

export async function getTeamRecommendations(
  teamId: number,
  topK = 5,
  excludedUserIds: number[] = [],
): Promise<TeamRecommendationResult> {
  const response = await api.get<
    TeamRecommendationResult | APIEnvelope<TeamRecommendationResult>
  >(
    `/challenges/teams/${teamId}/recommendations`,
    {
      params: {
        top_k: topK,
        excluded_user_ids:
          excludedUserIds.length > 0
            ? excludedUserIds.join(',')
            : undefined,
      },
      timeout: 60000,
    },
  );

  return unwrap(response.data);
}

export async function createTeamInvite(teamId: number, userId: number): Promise<TeamInvite> {
  const response = await api.post<TeamInvite | APIEnvelope<TeamInvite>>('/challenges/invites', {
    team_id: teamId,
    user_id: userId,
  });
  return unwrap(response.data);
}

export async function getMyInvites(page = 1, size = 20): Promise<TeamInvite[]> {
  const response = await api.get<TeamInvite[] | APIEnvelope<TeamInvite[]>>('/challenges/my-invites', {
    params: { page, size },
  });
  return unwrap(response.data);
}

export async function respondTeamInvite(inviteId: number, status: 'ACCEPTED' | 'REJECTED'): Promise<TeamInvite> {
  const response = await api.patch<TeamInvite | APIEnvelope<TeamInvite>>(`/challenges/invites/${inviteId}`, { status });
  return unwrap(response.data);
}
