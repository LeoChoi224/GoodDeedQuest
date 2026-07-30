/**
 * 지도 SVG(korea_drilldown.json)의 시/도 표시명 → 백엔드 city_id(SGIS 시도코드) 매핑.
 * 강원/전북은 2023년 개명(강원도→강원특별자치도, 전라북도→전북특별자치도)으로
 * DB 시드(city_seed.csv)엔 새 이름이 들어있지만, 지도 SVG는 옛 이름을 쓰고 있어 별도 매핑함.
 */
export const PROVINCE_NAME_TO_CITY_ID: Record<string, number> = {
  서울특별시: 11,
  부산광역시: 21,
  대구광역시: 22,
  인천광역시: 23,
  광주광역시: 24,
  대전광역시: 25,
  울산광역시: 26,
  세종특별자치시: 29,
  경기도: 31,
  강원도: 32,
  충청북도: 33,
  충청남도: 34,
  전라북도: 35,
  전라남도: 36,
  경상북도: 37,
  경상남도: 38,
  제주특별자치도: 39,
};

const CITY_ID_TO_PROVINCE_NAME: Record<number, string> = Object.fromEntries(
  Object.entries(PROVINCE_NAME_TO_CITY_ID).map(([name, id]) => [id, name])
);

export function resolveCityId(provinceName: string): number | null {
  return PROVINCE_NAME_TO_CITY_ID[provinceName] ?? null;
}

/** national-ranking이 주는 city_id → 지도 SVG가 쓰는 표시명(province param)으로 역변환. */
export function resolveProvinceName(cityId: number): string | null {
  return CITY_ID_TO_PROVINCE_NAME[cityId] ?? null;
}