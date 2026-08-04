/**
 * 선행퀘스트 — 로그인/회원가입 플로우 (01_login_flow) as a runnable RN app.
 * Loads DotGothic16 (pixel titles) + Noto Sans KR (body) then mounts the flow.
 */
import React from 'react';
import { View, ActivityIndicator, StyleSheet } from 'react-native';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { useFonts, DotGothic16_400Regular } from '@expo-google-fonts/dotgothic16';
import RootNavigator from './src/navigation/RootNavigator';
import { colors } from './src/theme';

export default function App() {
  const [loaded, error] = useFonts({
    DotGothic16_400Regular,
    // Pretendard (local OTF) — body typography
    'Pretendard-Regular': require('./assets/fonts/Pretendard-Regular.otf'),
    'Pretendard-Medium': require('./assets/fonts/Pretendard-Medium.otf'),
    'Pretendard-Bold': require('./assets/fonts/Pretendard-Bold.otf'),
  });

  // Proceed even if a font fails to load — custom fontFamily names simply fall
  // back to the system font (Korean still renders), so we never brick on splash.
  if (!loaded && !error) {
    return (
      <View style={styles.splash}>
        <ActivityIndicator color={colors.gold} size="large" />
      </View>
    );
  }

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <SafeAreaProvider>
        <RootNavigator />
      </SafeAreaProvider>
    </GestureHandlerRootView>
  );
}

const styles = StyleSheet.create({
  splash: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.primaryDark },
});
