// SignupAccountScreen.js — React Native (Expo) 회원가입 2단계: 계정정보
// 선행퀘스트 / 스토리보드 8번 기준

import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Svg, { Path } from 'react-native-svg';

import { COLORS } from '../디자인/SignupAccountScreen.styles';
import { styles } from '../디자인/SignupAccountScreen.styles';

function CareIcon({ size = 18 }) {
  return (
    <Svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth={1.7} strokeLinecap="round" strokeLinejoin="round">
      <Path d="M12 6.8c-.9-1.6-3-1.8-4.1-.4-.9 1.1-.7 2.7.4 3.7L12 13l3.7-2.9c1.1-1 1.3-2.6.4-3.7-1.1-1.4-3.2-1.2-4.1.4Z" />
      <Path d="M4.3 13.2c0 3.2 2.9 5.9 6.4 6.3" />
      <Path d="M19.7 13.2c0 3.2-2.9 5.9-6.4 6.3" />
    </Svg>
  );
}

export default function SignupAccountScreen({ navigation }) {
  const [id, setId] = useState('');
  const [pw1, setPw1] = useState('');
  const [pw2, setPw2] = useState('');
  const [idCheckResult, setIdCheckResult] = useState(null); // null | 'available' | 'duplicate'
  const [lastCheckedId, setLastCheckedId] = useState('');

  const idValidNow = idCheckResult === 'available' && lastCheckedId === id && id.length > 0;

  let idFeedback = null;
  if (idCheckResult === 'available' && lastCheckedId === id) {
    idFeedback = { text: '사용 가능한 아이디입니다.', ok: true };
  } else if (idCheckResult === 'duplicate' && lastCheckedId === id) {
    idFeedback = { text: '이미 사용중인 아이디입니다.', ok: false };
  } else if (lastCheckedId && lastCheckedId !== id) {
    idFeedback = { text: '아이디를 다시 확인해주세요.', ok: false };
  }

  let pwFeedback = null;
  if (pw1.length > 0 && pw1.length < 6) {
    pwFeedback = { text: '비밀번호는 6자 이상이어야 합니다.', ok: false };
  } else if (pw2.length > 0 && pw1 !== pw2) {
    pwFeedback = { text: '비밀번호가 일치하지 않습니다.', ok: false };
  } else if (pw2.length > 0 && pw1 === pw2 && pw1.length >= 6) {
    pwFeedback = { text: '비밀번호가 일치합니다.', ok: true };
  }

  const pwValid = pw1.length >= 6 && pw1 === pw2;
  const canProceed = idValidNow && pwValid;

  const onCheckId = () => {
    if (!id) return;
    // 프로토타입: "admin"만 중복으로 시뮬레이션
    const result = id.trim().toLowerCase() === 'admin' ? 'duplicate' : 'available';
    setIdCheckResult(result);
    setLastCheckedId(id);
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <View style={styles.logoBadge}>
          <CareIcon size={18} />
        </View>
        <Text style={styles.logo}>선·퀘</Text>
      </View>

      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        <View>
          <Text style={styles.title}>계정 정보를{'\n'}입력해 주세요</Text>
          <Text style={styles.stepLabel}>2단계 · 계정정보</Text>
        </View>

        <View style={{ gap: 8 }}>
          <View style={styles.idRow}>
            <TextInput
              style={styles.idInput}
              placeholder="아이디 (영문, 숫자 4~16자)"
              placeholderTextColor={COLORS.inkMuted48}
              value={id}
              onChangeText={setId}
              autoCapitalize="none"
            />
            <TouchableOpacity style={styles.checkButton} onPress={onCheckId}>
              <Text style={styles.checkButtonText}>중복확인</Text>
            </TouchableOpacity>
          </View>
          {idFeedback && (
            <Text style={[styles.feedback, { color: idFeedback.ok ? COLORS.success : COLORS.error }]}>
              {idFeedback.text}
            </Text>
          )}
        </View>

        <View style={{ gap: 10 }}>
          <TextInput
            style={styles.input}
            placeholder="비밀번호 (6자 이상)"
            placeholderTextColor={COLORS.inkMuted48}
            secureTextEntry
            value={pw1}
            onChangeText={setPw1}
          />
          <TextInput
            style={styles.input}
            placeholder="비밀번호 확인"
            placeholderTextColor={COLORS.inkMuted48}
            secureTextEntry
            value={pw2}
            onChangeText={setPw2}
          />
          {pwFeedback && (
            <Text style={[styles.feedback, { color: pwFeedback.ok ? COLORS.success : COLORS.error }]}>
              {pwFeedback.text}
            </Text>
          )}
        </View>
      </ScrollView>

      <View style={styles.footer}>
        <TouchableOpacity
          disabled={!canProceed}
          activeOpacity={0.95}
          onPress={() => navigation.navigate('SignupProfile')}
          style={[styles.nextButton, { backgroundColor: canProceed ? COLORS.primary : COLORS.hairline }]}
        >
          <Text style={[styles.nextButtonText, { color: canProceed ? COLORS.canvas : COLORS.inkMuted48 }]}>
            다음
          </Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

