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
}

export async function submitVerification(questId: number, s3Key: string): Promise<SubmitResult> {
  const response = await api.post('/quest-verification/submit', {
    quest_id: questId,
    s3_key: s3Key
  });
  return response.data
}

