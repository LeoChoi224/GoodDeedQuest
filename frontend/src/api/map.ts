import api from './client';

export type CityRankingEntry = {
  rank: number;
  region_id: number;
  region_name: string;
  score: number;
};

export type CityRankingResponse = {
  city_id: number;
  competition_id: number;
  ranking: CityRankingEntry[];
};

/** 시군구 랭킹 조회 (SiDoMapScreen). 대항전이 없으면 success:false로 응답이 와서 예외로 변환. */
export async function getCityRanking(cityId: number): Promise<CityRankingResponse> {
  const response = await api.get(`/map/city-ranking/${cityId}`);
  if (!response.data.success) {
    throw new Error(response.data.message ?? '랭킹을 불러오지 못했습니다.');
  }
  return response.data.data;
}

export type NationalRankingEntry = {
  rank: number;
  city_id: number;
  city_name: string;
  total_score: number;
};

export type NationalRankingResponse = {
  competition_id: number;
  ranking: NationalRankingEntry[];
};

/** 시/도별 랭킹 조회 (MainMapScreen). 대항전이 없으면 success:false로 응답이 와서 예외로 변환. */
export async function getNationalRanking(): Promise<NationalRankingResponse> {
  const response = await api.get('/map/national-ranking');
  if (!response.data.success) {
    throw new Error(response.data.message ?? '랭킹을 불러오지 못했습니다.');
  }
  return response.data.data;
}

export type PersonalRankingEntry = {
  rank: number;
  user_id: number;
  nickname: string;
  score: number;
  is_me: boolean;
};

export type RecommendedFacility = {
  center_id: number;
  vol_name: string;
  ai_category: string;
  region_id: number;
  region_name: string;
};

export type RegionRankingResponse = {
  region_id: number;
  region_name: string;
  competition_id: number;
  personal_ranking: PersonalRankingEntry[];
  lacking_category: string;
  lacking_category_comment: string;
  recommended_facilities: RecommendedFacility[];
};

/** 시군구 상세 랭킹 조회 (RegionDetailsScreen) - 개인 랭킹 + AI 부족봉사 판단 + 추천 시설. */
export async function getRegionRanking(regionId: number): Promise<RegionRankingResponse> {
  const response = await api.get(`/map/region-ranking/${regionId}`);
  if (!response.data.success) {
    throw new Error(response.data.message ?? '랭킹을 불러오지 못했습니다.');
  }
  return response.data.data;
}

export type VolunteerCenter = {
  center_id: number;
  region_id: number;
  vol_name: string | null;
  vol_address: string | null;
  vol_title: string | null;
  target: string | null;
  vms_url: string | null;
  vol_qual: string | null;
  vol_act: string | null;
  vol_date: string | null;
  latitude: number | null;
  longitude: number | null;
  updated_at: string;
};

/** 내 주변 봉사센터 조회 (VolSearchScreen). VMS 크롤링 데이터라 "봉사" 전용, "선행" 데이터 소스는 아직 없음. */
export async function getNearbyVolunteerCenters(lat: number, lng: number, radiusKm = 3): Promise<VolunteerCenter[]> {
  const response = await api.get('/map/volunteer-centers', { params: { lat, lng, radius_km: radiusKm } });
  return response.data.data ?? [];
}

export type RegionOption = {
  region_id: number;
  region_name: string;
};

/** 시/도 선택 시 하위 시군구 목록 조회 (TeamSelectPopup). */
export async function getRegionsByCity(cityId: number): Promise<RegionOption[]> {
  const response = await api.get(`/map/cities/${cityId}/regions`);
  return response.data.data ?? [];
}

export type MapMainResponse = {
  has_region: boolean;
  region: { region_id: number; region_name: string; city_id: number } | null;
};

/** 지도메인 진입 시 참여지역 설정 여부 확인 (MainMapScreen). */
export async function getMapMain(): Promise<MapMainResponse> {
  const response = await api.get('/map/main');
  return response.data.data;
}

export type TeamSelectResult = {
  region_id: number;
  region_name: string;
  competition_id: number;
};

/** 대항전 참여 지역 등록/변경. 최초 선택은 언제든, 변경은 정산 중(SETTLING)에만 가능. */
export async function selectTeamRegion(regionId: number): Promise<TeamSelectResult> {
  const response = await api.post('/map/team-select', { region_id: regionId });
  if (!response.data.success) {
    throw new Error(response.data.message ?? '참여 지역을 설정하지 못했습니다.');
  }
  return response.data.data;
}