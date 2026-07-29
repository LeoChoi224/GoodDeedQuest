import api from './client';

// AI 서버가 Vision → RAG → LLM Story 체인을 거쳐야 해서 백엔드 자체 타임아웃(30초)보다
// 여유 있게 잡는다. 클라이언트가 먼저 포기하면 서버는 처리 중인데 화면엔 실패로 뜬다.
const SCRIPT_TIMEOUT = 60000;

export type ShortFormStatus = 'PENDING' | 'GENERATING' | 'COMPLETED' | 'FAILED';

export type CaptionItem = {
  media_s3_key: string;
  order: number;
  caption: string;
};

export type ShortForm = {
  shorts_id: number;
  user_id: number;
  bgm_id: number;
  title: string;
  ai_generated_captions: CaptionItem[] | null;
  status: ShortFormStatus;
  video_url: string | null;
  created_at: string;
  updated_at: string;
};

export type ScriptGenerateResult = {
  shorts_id: number;
  status: ShortFormStatus;
  title: string;
  captions: CaptionItem[];
};

export type BackgroundMusic = {
  bgm_id: number;
  title: string;
  mood_tag: string | null;
  source_info: string | null;
  preview_url: string | null;
};

export type BackgroundMusicList = {
  items: BackgroundMusic[];
  total: number;
};

/**
 * 숏폼 생성 시작. shorts_id는 autoincrement PK라 생성 응답으로만 알 수 있고,
 * 이후 대본 생성(/script)·최종 생성(/generate) 호출에 필요하다.
 * bgm_id를 생략(자동 생성 경로)하면 백엔드가 RAG 기반으로 자동 매칭한다.
 */
export async function createShortform(
  title: string,
  mediaKeys: string[],
  bgmId?: number,
): Promise<ShortForm> {
  const response = await api.post<ShortForm>('/shortforms', {
    title,
    selected_media_s3_keys: mediaKeys,
    bgm_id: bgmId ?? null,
  });
  return response.data;
}

/** AI 대본 생성 팝업 - '생성하기' 클릭 시 호출. 결과는 DB에 저장되지 않는다. */
export async function generateScript(
  shortsId: number,
  mediaKeys: string[],
  questTitle: string,
): Promise<ScriptGenerateResult> {
  const response = await api.post<ScriptGenerateResult>(
    `/shortforms/${shortsId}/script`,
    {
      selected_media_s3_keys: mediaKeys,
      quest_title: questTitle,
    },
    { timeout: SCRIPT_TIMEOUT },
  );
  return response.data;
}

/**
 * 사용자가 팝업에서 직접 수정한 제목/캡션을 검증한다.
 * stateless 엔드포인트라 DB에는 아무것도 저장되지 않는다 - 개수/길이 제약 위반 시 400.
 */
export async function updateScript(
  shortsId: number,
  title: string,
  captions: CaptionItem[],
): Promise<ScriptGenerateResult> {
  const response = await api.put<ScriptGenerateResult>(
    `/shortforms/${shortsId}/script`,
    { title, captions },
  );
  return response.data;
}

export async function getBackgroundMusicList(
  moodTag?: string,
): Promise<BackgroundMusicList> {
  const response = await api.get<BackgroundMusicList>('/background-music', {
    params: moodTag ? { mood_tag: moodTag } : undefined,
  });
  return response.data;
}
