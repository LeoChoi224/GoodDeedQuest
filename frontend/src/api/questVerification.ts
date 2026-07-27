import api from "./client";

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
  });
  return response.data
}

/** 손글씨 코드 사진을 올려 추가 인증을 마친다. */
export async function submitChallenge(submissionId: number, s3Key: string): Promise<SubmitResult> {
  const response = await api.post('/quest-verification/challenge', {
    submission_id: submissionId,
    s3_key: s3Key,
  });
  return response.data
}
