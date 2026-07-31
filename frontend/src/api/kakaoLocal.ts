/**
 * 카카오 로컬 검색(키워드) REST API - 자동완성 드롭다운용.
 * KakaoMapView(WebView, JS SDK)의 keywordSearch는 첫 번째 결과 하나만 가져오는 구조라
 * "엔터 치면 무조건 1등 결과로 이동" 문제가 있었음. 대신 이 REST API로 여러 개 후보를
 * 직접 받아서 리스트로 보여주고, 사용자가 그중 하나를 직접 선택하게 함.
 * REST API 키는 카카오 로그인 때 쓰던 것과 같은 앱의 키 재사용(도메인 화이트리스트 불필요,
 * JS SDK 키와는 별개 값).
 */
const KAKAO_REST_KEY = process.env.EXPO_PUBLIC_KAKAO_REST_KEY ?? '';

export type KakaoPlace = {
  id: string;
  placeName: string;
  addressName: string;
  roadAddressName: string;
  lat: number;
  lng: number;
};

/** 키워드로 장소 후보 목록 검색 (자동완성 드롭다운용, 기본 8개). */
export async function searchKakaoPlaces(keyword: string, size = 8): Promise<KakaoPlace[]> {
  const q = keyword.trim();
  if (!KAKAO_REST_KEY || !q) return [];

  const url = `https://dapi.kakao.com/v2/local/search/keyword.json?query=${encodeURIComponent(q)}&size=${size}`;
  const response = await fetch(url, {
    headers: { Authorization: `KakaoAK ${KAKAO_REST_KEY}` },
  });

  if (!response.ok) {
    throw new Error(`카카오 장소 검색 실패 (${response.status})`);
  }

  const json = await response.json();
  const docs: any[] = json?.documents ?? [];

  return docs.map((d) => ({
    id: String(d.id),
    placeName: d.place_name,
    addressName: d.address_name,
    roadAddressName: d.road_address_name,
    lat: parseFloat(d.y),
    lng: parseFloat(d.x),
  }));
}