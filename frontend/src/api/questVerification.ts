import api from "./client";

// AI 판정은 기본 10초로 모자란다. 특히 동영상은 다운로드 + 프레임 추출까지 붙는다.
// 클라이언트가 먼저 포기하면 서버는 처리를 마쳤는데 화면엔 실패로 뜬다.
const AI_TIMEOUT = 180000;

export type PresignResult = {
  upload_url: string,
  s3_key: string
}

export async function getPresignedUrl(questId: number, contentType: string): Promise<PresignResult> {
  const response = await api.post('/quest-verification/presign', {
    quest_id: questId,
    content_type: contentType
  });
  return response.data;
}

export async function uploadToS3(uploadUrl: string, localUri: string, contentType: string): Promise<void> {
  const file = await fetch(localUri);
  const blob = await file.blob();
  const result = await fetch(uploadUrl, {
    method: 'PUT',
    body: blob,
    headers: { 'Content-Type': contentType },
  });
  if (!result.ok) {
    throw new Error(`s3 업로드 실패 ${result.status}`)
  }
}

export type SubmitResult = {
  verified: boolean;
  reason: string;
  xp_gained: number;
  points_gained: number;
  // 진위가 의심스러울 때만 채워진다 — 손글씨 코드로 추가 인증을 요구
  challenge_required?: boolean;
  challenge_code?: string | null;
  submission_id?: number | null;
  // 이번 인증으로 새로 해금된 칭호(배지) 이름 목록 — 인증완료 화면 토스트 표시용
  unlocked_badges?: string[];
}

export async function uploadOne(questId: number, localUri: string, contentType = 'image/jpeg'): Promise<string> {
  const presign = await getPresignedUrl(questId, contentType);
  await uploadToS3(presign.upload_url, localUri, contentType);
  return presign.s3_key
}

export async function submitVerification(questId: number, s3Key: string, extraMediaKeys: string[] = []): Promise<SubmitResult> {
  const response = await api.post('/quest-verification/submit', {
    quest_id: questId,
    s3_key: s3Key,
    extra_media_keys: extraMediaKeys
  }, { timeout: AI_TIMEOUT });
  return response.data
}

/** 손글씨 코드 사진을 올려 추가 인증을 마친다. */
export async function submitChallenge(submissionId: number, s3Key: string): Promise<SubmitResult> {
  const response = await api.post('/quest-verification/challenge', {
    submission_id: submissionId,
    s3_key: s3Key,
  }, { timeout: AI_TIMEOUT });
  return response.data
}
