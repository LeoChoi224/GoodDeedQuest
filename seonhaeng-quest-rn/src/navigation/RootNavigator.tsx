/**
 * Root stack — connects the whole app: Login → 회원가입 flow → Main (right drawer
 * wrapping the 5 bottom tabs + team/shortform/admin). Page transitions use the
 * iOS-standard slide+fade. Signup steps share state via SignupProvider.
 */
import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { SignupProvider } from '../context/SignupContext';
import { ToastProvider } from '../components/Toast';
import LoginScreen from '../screens/LoginScreen';
import TermsScreen from '../screens/TermsScreen';
import AccountScreen from '../screens/AccountScreen';
import ProfileScreen from '../screens/ProfileScreen';
import CompleteScreen from '../screens/CompleteScreen';
import AppDrawer from './AppDrawer';
import UserDetailScreen from '../screens/user/UserDetailScreen';

export type RootStackParamList = {
  Login: undefined;
  Terms: undefined;
  Account: undefined;
  Profile: undefined;
  Complete: undefined;
  Main: undefined;
  UserDetail: { user?: any; moderation?: boolean } | undefined;
};

const Stack = createNativeStackNavigator<RootStackParamList>();

export default function RootNavigator() {
  return (
    <SignupProvider>
      <NavigationContainer>
        <ToastProvider>
          <Stack.Navigator
            initialRouteName="Login"
            screenOptions={{
              headerShown: false,
              animation: 'slide_from_right',
              contentStyle: { backgroundColor: '#EEF6F0' },
              gestureEnabled: true,
            }}
          >
            <Stack.Screen name="Login" component={LoginScreen} />
            <Stack.Screen name="Terms" component={TermsScreen} />
            <Stack.Screen name="Account" component={AccountScreen} />
            <Stack.Screen name="Profile" component={ProfileScreen} />
            <Stack.Screen
              name="Complete"
              component={CompleteScreen}
              options={{ animation: 'fade', gestureEnabled: false }}
            />
            <Stack.Screen name="Main" component={AppDrawer} options={{ gestureEnabled: false }} />
            {/* 어디서든 유저 클릭 시 도달하는 공용 상세 (Root 레벨에 등록) */}
            <Stack.Screen name="UserDetail" component={UserDetailScreen} />
          </Stack.Navigator>
        </ToastProvider>
      </NavigationContainer>
    </SignupProvider>
  );
}
