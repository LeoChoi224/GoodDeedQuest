/**
 * Right-side hamburger drawer. Holds the tabs (Main) plus the drawer-only flows
 * (팀 챌린지, 숏폼, 관리자). Custom content = DrawerContent.
 *
 * ⭐ 추가: 로그인 세션 동안(이 컴포넌트가 마운트돼 있는 동안) 10분마다 GPS 위치를
 * 서버에 저장. 포그라운드에서만 동작(백그라운드/앱 종료 시엔 저장 안 됨) -
 * VolSearchScreen에서 쓰던 것과 같은 expo-location + updateMyLocation() 조합을
 * 앱 전역으로 확장한 것뿐, 백엔드/API 래퍼는 기존 것 재사용. RootNavigator가
 * 로그아웃 시 이 컴포넌트를 통째로 언마운트하므로 인터벌도 자동으로 정리됨.
 */
import React, { useEffect } from 'react';
import { createDrawerNavigator } from '@react-navigation/drawer';
import { useWindowDimensions } from 'react-native';
import * as Location from 'expo-location';
import DrawerContent from '../components/DrawerContent';
import MainTabs from './MainTabs';
import { TeamStack, ShortformStack, AdminStack } from './flowStacks';
import { ProfileProvider } from '../context/ProfileContext'; // 마이페이지 프로필 헤더 ↔ 드로어 상단 실시간 동기화
import { updateMyLocation } from '../api/auth';

const Drawer = createDrawerNavigator();

const LOCATION_UPDATE_INTERVAL_MS = 10 * 60 * 1000; // 10분

export default function AppDrawer() {
  const { width } = useWindowDimensions();

  useEffect(() => {
    let cancelled = false;

    const pushLocation = async () => {
      try {
        const { status } = await Location.requestForegroundPermissionsAsync();
        if (status !== 'granted' || cancelled) return;

        const pos = await Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.Balanced });
        if (cancelled) return;

        await updateMyLocation(pos.coords.latitude, pos.coords.longitude);
      } catch {
        // 위치 저장 실패는 조용히 무시 - 앱 사용 흐름에 지장 주면 안 됨
      }
    };

    pushLocation(); // 로그인 직후 1회 즉시 저장
    const timer = setInterval(pushLocation, LOCATION_UPDATE_INTERVAL_MS);

    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, []);

  return (
    // 로그인 이후(메인 셸)에서만 프로필을 공유하도록 이 레벨에 Provider를 둔다
    <ProfileProvider>
      <Drawer.Navigator
        drawerContent={(props) => <DrawerContent {...props} />}
        screenOptions={{
          headerShown: false,
          drawerPosition: 'right',
          drawerType: 'front',
          drawerStyle: { width: Math.min(320, width * 0.82) },
          swipeEnabled: false,
        }}
      >
        {/* ⭐ 수정: RootNavigator의 최상위 "Main"(AppDrawer 자체)과 이름이 겹쳐
            React Navigation이 "confusing behavior during navigation" 경고를
            띄우던 문제 - 드로어 안쪽의 탭 네비게이터는 별도 이름(Tabs)으로 분리한다. */}
        <Drawer.Screen name="Tabs" component={MainTabs} />
        <Drawer.Screen name="TeamChallenge" component={TeamStack} />
        <Drawer.Screen name="Shortform" component={ShortformStack} />
        <Drawer.Screen name="Admin" component={AdminStack} />
      </Drawer.Navigator>
    </ProfileProvider>
  );
}