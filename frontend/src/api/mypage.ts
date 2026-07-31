import api from './client';

export type MyQuestAchievement = {
  submission_id: number; // ⭐ 수정: 같은 퀘스트를 여러 번 완료할 수 있어 리스트 key 등 식별용으로 사용
  quest_id: number;
  title: string;
  description: string;
  category_code: string;
  completed_at: string;
  reward_point: number | null;
  reward_exp: number | null;
};

export async function getMyQuestAchievements(): Promise<MyQuestAchievement[]> {
  const response = await api.get('/mypage/quests/achievements');
  return response.data.data ?? [];
}

// ⭐ 수정: 마이페이지 프로필 헤더(이름/칭호/레벨/연속접속일/프로필이미지)
export type MyProfile = {
  nickname: string;
  title: string;
  current_level: number;
  daily_streak: number;
  profile_image_url: string | null;
  equipped_border_image_url: string | null; // ⭐ 수정: 상대경로(/static/...)로 오므로 getFullImageUrl()로 변환해서 써야 함
};

export async function getMyProfile(): Promise<MyProfile> {
  const response = await api.get('/mypage/profile');
  return response.data.data;
}

type ProfileImagePresignResult = {
  upload_url: string;
  s3_key: string;
};

async function presignProfileImage(contentType: string): Promise<ProfileImagePresignResult> {
  const response = await api.post('/mypage/profile/image/presign', { content_type: contentType });
  return response.data;
}

// questVerification.ts::uploadToS3와 동일한 presigned PUT 방식
async function uploadProfileImageToS3(uploadUrl: string, localUri: string, contentType: string): Promise<void> {
  const file = await fetch(localUri);
  const blob = await file.blob();
  const result = await fetch(uploadUrl, {
    method: 'PUT',
    body: blob,
    headers: { 'Content-Type': contentType },
  });
  if (!result.ok) {
    throw new Error(`s3 업로드 실패 ${result.status}`);
  }
}

async function confirmProfileImage(s3Key: string): Promise<MyProfile> {
  const response = await api.patch('/mypage/profile/image', { s3_key: s3Key });
  return response.data.data;
}

/** 갤러리에서 고른 로컬 이미지를 presign → S3 업로드 → 확정까지 한 번에 처리한다. */
export async function uploadProfileImage(localUri: string, contentType = 'image/jpeg'): Promise<MyProfile> {
  const presign = await presignProfileImage(contentType);
  await uploadProfileImageToS3(presign.upload_url, localUri, contentType);
  return confirmProfileImage(presign.s3_key);
}
