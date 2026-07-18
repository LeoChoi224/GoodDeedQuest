/**
 * Bottom tab navigator with the custom BottomNav tab bar.
 * Order: 커뮤니티 | 지도 | 홈 | 상점 | 마이페이지, initial = 홈.
 */
import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import BottomNav from '../components/BottomNav';
import { CommunityStack, MapStack, HomeStack, ShopStack, MyStack } from './flowStacks';

const Tab = createBottomTabNavigator();

export default function MainTabs() {
  return (
    <Tab.Navigator
      initialRouteName="Home"
      screenOptions={{ headerShown: false }}
      tabBar={(props) => <BottomNav {...props} />}
    >
      <Tab.Screen name="Community" component={CommunityStack} />
      <Tab.Screen name="Map" component={MapStack} />
      <Tab.Screen name="Home" component={HomeStack} />
      <Tab.Screen name="Shop" component={ShopStack} />
      <Tab.Screen name="My" component={MyStack} />
    </Tab.Navigator>
  );
}
