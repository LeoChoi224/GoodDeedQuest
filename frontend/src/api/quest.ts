import api from './client';

export type QuestType = 'VOLUNTEER' | 'GOOD_DEED';
export type Difficulty = 'VERY_EASY' | 'EASY' | 'NORMAL' | 'HARD' | 'VERY_HARD';
export type QuestStatus = 'NOT_STARTED' | 'IN_PROGRESS' | 'COMPLETED';

export type Quest = {
  quest_id: number;
  quest_title: string;
  quest_description: string;
  quest_type: QuestType;
  quest_status: QuestStatus;
  category_code: string;
  category_name: string;
  difficulty: Difficulty;
  reward_point: number | null;
  reward_exp: number | null;
  location: string | null;
  estimated_duration: number | null;
};

const DIFFICULTY_LABEL: Record<Difficulty, string> = {
  VERY_EASY: '매우 쉬움',
  EASY: '쉬움',
  NORMAL: '보통',
  HARD: '어려움',
  VERY_HARD: '매우 어려움',
};

/** DiffChip은 한글 라벨을 받으므로 enum을 변환해서 넘긴다. */
export function difficultyLabel(difficulty: Difficulty): string {
  return DIFFICULTY_LABEL[difficulty] ?? '보통';
}

/** GOOD_DEED(개인 선행)는 동영상, VOLUNTEER(봉사)는 VMS 확인서 사진으로 인증한다. */
export function isVideoQuest(questType: QuestType): boolean {
  return questType !== 'VOLUNTEER';
}

export async function getQuests(): Promise<Quest[]> {
  const response = await api.get('/quests');
  return response.data.data ?? [];
}

export async function getQuest(questId: number): Promise<Quest> {
  const response = await api.get(`/quests/${questId}`);
  return response.data.data;
}
