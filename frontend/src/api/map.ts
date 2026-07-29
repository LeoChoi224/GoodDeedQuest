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