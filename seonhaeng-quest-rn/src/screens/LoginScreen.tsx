/**
 * SCREEN 1 · 로그인 — dark green hero (twinkle stars, drifting particles, pixel
 * skyline, app icon + 선행퀘스트) with a white login sheet sliding up over it.
 * Email + password (show/hide) + 로그인하기 (sword) + 회원가입 link + kakao/google.
 */
import React, { useState } from 'react';
import {
  View,
  Text,
  Image,
  StyleSheet,
  ScrollView,
  Pressable,
  Dimensions,
  useWindowDimensions,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { StatusBar } from 'expo-status-bar';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Animated, { FadeInDown } from 'react-native-reanimated';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import type { RootStackParamList } from '../navigation/RootNavigator';
import { colors, fonts, radii, shadow, heroGradient, brand } from '../theme';
import Starfield from '../components/Starfield';
import Skyline from '../components/Skyline';
import SpringButton from '../components/SpringButton';
import GdqInput from '../components/GdqInput';
import { MailIcon, LockIcon, SwordIcon, EyeOpen, EyeOff, HamburgerIcon, KakaoIcon, GoogleIcon } from '../components/PixelIcons';

type Props = NativeStackScreenProps<RootStackParamList, 'Login'>;

export default function LoginScreen({ navigation }: Props) {
  const insets = useSafeAreaInsets();
  const { width } = useWindowDimensions();
  const [showPw, setShowPw] = useState(false);

  const HERO_H = Math.max(400, Dimensions.get('window').height * 0.5);

  return (
    <View style={styles.root}>
      <StatusBar style="light" />

      {/* ---- hero ---- */}
      <LinearGradient
        colors={heroGradient.colors}
        locations={heroGradient.locations}
        style={[styles.hero, { height: HERO_H }]}
      >
        <Starfield />
        <View style={styles.skyline} pointerEvents="none">
          <Skyline width={width} height={150} />
        </View>
        <View style={[styles.logoBlock, { top: insets.top + 34 }]}>
          <Image source={brand.appIcon} style={styles.appIcon} />
          <Text style={styles.brandTitle}>선행퀘스트</Text>
          <Text style={styles.brandSub}>오늘의 선행 퀘스트를 시작하세요</Text>
        </View>
      </LinearGradient>

      {/* ---- hamburger ---- */}
      <Pressable style={[styles.ham, { top: insets.top + 6 }]} hitSlop={8}>
        <HamburgerIcon size={22} color={colors.parchment} />
      </Pressable>

      {/* ---- login sheet ---- */}
      <Animated.View
        entering={FadeInDown.duration(400)}
        style={[styles.card, { marginTop: HERO_H - 130 }]}
      >
        <LinearGradient
          colors={['#FFF8E7', '#FFEFC9', '#FFF8E7']}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 0 }}
          style={styles.goldStrip}
        />
        <ScrollView
          contentContainerStyle={styles.cardBody}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
        >
          <View style={styles.handle} />
          <Text style={styles.cardTitle}>로그인</Text>

          <Text style={styles.label}>이메일</Text>
          <GdqInput
            style={styles.inputSpacing}
            keyboardType="email-address"
            autoCapitalize="none"
            placeholder="이메일을 입력하세요"
            leftIcon={<MailIcon />}
          />

          <Text style={styles.label}>비밀번호</Text>
          <GdqInput
            placeholder="비밀번호를 입력하세요"
            secureTextEntry={!showPw}
            leftIcon={<LockIcon />}
            rightAccessory={showPw ? <EyeOff /> : <EyeOpen />}
            onRightPress={() => setShowPw((s) => !s)}
          />

          <SpringButton
            style={styles.primaryBtn}
            onPress={() => navigation.reset({ index: 0, routes: [{ name: 'Main' }] })}
          >
            <SwordIcon />
            <Text style={styles.primaryBtnText}>로그인하기</Text>
          </SpringButton>

          <Text style={styles.signupHint}>
            아직 영웅이 아니신가요?{'  '}
            <Text style={styles.signupLink} onPress={() => navigation.navigate('Terms')}>
              회원가입
            </Text>
          </Text>

          <View style={styles.dividerRow}>
            <View style={styles.divider} />
            <Text style={styles.dividerText}>또는</Text>
            <View style={styles.divider} />
          </View>

          <View style={styles.socialRow}>
            <SpringButton style={[styles.socialBtn, { backgroundColor: colors.kakao }]}>
              <KakaoIcon />
              <Text style={[styles.socialText, { color: colors.kakaoText }]}>카카오</Text>
            </SpringButton>
            <SpringButton style={[styles.socialBtn, styles.googleBtn]}>
              <GoogleIcon />
              <Text style={[styles.socialText, { color: colors.textPrimary }]}>구글</Text>
            </SpringButton>
          </View>
        </ScrollView>
      </Animated.View>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.white },
  hero: { position: 'absolute', top: 0, left: 0, right: 0, overflow: 'hidden' },
  skyline: { position: 'absolute', bottom: 0, left: 0, right: 0, height: 150 },
  logoBlock: { position: 'absolute', left: 0, right: 0, alignItems: 'center', gap: 16 },
  appIcon: { width: 132, height: 132 },
  brandTitle: {
    fontFamily: fonts.pixel,
    fontSize: 30,
    color: colors.white,
    letterSpacing: 1,
    textShadowColor: 'rgba(0,0,0,0.35)',
    textShadowOffset: { width: 0, height: 2 },
    textShadowRadius: 0,
  },
  brandSub: { fontSize: 13, color: 'rgba(255,255,255,0.62)', fontFamily: fonts.bodyR },
  ham: {
    position: 'absolute',
    right: 18,
    zIndex: 21,
    width: 38,
    height: 38,
    borderRadius: 10,
    backgroundColor: 'rgba(255,248,231,0.12)',
    borderWidth: 1,
    borderColor: 'rgba(212,160,23,0.5)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  card: {
    flex: 1,
    backgroundColor: colors.white,
    borderTopLeftRadius: radii.cardLg,
    borderTopRightRadius: radii.cardLg,
    overflow: 'hidden',
    ...shadow.card,
    shadowOffset: { width: 0, height: -8 },
    shadowOpacity: 0.14,
    shadowRadius: 30,
  },
  goldStrip: { height: 5, width: '100%' },
  cardBody: { paddingHorizontal: 24, paddingTop: 22, paddingBottom: 40 },
  handle: { width: 38, height: 4, borderRadius: 2, backgroundColor: '#E5E7EB', alignSelf: 'center', marginBottom: 16 },
  cardTitle: { fontSize: 18, fontWeight: '700', color: colors.textPrimary, marginBottom: 20, fontFamily: fonts.bodyB },
  label: { fontSize: 12, fontWeight: '600', color: colors.textPrimary, marginBottom: 7, fontFamily: fonts.bodyM },
  inputSpacing: {},
  primaryBtn: {
    height: 52,
    borderRadius: radii.button,
    backgroundColor: colors.primaryDark,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 9,
    marginTop: 20,
    ...shadow.button,
  },
  primaryBtnText: { color: colors.white, fontSize: 16, fontWeight: '700', fontFamily: fonts.bodyB },
  signupHint: { textAlign: 'center', fontSize: 13, color: colors.textSecondary, marginTop: 14, fontFamily: fonts.bodyR },
  signupLink: { color: colors.primaryDark, fontWeight: '700', textDecorationLine: 'underline', fontFamily: fonts.bodyB },
  dividerRow: { flexDirection: 'row', alignItems: 'center', gap: 12, marginVertical: 16 },
  divider: { flex: 1, height: 1, backgroundColor: colors.divider },
  dividerText: { fontSize: 12, color: colors.textMuted, fontFamily: fonts.bodyR },
  socialRow: { flexDirection: 'row', gap: 12 },
  socialBtn: {
    flex: 1,
    height: 48,
    borderRadius: radii.input,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 7,
  },
  googleBtn: { backgroundColor: colors.googleBg, borderWidth: 1, borderColor: colors.inputBorder },
  socialText: { fontSize: 14, fontWeight: '600', fontFamily: fonts.bodyM },
});
