/**
 * SCREEN 5 · 인증 완료 (route QuestComplete, fade) — 체크 엠블럼 pop+bob + Confetti,
 * "✦ 인증완료! ✦" 스파클, 보상 chip 순차 등장(EXP·P count-up) + XP PixelProgress.
 * "메인 페이지로 돌아가기" → popToTop().
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
import { colors, fonts, radii, shadow, brand, spring } from '../../theme';
import HazeBackground from '../../components/HazeBackground';
import SpringButton from '../../components/SpringButton';
import Confetti from '../../components/Confetti';
import PixelProgress from '../../components/PixelProgress';
import { CoinW, StarW, useCountUp } from './_parts';

function Spark({ delay = 0 }: { delay?: number }) {
  const v = useSharedValue(0);
  useEffect(() => {
    v.value = withDelay(delay, withRepeat(withTiming(1, { duration: 700, easing: Easing.inOut(Easing.ease) }), -1, true));
  }, []);
  const st = useAnimatedStyle(() => ({ opacity: 0.35 + v.value * 0.65, transform: [{ scale: 0.7 + v.value * 0.5 }] }));
  return <Animated.Text style={[styles.spark, st]}>✦</Animated.Text>;
}

export default function QuestCompleteScreen({ navigation, route }: any) {
  const insets = useSafeAreaInsets();
  const exp = route?.params?.exp ?? 100;
  const point = route?.params?.point ?? 250;

  const expCount = useCountUp(exp, 900);
  const pointCount = useCountUp(point, 900);
  const xpProgress = Math.min(1, exp / 150);

  // check emblem pop → bob (gdq-pop + gdq-bob)
  const scale = useSharedValue(0);
  const rot = useSharedValue(-8);
  const bob = useSharedValue(0);
  useEffect(() => {
    scale.value = withSequence(withTiming(1.12, { duration: 385, easing: Easing.bezier(0.34, 1.56, 0.64, 1) }), withSpring(1, spring.pop));
    rot.value = withSequence(withTiming(2, { duration: 385 }), withSpring(0, spring.pop));
    bob.value = withDelay(700, withRepeat(withTiming(1, { duration: 1500, easing: Easing.inOut(Easing.ease) }), -1, true));
  }, []);
  const iconStyle = useAnimatedStyle(() => ({
    transform: [{ scale: scale.value }, { rotate: `${rot.value}deg` }, { translateY: -6 * bob.value }],
  }));

  return (
    <View style={styles.root}>
      <StatusBar style="light" />
      <HazeBackground />

      <View style={[styles.center, { paddingTop: insets.top + 40 }]}>
        <View style={styles.iconWrap}>
          <Confetti />
          <Animated.View style={iconStyle}>
            <Image source={brand.appIconCheck} style={styles.checkIcon} />
          </Animated.View>
        </View>

        <Animated.View entering={FadeInDown.delay(500).duration(500)} style={styles.titleRow}>
          <Spark />
          <Text style={styles.title}>인증완료!</Text>
          <Spark delay={700} />
        </Animated.View>

        <Animated.View entering={FadeInDown.delay(650).duration(450)} style={styles.chips}>
          <View style={[styles.chip, styles.chipGreen]}>
            <StarW />
            <Text style={styles.chipText}>+{expCount} EXP</Text>
          </View>
          <View style={[styles.chip, styles.chipGold]}>
            <CoinW />
            <Text style={styles.chipText}>+{pointCount} P</Text>
          </View>
        </Animated.View>

        <Animated.View entering={FadeInDown.delay(780).duration(450)} style={styles.xpCard}>
          <View style={styles.xpHead}>
            <Text style={styles.xpLabel}>레벨 경험치</Text>
            <Text style={styles.xpVal}>+{expCount} EXP</Text>
          </View>
          <PixelProgress progress={xpProgress} height={12} color={colors.gold} />
        </Animated.View>

        <Text style={styles.sub}>멋진 선행이었어요! 보상이 지급되었습니다.</Text>
      </View>

      <LinearGradient
        colors={['rgba(238,246,240,0)', colors.screenBg]}
        locations={[0, 0.3]}
        style={[styles.footer, { paddingBottom: insets.bottom + 20 }]}
      >
        <SpringButton onPress={() => navigation.popToTop()} style={[styles.nextBtn, shadow.button]}>
          <Text style={styles.nextText}>메인 페이지로 돌아가기</Text>
        </SpringButton>
      </LinearGradient>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.screenBg },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 30, gap: 22, paddingBottom: 100 },
  iconWrap: { alignItems: 'center', justifyContent: 'center' },
  checkIcon: { width: 132, height: 132 },
  titleRow: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  spark: { color: colors.gold, fontSize: 18 },
  title: { fontFamily: fonts.pixel, fontSize: 24, color: colors.primaryDark },
  chips: { flexDirection: 'row', gap: 10 },
  chip: { flexDirection: 'row', alignItems: 'center', gap: 6, borderRadius: 999, paddingHorizontal: 16, paddingVertical: 8, borderWidth: 1 },
  chipGreen: { backgroundColor: colors.xpGreen, borderColor: '#2E7D32' },
  chipGold: { backgroundColor: colors.gold, borderColor: '#A97D10' },
  chipText: { color: colors.white, fontWeight: '700', fontSize: 14, fontFamily: fonts.bodyB },
  xpCard: { alignSelf: 'stretch', backgroundColor: colors.white, borderRadius: radii.card, borderWidth: 1, borderColor: '#D6E7DC', paddingHorizontal: 16, paddingVertical: 14, gap: 10 },
  xpHead: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  xpLabel: { fontSize: 13, fontWeight: '700', color: colors.textPrimary, fontFamily: fonts.bodyB },
  xpVal: { fontSize: 13, fontWeight: '800', color: '#A9822E', fontFamily: fonts.bodyB },
  sub: { fontSize: 13, color: colors.textSecondary, textAlign: 'center', fontFamily: fonts.bodyR },
  footer: { position: 'absolute', bottom: 0, left: 0, right: 0, paddingHorizontal: 20, paddingTop: 16 },
  nextBtn: { height: 52, borderRadius: radii.button, backgroundColor: colors.primaryDark, alignItems: 'center', justifyContent: 'center' },
  nextText: { color: colors.white, fontSize: 16, fontWeight: '700', fontFamily: fonts.bodyB },
});
