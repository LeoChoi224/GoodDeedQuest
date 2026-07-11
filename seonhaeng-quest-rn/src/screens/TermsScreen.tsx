/**
 * SCREEN 2 · 약관동의 — 전체동의 + 3 required terms. "다음" is disabled (gray) until
 * all three are agreed; tapping it while disabled triggers an error shake.
 * Terms card + rows stagger in (Fade List / ig-fadeup).
 */
import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, Pressable } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { LinearGradient } from 'expo-linear-gradient';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Animated, { FadeInDown } from 'react-native-reanimated';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import type { RootStackParamList } from '../navigation/RootNavigator';
import { colors, fonts, radii, shadow } from '../theme';
import HazeBackground from '../components/HazeBackground';
import { AppHeader } from '../components/Chrome';
import Checkbox from '../components/Checkbox';
import SpringButton from '../components/SpringButton';
import Shake from '../components/Shake';
import { useSignup } from '../context/SignupContext';

type Props = NativeStackScreenProps<RootStackParamList, 'Terms'>;

const TERM_LABELS: Record<'t1' | 't2' | 't3', string> = {
  t1: '(필수) 서비스 이용약관',
  t2: '(필수) 개인정보 수집 및 이용',
  t3: '(필수) 위치기반 서비스 약관',
};

export default function TermsScreen({ navigation }: Props) {
  const insets = useSafeAreaInsets();
  const { terms, setTerm, toggleAllTerms, allAgreed } = useSignup();
  const [shake, setShake] = useState(0);

  const onNext = () => {
    if (!allAgreed) {
      setShake((s) => s + 1);
      return;
    }
    navigation.navigate('Account');
  };

  return (
    <View style={styles.root}>
      <StatusBar style="dark" />
      <HazeBackground />

      <View style={{ paddingTop: insets.top, backgroundColor: colors.white }}>
        <AppHeader onBack={() => navigation.goBack()} />
      </View>

      <ScrollView contentContainerStyle={styles.body} showsVerticalScrollIndicator={false}>
        <Text style={styles.h1}>약관에 동의 해{'\n'}주세요</Text>

        <Animated.View entering={FadeInDown.duration(400)} style={styles.termsCard}>
          <Pressable onPress={toggleAllTerms} style={styles.allRow}>
            <Checkbox checked={allAgreed} onToggle={toggleAllTerms} />
            <Text style={styles.allLabel}>전체동의</Text>
          </Pressable>

          {(['t1', 't2', 't3'] as const).map((k, i) => (
            <Animated.View
              key={k}
              entering={FadeInDown.delay(80 + i * 100).duration(420)}
              style={[styles.termRow, i === 2 && { borderBottomWidth: 0 }]}
            >
              <Checkbox checked={terms[k]} onToggle={() => setTerm(k)} />
              <Text style={styles.termLabel}>{TERM_LABELS[k]}</Text>
              <Pressable hitSlop={8}>
                <Text style={styles.viewLink}>보기</Text>
              </Pressable>
            </Animated.View>
          ))}
        </Animated.View>

        <Text style={styles.note}>"보기" 탭 → 약관 상세 바텀시트</Text>
      </ScrollView>

      {/* pinned footer */}
      <LinearGradient
        colors={['rgba(238,246,240,0)', colors.screenBg]}
        locations={[0, 0.3]}
        style={[styles.footer, { paddingBottom: insets.bottom + 20 }]}
      >
        <Shake trigger={shake}>
          <SpringButton
            onPress={onNext}
            active={allAgreed}
            bgColors={[colors.disabled, colors.primaryDark]}
            style={[styles.nextBtn, allAgreed && shadow.button]}
          >
            <Text style={styles.nextText}>다음</Text>
          </SpringButton>
        </Shake>
      </LinearGradient>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.screenBg },
  body: { paddingHorizontal: 20, paddingTop: 26, paddingBottom: 120 },
  h1: { fontSize: 20, fontWeight: '700', color: colors.textPrimary, marginBottom: 22, lineHeight: 27, fontFamily: fonts.bodyB },
  termsCard: { backgroundColor: colors.white, borderRadius: radii.card, overflow: 'hidden', ...shadow.card },
  allRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    height: 56,
    paddingHorizontal: 18,
    backgroundColor: colors.cellHeader,
    borderBottomWidth: 1,
    borderBottomColor: colors.inputBorder,
  },
  allLabel: { fontSize: 16, fontWeight: '700', color: colors.textPrimary, fontFamily: fonts.bodyB },
  termRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    height: 56,
    paddingHorizontal: 18,
    borderBottomWidth: 1,
    borderBottomColor: '#F1F3F2',
  },
  termLabel: { flex: 1, fontSize: 15, color: colors.textPrimary, fontFamily: fonts.bodyR },
  viewLink: { fontSize: 13, color: colors.primaryDark, fontFamily: fonts.bodyM },
  note: { fontSize: 12, color: colors.textMuted, marginTop: 12, paddingLeft: 4, fontFamily: fonts.bodyR },
  footer: { position: 'absolute', bottom: 0, left: 0, right: 0, paddingHorizontal: 20, paddingTop: 16 },
  nextBtn: {
    height: 52,
    borderRadius: radii.button,
    alignItems: 'center',
    justifyContent: 'center',
  },
  nextText: { color: colors.white, fontSize: 16, fontWeight: '700', fontFamily: fonts.bodyB },
});
