import axios from 'axios';

import api from '../../api/client';

/**
 * 관리자 API 연동 파일
 *
 * - 공통 Axios 인스턴스(src/api/client.ts)를 재사용합니다.
 * - 로그인 토큰은 client.ts의 요청 인터셉터가 SecureStore에서 읽어
 *   Authorization 헤더에 자동으로 추가합니다.
 * - 이 파일에서는 BASE_URL, 토큰, fetch를 따로 관리하지 않습니다.
 */

export type UserRole = 'USER' | 'ADMIN' | string;
export type ReportStatus =
  | 'PENDING'
  | 'APPROVED'
  | 'REJECTED'
  | 'EXPIRED';

export interface AdminDashboardSummary {
  total_user_count: number;
  active_user_count: number;
  inactive_user_count: number;
  today_access_user_count: number;
  pending_report_count: number;
}

export interface AdminDashboardAlert {
  type: string;
  level: string;
  title: string;
  message: string;
  count: number;
}

export interface AdminActivityTrend {
  access_date: string;
  user_count: number;
}

export interface AdminUser {
  user_id: number;
  email: string;
  nickname: string;
  profile_image_url: string | null;
  is_active: boolean;
  role: UserRole;
  trust_score: number;
  current_level: number;
  created_at: string;
  updated_at: string;
}

export interface AdminUserDetail extends AdminUser {
  region_id: number | null;
  provider: string | null;
  birthday: string | null;
  category: unknown[] | null;
  active_time: unknown[] | null;
  point_balance: number;
  current_xp: number;
  daily_streak: number;
}

export interface AdminReport {
  report_id: number;
  reporter_id: number;
  reviewed_by: number | null;
  post_id: number | null;
  reason: string;
  status: ReportStatus;
  created_at: string;
  reviewed_at: string | null;
  updated_at: string;
}

export interface AdminReportDetail extends AdminReport {
  post_media_url: string | null;
}

export type AdminUserSort =
  | 'newest'
  | 'oldest'
  | 'level'
  | 'nickname'
  | 'trust';

export interface AdminUserListParams {
  nickname?: string;
  is_active?: boolean;
  skip?: number;
  limit?: number;
  sort_by?: AdminUserSort;
}

export interface AdminReportListParams {
  status?: ReportStatus;
  skip?: number;
  limit?: number;
  newest_first?: boolean;
}

/**
 * Backend 공통 응답이 { data: ... } 구조인 경우 실제 데이터를 꺼냅니다.
 * 응답 자체가 데이터인 경우에는 그대로 반환합니다.
 */
function unwrapResponse<T>(payload: unknown): T {
  if (payload && typeof payload === 'object' && 'data' in payload) {
    return (payload as { data: T }).data;
  }

  return payload as T;
}

/**
 * 관리자 API 함수 모음
 *
 * client.ts의 baseURL이 /api/v1까지 포함하므로,
 * 여기서는 /admin 이하 경로만 작성합니다.
 */
export const adminApi = {
  // 관리자 대시보드 오늘의 요약을 조회합니다.
  async getDashboardSummary(): Promise<AdminDashboardSummary> {
    const response = await api.get('/admin/dashboard/summary');
    return unwrapResponse<AdminDashboardSummary>(response.data);
  },

  // 관리자 대시보드 주요 알림을 조회합니다.
  async getDashboardAlerts(): Promise<AdminDashboardAlert[]> {
    const response = await api.get('/admin/dashboard/alerts');
    return unwrapResponse<AdminDashboardAlert[]>(response.data);
  },

  // 최근 7일 일별 접속 사용자 수를 조회합니다.
  async getActivityTrend(): Promise<AdminActivityTrend[]> {
    const response = await api.get('/admin/dashboard/activity-trend');
    return unwrapResponse<AdminActivityTrend[]>(response.data);
  },

  // 조건에 맞는 사용자 목록을 조회합니다.
  async getUsers(
    params: AdminUserListParams = {},
  ): Promise<AdminUser[]> {
    const response = await api.get('/admin/users', { params });
    return unwrapResponse<AdminUser[]>(response.data);
  },

  // 특정 사용자 상세 정보를 조회합니다.
  async getUser(userId: number): Promise<AdminUserDetail> {
    const response = await api.get(`/admin/users/${userId}`);
    return unwrapResponse<AdminUserDetail>(response.data);
  },

  // 특정 사용자의 활성 상태를 변경합니다.
  async updateUserActiveStatus(
    userId: number,
    isActive: boolean,
  ): Promise<AdminUserDetail> {
    const response = await api.patch(
      `/admin/users/${userId}/active-status`,
      { is_active: isActive },
    );

    return unwrapResponse<AdminUserDetail>(response.data);
  },

  // 조건에 맞는 신고 목록을 조회합니다.
  async getReports(
    params: AdminReportListParams = {},
  ): Promise<AdminReport[]> {
    const response = await api.get('/admin/reports', { params });
    return unwrapResponse<AdminReport[]>(response.data);
  },

  // 특정 신고 상세 정보를 조회합니다.
  async getReport(reportId: number): Promise<AdminReportDetail> {
    const response = await api.get(`/admin/reports/${reportId}`);

    return unwrapResponse<AdminReportDetail>(response.data);
  },

  // 처리 대기 중인 신고를 반려합니다.
  async rejectReport(reportId: number): Promise<AdminReport> {
    const response = await api.patch(
      `/admin/reports/${reportId}/reject`,
    );

    return unwrapResponse<AdminReport>(response.data);
  },

  // 신고를 승인하고 해당 게시글을 비활성화합니다.
  async approvePostDeletion(
    reportId: number,
  ): Promise<AdminReport> {
    const response = await api.patch(
      `/admin/reports/${reportId}/approve/post-delete`,
    );

    return unwrapResponse<AdminReport>(response.data);
  },

  // 신고를 승인하고 신고 대상 사용자를 비활성화합니다.
  async approveUserDeactivation(
    reportId: number,
  ): Promise<AdminReport> {
    const response = await api.patch(
      `/admin/reports/${reportId}/approve/user-deactivate`,
    );

    return unwrapResponse<AdminReport>(response.data);
  },
};

/**
 * 화면에 표시할 API 오류 메시지를 반환합니다.
 */
export function getAdminErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;

    if (typeof detail === 'string' && detail.trim()) {
      return detail;
    }

    if (error.code === 'ECONNABORTED') {
      return '서버 응답 시간이 초과되었습니다.';
    }

    if (!error.response) {
      return '서버에 연결할 수 없습니다. 백엔드 실행 상태와 네트워크를 확인해 주세요.';
    }

    return `요청 처리에 실패했습니다. (${error.response.status})`;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return '알 수 없는 오류가 발생했습니다.';
}