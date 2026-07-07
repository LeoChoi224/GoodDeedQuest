// SignupProfileScreen.js — React Native (Expo) 회원가입 3단계: 프로필
// 선행퀘스트 / 스토리보드 9번 기준

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

import { COLORS } from '../디자인/SignupProfileScreen.styles';
import { styles } from '../디자인/SignupProfileScreen.styles';

const CATEGORY_LABELS = ['봉사', '환경', '나눔', '동물', '지역사회', '기타'];
const TIME_SLOT_LABELS = ['오전 (06-12시)', '오후 (12-18시)', '저녁 (18-24시)', '새벽 (00-06시)'];

function CareIcon({ size = 18 }) {
  return (
    <Svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth={1.7} strokeLinecap="round" strokeLinejoin="round">
      <Path d="M12 6.8c-.9-1.6-3-1.8-4.1-.4-.9 1.1-.7 2.7.4 3.7L12 13l3.7-2.9c1.1-1 1.3-2.6.4-3.7-1.1-1.4-3.2-1.2-4.1.4Z" />
      <Path d="M4.3 13.2c0 3.2 2.9 5.9 6.4 6.3" />
      <Path d="M19.7 13.2c0 3.2-2.9 5.9-6.4 6.3" />
    </Svg>
  );
}

export default function SignupProfileScreen({ navigation }) {
  const [nickname, setNickname] = useState('');
  const [birthdate, setBirthdate] = useState('');
  const [nicknameCheckResult, setNicknameCheckResult] = useState(null); // null | 'available' | 'duplicate'
  const [lastCheckedNickname, setLastCheckedNickname] = useState('');
  const [selectedCategories, setSelectedCategories] = useState([]);
  const [timeSlot, setTimeSlot] = useState(null);

  const nicknameValidNow = nicknameCheckResult === 'available' && lastCheckedNickname === nickname && nickname.length > 0;

  let nicknameFeedback = null;
  if (nicknameCheckResult === 'available' && lastCheckedNickname === nickname) {
    nicknameFeedback = { text: '사용 가능한 닉네임입니다.', ok: true };
  } else if (nicknameCheckResult === 'duplicate' && lastCheckedNickname === nickname) {
    nicknameFeedback = { text: '이미 사용중인 닉네임입니다.', ok: false };
  } else if (lastCheckedNickname && lastCheckedNickname !== nickname) {
    nicknameFeedback = { text: '닉네임을 다시 확인해주세요.', ok: false };
  }

  const onCheckNickname = () => {
    if (!nickname) return;
    // 프로토타입: "관리자"만 중복으로 시뮬레이션
    const result = nickname.trim() === '관리자' ? 'duplicate' : 'available';
    setNicknameCheckResult(result);
    setLastCheckedNickname(nickname);
  };

  const toggleCategory = (label) => {
    setSelectedCategories((prev) =>
      prev.includes(label) ? prev.filter((c) => c !== label) : [...prev, label]
    );
  };

  const onSelectTimeSlot = (label) => {
    setTimeSlot((prev) => (prev === label ? null : label));
  };

  const birthdateValid = /^[0-9]{8}$/.test(birthdate.trim());
  const canProceed = nicknameValidNow && birthdateValid && selectedCategories.length > 0;

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
          <Text style={styles.title}>프로필을{'\n'}입력해 주세요</Text>
          <Text style={styles.stepLabel}>3단계 · 프로필</Text>
        </View>

        <View style={{ gap: 8 }}>
          <View style={styles.idRow}>
            <TextInput
              style={styles.idInput}
              placeholder="닉네임 (2~12자)"
              placeholderTextColor={COLORS.inkMuted48}
              value={nickname}
              onChangeText={setNickname}
            />
            <TouchableOpacity style={styles.checkButton} onPress={onCheckNickname}>
              <Text style={styles.checkButtonText}>중복확인</Text>
            </TouchableOpacity>
          </View>
          {nicknameFeedback && (
            <Text style={[styles.feedback, { color: nicknameFeedback.ok ? COLORS.success : COLORS.error }]}>
              {nicknameFeedback.text}
            </Text>
          )}
        </View>

        <TextInput
          style={styles.input}
          placeholder="생년월일 (예: 20000101)"
          placeholderTextColor={COLORS.inkMuted48}
          keyboardType="number-pad"
          value={birthdate}
          onChangeText={setBirthdate}
        />

        <View style={{ gap: 10 }}>
          <Text style={styles.sectionLabel}>주로 활동하는 시간대</Text>
          <View style={styles.grid}>
            {TIME_SLOT_LABELS.map((label) => {
              const selected = timeSlot === label;
              return (
                <TouchableOpacity
                  key={label}
                  activeOpacity={0.9}
                  onPress={() => onSelectTimeSlot(label)}
                  style={[
                    styles.chip,
                    {
                      backgroundColor: selected ? COLORS.primary : COLORS.parchment,
                      borderColor: selected ? COLORS.primary : COLORS.hairline,
                    },
                  ]}
                >
                  <Text style={{ color: selected ? COLORS.canvas : COLORS.ink, fontSize: 14 }}>{label}</Text>
                </TouchableOpacity>
              );
            })}
          </View>
        </View>

        <View style={{ gap: 10 }}>
          <Text style={styles.sectionLabel}>선호 카테고리 (중복 선택 가능)</Text>
          <View style={styles.grid}>
            {CATEGORY_LABELS.map((label) => {
              const selected = selectedCategories.includes(label);
              return (
                <TouchableOpacity
                  key={label}
                  activeOpacity={0.9}
                  onPress={() => toggleCategory(label)}
                  style={[
                    styles.chip,
                    {
                      backgroundColor: selected ? COLORS.primary : COLORS.parchment,
                      borderColor: selected ? COLORS.primary : COLORS.hairline,
                    },
                  ]}
                >
                  <Text style={{ color: selected ? COLORS.canvas : COLORS.ink, fontSize: 15 }}>{label}</Text>
                </TouchableOpacity>
              );
            })}
          </View>
        </View>
      </ScrollView>

      <View style={styles.footer}>
        <TouchableOpacity
          disabled={!canProceed}
          activeOpacity={0.95}
          onPress={() => navigation.navigate('SignupComplete')}
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

