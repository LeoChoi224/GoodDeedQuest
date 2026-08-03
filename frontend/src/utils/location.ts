import * as Location from 'expo-location';

/**
 * 현재 위치를 얻는다. 권한을 거부하거나 실패하면 null을 돌려준다.
 * 좌표가 없어도 추천은 돌아간다 — 백엔드가 User 테이블에 저장된 좌표로 대신 채운다.
 */
export async function getCurrentCoords(): Promise<{ latitude: number; longitude: number } | null> {
  try {
    const { status } = await Location.requestForegroundPermissionsAsync();
    if (status !== 'granted') return null;
    // 봉사 검색 반경이 5km 단위라 높은 정확도는 필요 없다. Balanced가 더 빨리 끝난다.
    const pos = await Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.Balanced });
    return { latitude: pos.coords.latitude, longitude: pos.coords.longitude };
  } catch {
    return null;
  }
}