import React, { forwardRef, useImperativeHandle, useMemo, useRef } from 'react';
import { StyleSheet, ViewStyle } from 'react-native';
import { WebView, WebViewMessageEvent } from 'react-native-webview';

const KAKAO_JS_KEY = process.env.EXPO_PUBLIC_KAKAO_JS_KEY ?? '';

// 봉사센터 마커 이미지 (frontend/assets/icons/vol_cen_pinmaker.png - 배경 투명 처리 + 44x66 리사이즈 후 base64 인라인)
const VOL_PIN_DATA_URI =
  'data:image/png;base64,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';

export type MapMarker = {
  id: string;
  lat: number;
  lng: number;
};

export type KakaoMapViewHandle = {
  searchPlace: (keyword: string) => void;
  /** 지도를 특정 좌표로 부드럽게 이동 (리스트 항목 탭 등에서 마커 위치로 되돌아갈 때 사용) */
  panTo: (lat: number, lng: number) => void;
};

type SearchResult = { lat: number; lng: number; name: string } | { error: true };

type Props = {
  latitude: number;
  longitude: number;
  myLocation?: { lat: number; lng: number } | null;
  /** true일 때만 지도 중심에 파란 검색 핀을 그림 (검색 안 하고 내 위치 그대로면 빨간 점이랑 겹쳐 보여서 굳이 안 그림) */
  showSearchMarker?: boolean;
  /** 0(또는 미지정) 이면 반경 원을 그리지 않음 - 단일 장소 상세보기처럼 반경이 의미 없는 화면용 */
  radiusKm?: number;
  markers?: MapMarker[];
  level?: number;
  onMarkerPress?: (id: string) => void;
  onSearchResult?: (result: SearchResult) => void;
  style?: ViewStyle;
};

function buildHtml(
  latitude: number,
  longitude: number,
  myLocation: { lat: number; lng: number } | null | undefined,
  showSearchMarker: boolean,
  radiusKm: number,
  markers: MapMarker[],
  level: number
) {
  // 봉사센터 - 배경 투명 처리한 PNG 핀 이미지. onclick 문자열 대신 DOM 엘리먼트에 직접 이벤트 리스너를 붙임
  // (문자열 onclick 방식은 JSON.stringify가 중첩되면서 따옴표가 깨져 클릭이 안 먹는 버그가 있었음)
  const markerScript = markers
    .map(
      (m) => `
        (function () {
          var div = document.createElement('div');
          div.style.cursor = 'pointer';
          div.innerHTML = '<img src="${VOL_PIN_DATA_URI}" width="30" height="45" style="display:block;" />';
          div.onclick = function () {
            window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'marker', id: ${JSON.stringify(m.id)} }));
          };
          new kakao.maps.CustomOverlay({
            position: new kakao.maps.LatLng(${m.lat}, ${m.lng}),
            map: map,
            yAnchor: 1,
            content: div,
          });
        })();`
    )
    .join('\n');

  // 현재 위치 - 빨간 원
  const myLocScript = myLocation
    ? `
      new kakao.maps.CustomOverlay({
        position: new kakao.maps.LatLng(${myLocation.lat}, ${myLocation.lng}),
        map: map,
        content: '<div style="width:16px;height:16px;border-radius:8px;background:#E53935;border:2px solid white;box-shadow:0 0 4px rgba(0,0,0,0.3);"></div>',
      });`
    : '';

  // 검색 중심지 - 파란 핀 마커 (물방울 모양). 검색을 실제로 했을 때만 그림
  const searchMarkerScript = showSearchMarker
    ? `
      new kakao.maps.CustomOverlay({
        position: center,
        map: map,
        yAnchor: 1,
        content:
          '<div>' +
          '<svg width="28" height="28" viewBox="0 0 24 24">' +
          '<path d="M12 2C8 2 5 5 5 9c0 5 7 13 7 13s7-8 7-13c0-4-3-7-7-7z" fill="#1E88E5" stroke="#0D47A1" stroke-width="1"/>' +
          '<circle cx="12" cy="9" r="3" fill="#FFFFFF"/>' +
          '</svg>' +
          '</div>',
      });`
    : '';

  // 반경 원 - radiusKm이 0(또는 미지정)이면 안 그림 (단일 장소 상세보기용)
  const circleScript =
    radiusKm > 0
      ? `
      new kakao.maps.Circle({
        center: center,
        radius: ${radiusKm * 1000},
        strokeWeight: 1,
        strokeColor: '#5B9BD5',
        strokeOpacity: 0.6,
        fillColor: '#5B9BD5',
        fillOpacity: 0.1,
        map: map,
      });`
      : '';

  return `
<!DOCTYPE html>
<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
  <style>html, body, #map { width: 100%; height: 100%; margin: 0; padding: 0; }</style>
</head>
<body>
  <div id="map"></div>
  <script src="https://dapi.kakao.com/v2/maps/sdk.js?appkey=${KAKAO_JS_KEY}&libraries=services&autoload=false"></script>
  <script>
    var map;
    var places;

    kakao.maps.load(function () {
      var center = new kakao.maps.LatLng(${latitude}, ${longitude});
      map = new kakao.maps.Map(document.getElementById('map'), { center: center, level: ${level} });
      places = new kakao.maps.services.Places();

      ${searchMarkerScript}

      ${circleScript}

      ${myLocScript}
      ${markerScript}

      // WebView 컨테이너 크기가 로드 시점에 완전히 안 잡혀서 지도가 엉뚱한 위치/축척으로
      // 보이는 경우가 있어(카카오맵/구글맵 임베드에서 흔한 문제), 레이아웃이 한 틱 정착된 뒤
      // relayout + 중심 재설정을 한 번 더 강제로 걸어줌.
      setTimeout(function () {
        map.relayout();
        map.setCenter(center);
      }, 0);
      setTimeout(function () {
        map.relayout();
        map.setCenter(center);
      }, 150);
    });

    window.__searchPlace = function (keyword) {
      if (!places) return;
      places.keywordSearch(keyword, function (data, status) {
        if (status === kakao.maps.services.Status.OK && data.length > 0) {
          var r = data[0];
          window.ReactNativeWebView.postMessage(JSON.stringify({
            type: 'search',
            lat: parseFloat(r.y),
            lng: parseFloat(r.x),
            name: r.place_name,
          }));
        } else {
          window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'search', error: true }));
        }
      });
    };

    // 리스트 항목 탭 등 RN 쪽에서 특정 좌표로 지도를 부드럽게 이동시킬 때 사용
    window.__panTo = function (lat, lng) {
      if (!map) return;
      map.panTo(new kakao.maps.LatLng(lat, lng));
    };
  </script>
</body>
</html>`;
}

export default forwardRef<KakaoMapViewHandle, Props>(function KakaoMapView(
  { latitude, longitude, myLocation, showSearchMarker = false, radiusKm = 3, markers = [], level = 5, onMarkerPress, onSearchResult, style },
  ref
) {
  const webviewRef = useRef<WebView>(null);

  const html = useMemo(
    () => buildHtml(latitude, longitude, myLocation, showSearchMarker, radiusKm, markers, level),
    [latitude, longitude, myLocation?.lat, myLocation?.lng, showSearchMarker, radiusKm, level, JSON.stringify(markers)]
  );

  useImperativeHandle(ref, () => ({
    searchPlace: (keyword: string) => {
      webviewRef.current?.injectJavaScript(`window.__searchPlace(${JSON.stringify(keyword)}); true;`);
    },
    panTo: (lat: number, lng: number) => {
      webviewRef.current?.injectJavaScript(`window.__panTo(${lat}, ${lng}); true;`);
    },
  }));

  if (!KAKAO_JS_KEY) return null;

  const handleMessage = (e: WebViewMessageEvent) => {
    try {
      const data = JSON.parse(e.nativeEvent.data);
      if (data.type === 'marker') onMarkerPress?.(data.id);
      else if (data.type === 'search') onSearchResult?.(data.error ? { error: true } : { lat: data.lat, lng: data.lng, name: data.name });
    } catch {
      // ignore malformed messages
    }
  };

  return (
    <WebView
      ref={webviewRef}
      style={[styles.webview, style]}
      originWhitelist={['*']}
      source={{ html, baseUrl: 'http://localhost' }}
      javaScriptEnabled
      domStorageEnabled
      scrollEnabled={false}
      onMessage={handleMessage}
    />
  );
});

const styles = StyleSheet.create({
  webview: { flex: 1, backgroundColor: 'transparent' },
});