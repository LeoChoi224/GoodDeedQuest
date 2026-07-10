// SignupTermsScreen.js — React Native (Expo) 회원가입 1단계: 약관동의
// 선행퀘스트 / 스토리보드 7번 기준

import React, { useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  Modal,
  Pressable,
  ScrollView,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Svg, { Path } from 'react-native-svg';

import { COLORS } from '../디자인/SignupTermsScreen.styles';
import { styles } from '../디자인/SignupTermsScreen.styles';

const TERMS = {
  1: {
    title: '[필수] 서비스 이용약관',
    body: '(약관 전문 placeholder)\n\n제1조 (목적)\n이 약관은 선행퀘스트 서비스 이용에 관한 조건을 규정합니다.\n\n실제 약관 문구는 추후 법무 검토 후 반영 예정입니다.',
  },
  2: {
    title: '[필수] 개인정보 수집 및 이용동의',
    body: '(약관 전문 placeholder)\n\n수집 항목: 이메일, 닉네임, 위치 정보 등\n수집 목적: 서비스 제공 및 퀘스트 인증\n\n실제 약관 문구는 추후 법무 검토 후 반영 예정입니다.',
  },
  3: {
    title: '[선택] 마케팅 정보 수신 동의',
    body: '(약관 전문 placeholder)\n\n이벤트 및 혜택 정보를 이메일/푸시로 받아보실 수 있습니다.\n\n실제 약관 문구는 추후 법무 검토 후 반영 예정입니다.',
  },
};

function CareIcon({ size = 18 }) {
  return (
    <Svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth={1.7} strokeLinecap="round" strokeLinejoin="round">
      <Path d="M12 6.8c-.9-1.6-3-1.8-4.1-.4-.9 1.1-.7 2.7.4 3.7L12 13l3.7-2.9c1.1-1 1.3-2.6.4-3.7-1.1-1.4-3.2-1.2-4.1.4Z" />
      <Path d="M4.3 13.2c0 3.2 2.9 5.9 6.4 6.3" />
      <Path d="M19.7 13.2c0 3.2-2.9 5.9-6.4 6.3" />
    </Svg>
  );
}

function CheckBox({ checked, onPress, size = 22 }) {
  return (
    <TouchableOpacity
      onPress={onPress}
      style={{
        width: size, height: size, borderRadius: 6,
        alignItems: 'center', justifyContent: 'center',
        backgroundColor: checked ? COLORS.primary : COLORS.canvas,
        borderWidth: checked ? 0 : 1.5,
        borderColor: COLORS.hairline,
      }}
    >
      {checked && (
        <Svg width={12} height={12} viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth={3} strokeLinecap="round" strokeLinejoin="round">
          <Path d="M20 6 9 17l-5-5" />
        </Svg>
      )}
    </TouchableOpacity>
  );
}

export default function SignupTermsScreen({ navigation }) {
  const [agree1, setAgree1] = useState(false);
  const [agree2, setAgree2] = useState(false);
  const [agree3, setAgree3] = useState(false);
  const [viewingIndex, setViewingIndex] = useState(null);

  const allAgreed = agree1 && agree2 && agree3;
  const canProceed = agree1 && agree2; // 필수 항목만 체크되면 진행 가능

  const toggleAll = () => {
    const next = !allAgreed;
    setAgree1(next);
    setAgree2(next);
    setAgree3(next);
  };

  return (
    <SafeAreaView style={styles.container}>
      {/* 헤더 / 로고 */}
      <View style={styles.header}>
        <View style={styles.logoBadge}>
          <CareIcon size={18} />
        </View>
        <Text style={styles.logo}>선·퀘</Text>
      </View>

      <ScrollView contentContainerStyle={styles.content}>
        <Text style={styles.title}>약관에{'\n'}동의해 주세요</Text>

        <TouchableOpacity style={styles.allAgreeRow} activeOpacity={0.9} onPress={toggleAll}>
          <CheckBox checked={allAgreed} onPress={toggleAll} />
          <Text style={styles.allAgreeText}>전체 동의합니다</Text>
        </TouchableOpacity>

        <View style={styles.divider} />

        <View style={{ gap: 4 }}>
          <TermRow
            label="[필수] 서비스 이용약관"
            checked={agree1}
            onToggle={() => setAgree1(!agree1)}
            onView={() => setViewingIndex(1)}
          />
          <TermRow
            label="[필수] 개인정보 수집 및 이용동의"
            checked={agree2}
            onToggle={() => setAgree2(!agree2)}
            onView={() => setViewingIndex(2)}
          />
          <TermRow
            label="[선택] 마케팅 정보 수신 동의"
            checked={agree3}
            onToggle={() => setAgree3(!agree3)}
            onView={() => setViewingIndex(3)}
          />
        </View>
      </ScrollView>

      <View style={styles.footer}>
        <TouchableOpacity
          disabled={!canProceed}
          activeOpacity={0.95}
          onPress={() => navigation.navigate('SignupAccount')}
          style={[styles.nextButton, { backgroundColor: canProceed ? COLORS.primary : COLORS.hairline }]}
        >
          <Text style={[styles.nextButtonText, { color: canProceed ? COLORS.canvas : COLORS.inkMuted48 }]}>
            다음
          </Text>
        </TouchableOpacity>
      </View>

      {/* 약관 상세 팝업 (중앙 모달) */}
      <Modal statusBarTranslucent visible={viewingIndex !== null} transparent animationType="fade">
        <View style={styles.modalOverlay}>
          <View style={styles.modalCard}>
            <View style={styles.sheetHeader}>
              <Text style={styles.sheetTitle}>{viewingIndex && TERMS[viewingIndex].title}</Text>
              <Pressable onPress={() => setViewingIndex(null)}>
                <Text style={{ fontSize: 20, color: COLORS.inkMuted48 }}>✕</Text>
              </Pressable>
            </View>
            <ScrollView>
              <Text style={styles.sheetBody}>{viewingIndex && TERMS[viewingIndex].body}</Text>
            </ScrollView>
            <TouchableOpacity style={styles.modalButton} onPress={() => setViewingIndex(null)}>
              <Text style={styles.modalButtonText}>확인</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

function TermRow({ label, checked, onToggle, onView }) {
  return (
    <View style={styles.termRow}>
      <CheckBox checked={checked} onPress={onToggle} />
      <TouchableOpacity style={{ flex: 1 }} onPress={onToggle}>
        <Text style={styles.termLabel}>{label}</Text>
      </TouchableOpacity>
      <TouchableOpacity onPress={onView}>
        <Text style={styles.termView}>보기</Text>
      </TouchableOpacity>
    </View>
  );
}

