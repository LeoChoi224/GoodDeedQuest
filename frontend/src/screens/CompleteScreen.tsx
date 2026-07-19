/**
 * SCREEN 5 · 회원가입 완료 — gold celebration flash (gdq-flash), confetti burst,
 * app-icon-check pop (gdq-pop) → gentle bob (gdq-bob), "✦ 환영합니다! ✦" welcome
 * entrance with sparkle pulse. "로그인창으로 이동" resets state and loops to Login.
 */
import React, { useEffect } from 'react';
import { View, Text, Image, StyleSheet } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { LinearGradient } from 'expo-linear-gradient';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Animated, {
  FadeInDown,
  useSharedValue,
  useAnimatedStyle,
  withTiming,
  withSpring,
  withSequence,
  withRepeat,
  withDelay,
  Easing,
} from 'react-native-reanimated';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import type { RootStackParamList } from '../navigation/RootNavigator';
import { colors, fonts, radii, shadow, brand, spring } from '../theme';
import HazeBackground from '../components/HazeBackground';
import { AppHeader } from '../components/Chrome';
import SpringButton from '../components/SpringButton';
import Confetti from '../components/Confetti';
import { useSignup } from '../context/SignupContext';

type Props = NativeStackScreenProps<RootStackParamList, 'Complete'>;

/** ✦ spark — gdq-spark: scale .7↔1.2, opacity .35↔1, infinite, per-delay. */
function Spark({ delay = 0 }: { delay?: number }) {
  const v = useSharedValue(0);
  useEffect(() => {
    v.value = withDelay(delay, withRepeat(withTiming(1, { duration: 700, easing: Easing.inOut(Easing.ease) }), -1, true));
  }, []);
  const st = useAnimatedStyle(() => ({
    opacity: 0.35 + v.value * 0.65,
    transform: [{ scale: 0.7 + v.value * 0.5 }],
  }));
  return (
    <Animated.Text style={[styles.spark, st]}>✦</Animated.Text>
  );
}

export default function CompleteScreen({ navigation }: Props) {
  const insets = useSafeAreaInsets();
  const s = useSignup();

  // gold flash: opacity .5 → 0 over 1s
  const flash = useSharedValue(0.5);
  // pop then bob for the check icon
  const scale = useSharedValue(0);
  const rot = useSharedValue(-10);
  const bob = useSharedValue(0);

  useEffect(() => {
    flash.value = withTiming(0, { duration: 1000, easing: Easing.out(Easing.ease) });

    // gdq-pop: 0 → 1.14(rot 3) → .95(rot -1) → 1(rot 0)
    scale.value = withSequence(
      withTiming(1.14, { duration: 380, easing: Easing.bezier(0.34, 1.56, 0.64, 1) }),
      withSpring(1, spring.pop)
    );
    rot.value = withSequence(
      withTiming(3, { duration: 380 }),
      withTiming(-1, { duration: 90 }),
      withSpring(0, spring.pop)
    );

    // gdq-bob starts after pop (~0.7s): translateY 0 ↔ -7 loop
    bob.value = withDelay(
      700,
      withRepeat(withTiming(1, { duration: 1500, easing: Easing.inOut(Easing.ease) }), -1, true)
    );
  }, []);

  const flashStyle = useAnimatedStyle(() => ({ opacity: flash.value }));
  const iconStyle = useAnimatedStyle(() => ({
    transform: [{ scale: scale.value }, { rotate: `${rot.value}deg` }, { translateY: -7 * bob.value }],
  }));

  const onBackToLogin = () => {
    s.reset();
    navigation.reset({ index: 0, routes: [{ name: 'Login' }] });
  };

  return (
    <View style={styles.root}>
      <StatusBar style="dark" />
      <HazeBackground />

      <View style={{ paddingTop: insets.top, backgroundColor: colors.white }}>
        <AppHeader />
      </View>

      {/* gold celebration flash */}
      <Animated.View style={[StyleSheet.absoluteFill, styles.flash, flashStyle]} pointerEvents="none" />

      {/* centered content */}
      <View style={styles.center}>
        <View style={styles.iconWrap}>
          <Confetti />
          <Animated.View style={iconStyle}>
            <Image source={brand.appIconCheck} style={styles.checkIcon} />
          </Animated.View>
        </View>

        <Animated.View entering={FadeInDown.delay(550).duration(500)} style={styles.welcomeRow}>
          <Spark />
          <Text style={styles.welcomeText}>환영합니다!</Text>
          <Spark delay={700} />
        </Animated.View>

        <Text style={styles.sub}>이제 당신도 선한 영웅입니다.{'\n'}첫 번째 퀘스트가 기다리고 있어요.</Text>
      </View>

      <LinearGradient
        colors={['rgba(238,246,240,0)', colors.screenBg]}
        locations={[0, 0.3]}
        style={[styles.footer, { paddingBottom: insets.bottom + 20 }]}
      >
        <SpringButton onPress={onBackToLogin} style={[styles.nextBtn, shadow.button]}>
          <Text style={styles.nextText}>로그인창으로 이동</Text>
        </SpringButton>
      </LinearGradient>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.screenBg },
  flash: { backgroundColor: colors.parchment, zIndex: 15 },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 24, gap: 26 },
  iconWrap: { alignItems: 'center', justifyContent: 'center' },
  checkIcon: { width: 152, height: 152 },
  welcomeRow: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  spark: { color: colors.gold, fontSize: 20 },
  welcomeText: { fontFamily: fonts.pixel, fontSize: 26, color: colors.primaryDark },
  sub: { fontSize: 14, color: colors.textSecondary, textAlign: 'center', lineHeight: 21, fontFamily: fonts.bodyR },
  footer: { position: 'absolute', bottom: 0, left: 0, right: 0, paddingHorizontal: 20, paddingTop: 16 },
  nextBtn: { height: 52, borderRadius: radii.button, backgroundColor: colors.primaryDark, alignItems: 'center', justifyContent: 'center' },
  nextText: { color: colors.white, fontSize: 16, fontWeight: '700', fontFamily: fonts.bodyB },
});
