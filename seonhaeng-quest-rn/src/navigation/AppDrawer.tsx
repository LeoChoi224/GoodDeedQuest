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

const Drawer = createDrawerNavigator();

export default function AppDrawer() {
  const { width } = useWindowDimensions();
  return (
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
  );
}
