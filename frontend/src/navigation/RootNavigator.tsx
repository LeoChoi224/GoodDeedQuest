/**
 * Root stack — connects the whole app: Login → 회원가입 flow → Main (right drawer
 * wrapping the 5 bottom tabs + team/shortform/admin). Page transitions use the
 * iOS-standard slide+fade. Signup steps share state via SignupProvider.
 */
import React from 'react';
import { View, ActivityIndicator, StyleSheet } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { SignupProvider } from '../context/SignupContext';
import { AuthProvider, useAuth } from '../context/AuthContext';
import { ToastProvider } from '../components/Toast';
import { colors } from '../theme';
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
  // 【판단】 social=true 면 소셜 로그인으로 막 만들어진 계정이다. 이 경우 Profile
  //        화면은 계정을 새로 만들면(register) 안 되고, 이미 있는 계정에 프로필만
  //        채워야(PATCH /auth/me) 한다.
  Profile: { social?: boolean } | undefined;
  Complete: undefined;
  Main: undefined;
  UserDetail: { user?: any; moderation?: boolean } | undefined;
};

const Stack = createNativeStackNavigator<RootStackParamList>();

/**
 * 로그인 여부에 따라 아예 다른 화면 묶음을 그린다.
 *
 * 【판단】 화면을 다 등록해두고 "로그인 안 했으면 로그인으로 보내기"로 막지 않는다.
 *        그러면 등록은 돼 있으니 어떤 경로로든 도달할 여지가 남는다. 아예 없는
 *        화면은 도달할 방법이 없다. 로그아웃되면 로그인 후 화면들이 통째로
 *        사라지므로 되돌아가기(뒤로가기)도 자동으로 막힌다.
 */
function Routes() {
  const { token, booting } = useAuth();

  // 토큰을 확인하는 동안. 여기서 로그인 화면을 먼저 보여주면 이미 로그인한
  // 사용자에게도 로그인 화면이 깜빡 스친다.
  if (booting) {
    return (
      <View style={styles.splash}>
        <ActivityIndicator color={colors.gold} size="large" />
      </View>
    );
  }

  return (
    <Stack.Navigator
      screenOptions={{
        headerShown: false,
        animation: 'slide_from_right',
        contentStyle: { backgroundColor: '#EEF6F0' },
        gestureEnabled: true,
      }}
    >
      {token ? (
        <>
          <Stack.Screen name="Main" component={AppDrawer} options={{ gestureEnabled: false }} />
          {/* 어디서든 유저 클릭 시 도달하는 공용 상세 (Root 레벨에 등록) */}
          <Stack.Screen name="UserDetail" component={UserDetailScreen} />
        </>
      ) : (
        <>
          <Stack.Screen name="Login" component={LoginScreen} />
          <Stack.Screen name="Terms" component={TermsScreen} />
          <Stack.Screen name="Account" component={AccountScreen} />
          <Stack.Screen name="Profile" component={ProfileScreen} />
          <Stack.Screen
            name="Complete"
            component={CompleteScreen}
            options={{ animation: 'fade', gestureEnabled: false }}
          />
        </>
      )}
    </Stack.Navigator>
  );
}

export default function RootNavigator() {
  return (
    <AuthProvider>
      <SignupProvider>
        <NavigationContainer>
          <ToastProvider>
            <Routes />
          </ToastProvider>
        </NavigationContainer>
      </SignupProvider>
    </AuthProvider>
  );
}

const styles = StyleSheet.create({
  splash: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.primaryDark },
});
