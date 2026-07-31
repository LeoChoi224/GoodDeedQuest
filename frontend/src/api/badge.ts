import api from './client';

export type Badge = {
  badge_id: number;
  name: string;
  description: string;
  icon_url: string;
  badge_category: string;
  is_owned: boolean;
};

export type MyBadge = {
  badge_id: number;
  name: string;
  description: string;
  icon_url: string;
  badge_category: string;
  is_equipped: boolean;
  awarded_at: string;
};

export async function getAllBadges(): Promise<Badge[]> {
  const response = await api.get('/badges');
  return response.data.data ?? [];
}

export async function getMyBadges(): Promise<MyBadge[]> {
  const response = await api.get('/badges/my');
  return response.data.data ?? [];
}

export async function equipBadge(badgeId: number): Promise<MyBadge> {
  const response = await api.patch(`/badges/${badgeId}/equip`);
  return response.data.data;
}

export async function unequipBadge(badgeId: number): Promise<MyBadge> {
  const response = await api.patch(`/badges/${badgeId}/unequip`);
  return response.data.data;
}
