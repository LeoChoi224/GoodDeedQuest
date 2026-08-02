/**
 * Right-side hamburger drawer. Holds the tabs (Main) plus the drawer-only flows
 * (팀 챌린지, 숏폼, 관리자). Custom content = DrawerContent.
 */
import React from 'react';
import { createDrawerNavigator } from '@react-navigation/drawer';
import { useWindowDimensions } from 'react-native';
import DrawerContent from '../components/DrawerContent';
import MainTabs from './MainTabs';
import { TeamStack, ShortformStack, AdminStack } from './flowStacks';
import { ProfileProvider } from '../context/ProfileContext'; // ⭐ 수정: 마이페이지 프로필 헤더 ↔ 드로어 상단 실시간 동기화

const Drawer = createDrawerNavigator();

export default function AppDrawer() {
  const { width } = useWindowDimensions();
  return (
    // ⭐ 수정: 로그인 이후(메인 셸)에서만 프로필을 공유하도록 이 레벨에 Provider를 둔다
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
        <Drawer.Screen name="Main" component={MainTabs} />
        <Drawer.Screen name="TeamChallenge" component={TeamStack} />
        <Drawer.Screen name="Shortform" component={ShortformStack} />
        <Drawer.Screen name="Admin" component={AdminStack} />
      </Drawer.Navigator>
    </ProfileProvider>
  );
}
