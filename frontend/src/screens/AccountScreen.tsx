/**
 * SCREEN 3 · 계정 입력 — 이메일(중복확인) · 비밀번호 · 비밀번호 확인.
 * Validation on "다음": email must pass 중복확인, password must be 영문·숫자 포함 8자 이상,
 * confirm must match. Invalid fields error-shake and surface an inline message.
 */
import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, KeyboardAvoidingView, Platform } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { LinearGradient } from 'expo-linear-gradient';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import type { RootStackParamList } from '../navigation/RootNavigator';
import { colors, fonts, radii, shadow } from '../theme';
import HazeBackground from '../components/HazeBackground';
import { AppHeader } from '../components/Chrome';
import GdqInput from '../components/GdqInput';
import SpringButton from '../components/SpringButton';
import Shake from '../components/Shake';
import { MailIcon, LockIcon, EyeOpen, EyeOff } from '../components/PixelIcons';
import { useSignup, isPasswordValid } from '../context/SignupContext';

type Props = NativeStackScreenProps<RootStackParamList, 'Account'>;

export default function AccountScreen({ navigation }: Props) {
  const insets = useSafeAreaInsets();
  const s = useSignup();
  const [showPw, setShowPw] = useState(false);
  const [emailShake, setEmailShake] = useState(0);
  const [pwShake, setPwShake] = useState(0);
  const [confirmShake, setConfirmShake] = useState(0);
  const [pwError, setPwError] = useState<string | null>(null);
  const [confirmError, setConfirmError] = useState<string | null>(null);

  const onCheckEmail = async () => {
    const ok = await s.checkEmail();
    if (!ok) setEmailShake((v) => v + 1);
  };

  const onNext = async () => {
    let ok = true;

    // 【판단】 이미 중복확인을 통과했으면(emailOk) 서버를 다시 부르지 않는다.
    //        그 사이 남이 같은 이메일로 가입했을 수는 있지만, 최종 차단은
    //        가입 요청을 받는 서버가 한다.
    const eok = s.emailOk || (await s.checkEmail());
    if (!eok) {
      setEmailShake((v) => v + 1);
      ok = false;
    }

    if (!isPasswordValid(s.password)) {
      setPwError('영문·숫자 포함 8자 이상 입력해 주세요.');
      setPwShake((v) => v + 1);
      ok = false;
    } else {
      setPwError(null);
    }

    if (!(s.passwordConfirm.length > 0 && s.password === s.passwordConfirm)) {
      setConfirmError('비밀번호가 일치하지 않습니다.');
      setConfirmShake((v) => v + 1);
      ok = false;
    } else {
      setConfirmError(null);
    }

    if (ok) navigation.navigate('Profile');
  };

  return (
    <View style={styles.root}>
      <StatusBar style="dark" />
      <HazeBackground />

      <View style={{ paddingTop: insets.top, backgroundColor: colors.white }}>
        <AppHeader onBack={() => navigation.goBack()} />
      </View>

      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <ScrollView contentContainerStyle={styles.body} showsVerticalScrollIndicator={false} keyboardShouldPersistTaps="handled">
          <Text style={styles.h1}>계정 정보를 입력해 주세요</Text>

          {/* email */}
          <Text style={styles.label}>이메일</Text>
          <Shake trigger={emailShake}>
            <View style={styles.emailRow}>
              <View style={{ flex: 1 }}>
                <GdqInput
                  value={s.email}
                  onChangeText={s.setEmail}
                  keyboardType="email-address"
                  autoCapitalize="none"
                  placeholder="이메일을 입력하세요"
                  leftIcon={<MailIcon />}
                />
              </View>
              <SpringButton style={styles.dupBtn} onPress={onCheckEmail} disabled={s.emailChecking}>
                <Text style={styles.dupText}>{s.emailChecking ? '확인 중' : '중복확인'}</Text>
              </SpringButton>
            </View>
            {s.emailMsg ? <Text style={[styles.fieldMsg, { color: s.emailMsg.color }]}>{s.emailMsg.text}</Text> : null}
          </Shake>

          {/* password */}
          <Text style={[styles.label, { marginTop: 14 }]}>비밀번호</Text>
          <Shake trigger={pwShake}>
            <GdqInput
              value={s.password}
              onChangeText={(v) => {
                s.setPassword(v);
                if (pwError) setPwError(null);
              }}
              placeholder="비밀번호를 입력하세요"
              secureTextEntry={!showPw}
              autoCapitalize="none"
              leftIcon={<LockIcon />}
              rightAccessory={showPw ? <EyeOff /> : <EyeOpen />}
              onRightPress={() => setShowPw((p) => !p)}
            />
          </Shake>

          {/* confirm */}
          <Text style={[styles.label, { marginTop: 16 }]}>비밀번호 확인</Text>
          <Shake trigger={confirmShake}>
            <GdqInput
              value={s.passwordConfirm}
              onChangeText={(v) => {
                s.setPasswordConfirm(v);
                if (confirmError) setConfirmError(null);
              }}
              placeholder="비밀번호를 다시 입력하세요"
              secureTextEntry={!showPw}
              autoCapitalize="none"
              leftIcon={<LockIcon />}
            />
          </Shake>

          <Text style={[styles.helper, (pwError || confirmError) && { color: colors.danger }]}>
            {pwError || confirmError || '영문·숫자 포함 8자 이상 입력해 주세요.'}
          </Text>
        </ScrollView>
      </KeyboardAvoidingView>

      <LinearGradient
        colors={['rgba(238,246,240,0)', colors.screenBg]}
        locations={[0, 0.3]}
        style={[styles.footer, { paddingBottom: insets.bottom + 20 }]}
      >
        <SpringButton onPress={onNext} style={[styles.nextBtn, shadow.button]} disabled={s.emailChecking}>
          <Text style={styles.nextText}>{s.emailChecking ? '확인 중...' : '다음'}</Text>
        </SpringButton>
      </LinearGradient>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.screenBg },
  body: { paddingHorizontal: 20, paddingTop: 26, paddingBottom: 130 },
  h1: { fontSize: 20, fontWeight: '700', color: colors.textPrimary, marginBottom: 22, fontFamily: fonts.bodyB },
  label: { fontSize: 12, fontWeight: '600', color: colors.textPrimary, marginBottom: 7, fontFamily: fonts.bodyM },
  emailRow: { flexDirection: 'row', gap: 8 },
  dupBtn: {
    width: 80,
    height: 50,
    borderRadius: radii.input,
    backgroundColor: colors.primaryDark,
    alignItems: 'center',
    justifyContent: 'center',
  },
  dupText: { color: colors.white, fontSize: 13, fontWeight: '600', fontFamily: fonts.bodyM },
  fieldMsg: { marginTop: 8, marginLeft: 2, fontSize: 12, fontWeight: '600', fontFamily: fonts.bodyM },
  helper: { fontSize: 12, color: colors.textSecondary, paddingLeft: 2, marginTop: 12, fontFamily: fonts.bodyR },
  footer: { position: 'absolute', bottom: 0, left: 0, right: 0, paddingHorizontal: 20, paddingTop: 16 },
  nextBtn: {
    height: 52,
    borderRadius: radii.button,
    backgroundColor: colors.primaryDark,
    alignItems: 'center',
    justifyContent: 'center',
  },
  nextText: { color: colors.white, fontSize: 16, fontWeight: '700', fontFamily: fonts.bodyB },
});
