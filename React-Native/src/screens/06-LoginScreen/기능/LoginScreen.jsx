// LoginScreen.js — React Native (Expo) 로그인 페이지
// 선행퀘스트 / 스토리보드 6번 기준
// 팔레트: #033236(딥틸, 메인 CTA) / #FFFFFF(캔버스) / #F6F6F6(서브 배경, 인풋 필)
// 타이포/spacing/radius 문법은 Apple Web Design System 토큰을 RN 상수로 이식

import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  Modal,
  Pressable,
  } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
// 아이콘: Apple Web Design System은 SF Symbols 대체로 Lucide 계열 사용을 권장.
// Expo 프로젝트에서는 lucide-react-native 사용 (npm i lucide-react-native react-native-svg)
import { Users, MapPin, Home, Coins, User, MessageCircle } from 'lucide-react-native';
import Svg, { Path } from 'react-native-svg';

import { COLORS, RADIUS, TYPE } from '../디자인/LoginScreen.styles';
import { styles } from '../디자인/LoginScreen.styles';

// 봉사(하트를 감싸는 두 손) 아이콘 — 앱 로고 마크
function CareIcon({ size = 18 }) {
  return (
    <Svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth={1.7} strokeLinecap="round" strokeLinejoin="round">
      <Path d="M12 6.8c-.9-1.6-3-1.8-4.1-.4-.9 1.1-.7 2.7.4 3.7L12 13l3.7-2.9c1.1-1 1.3-2.6.4-3.7-1.1-1.4-3.2-1.2-4.1.4Z" />
      <Path d="M4.3 13.2c0 3.2 2.9 5.9 6.4 6.3" />
      <Path d="M19.7 13.2c0 3.2-2.9 5.9-6.4 6.3" />
    </Svg>
  );
}

// 구글 멀티컬러 "G" 마크 (react-native-svg)
function GoogleGIcon({ size = 18 }) {
  return (
    <Svg width={size} height={size} viewBox="0 0 18 18">
      <Path fill="#4285F4" d="M17.64 9.2c0-.64-.06-1.25-.16-1.84H9v3.48h4.84c-.21 1.13-.85 2.09-1.81 2.73v2.27h2.92c1.71-1.57 2.69-3.88 2.69-6.64Z" />
      <Path fill="#34A853" d="M9 18c2.43 0 4.47-.8 5.96-2.18l-2.92-2.27c-.81.54-1.84.86-3.04.86-2.34 0-4.32-1.58-5.03-3.7H.96v2.34C2.44 15.98 5.48 18 9 18Z" />
      <Path fill="#FBBC05" d="M3.97 10.71a5.4 5.4 0 0 1 0-3.42V4.95H.96a9 9 0 0 0 0 8.1l3.01-2.34Z" />
      <Path fill="#EA4335" d="M9 3.58c1.32 0 2.51.46 3.44 1.35l2.59-2.59C13.46.9 11.43 0 9 0 5.48 0 2.44 2.02.96 4.95l3.01 2.34C4.68 5.16 6.66 3.58 9 3.58Z" />
    </Svg>
  );
}

export default function LoginScreen({ navigation }) {
  const [id, setId] = useState('');
  const [password, setPassword] = useState('');
  const [showError, setShowError] = useState(false);

  const handleLogin = () => {
    // TODO: 실제 인증 API 연동. 현재는 데모용으로 항상 실패 팝업 표시.
    setShowError(true);
  };

  return (
    <SafeAreaView style={styles.container}>
      {/* 헤더 / 로고: 봉사(하트+두 손) 아이콘 + 축약 워드마크 */}
      <View style={styles.header}>
        <View style={styles.logoBadge}>
          <CareIcon size={18} />
        </View>
        <Text style={styles.logo}>선·퀘</Text>
      </View>

      {/* 본문 */}
      <View style={styles.content}>
        <Text style={styles.title}>로그인</Text>

        <View style={{ gap: 12 }}>
          <TextInput
            style={styles.input}
            placeholder="아이디"
            placeholderTextColor={COLORS.inkMuted48}
            value={id}
            onChangeText={setId}
            autoCapitalize="none"
          />
          <TextInput
            style={styles.input}
            placeholder="비밀번호"
            placeholderTextColor={COLORS.inkMuted48}
            value={password}
            onChangeText={setPassword}
            secureTextEntry
          />

          <TouchableOpacity
            style={styles.primaryButton}
            activeOpacity={0.95}
            onPress={handleLogin}
          >
            <Text style={styles.primaryButtonText}>로그인</Text>
          </TouchableOpacity>

          <TouchableOpacity
            onPress={() => navigation.navigate('SignupTerms')}
            style={{ alignSelf: 'center', marginTop: 4 }}
          >
            <Text style={styles.signupLink}>회원가입</Text>
          </TouchableOpacity>
        </View>

        <View style={{ gap: 10, marginTop: 32 }}>
          <TouchableOpacity
            style={[styles.oauthButton, { backgroundColor: COLORS.kakao, flexDirection: 'row', gap: 8 }]}
            activeOpacity={0.95}
            onPress={() => setShowError(true)}
          >
            <MessageCircle size={18} color={COLORS.kakaoText} fill={COLORS.kakaoText} strokeWidth={0} />
            <Text style={[styles.oauthButtonText, { color: COLORS.kakaoText }]}>
              카카오로 시작하기
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.oauthButton, { backgroundColor: COLORS.canvas, borderWidth: 1, borderColor: COLORS.hairline, flexDirection: 'row', gap: 8 }]}
            activeOpacity={0.95}
            onPress={() => setShowError(true)}
          >
            <GoogleGIcon size={18} />
            <Text style={[styles.oauthButtonText, { color: COLORS.ink }]}>
              구글로 시작하기
            </Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* 하단 네비바 (5탭 고정) */}
      <View style={styles.bottomNav}>
        <NavItem Icon={Users} label="커뮤니티" onPress={() => navigation.navigate('Community')} />
        <NavItem Icon={MapPin} label="지도" onPress={() => navigation.navigate('Map')} />
        <NavItem Icon={Home} label="홈" onPress={() => navigation.navigate('Main')} />
        <NavItem Icon={Coins} label="상점" onPress={() => navigation.navigate('Store')} />
        <NavItem Icon={User} label="마이" onPress={() => navigation.navigate('MyPage')} />
      </View>

      {/* 로그인 실패 팝업 */}
      <Modal statusBarTranslucent visible={showError} transparent animationType="fade">
        <View style={styles.modalOverlay}>
          <View style={styles.modalCard}>
            <Text style={styles.modalTitle}>회원정보가 틀렸습니다</Text>
            <Text style={styles.modalSubtitle}>아이디와 비밀번호를 다시 확인해주세요.</Text>
            <Pressable style={styles.modalButton} onPress={() => setShowError(false)}>
              <Text style={styles.modalButtonText}>확인</Text>
            </Pressable>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

function NavItem({ Icon, label, onPress }) {
  return (
    <TouchableOpacity style={styles.navItem} onPress={onPress}>
      <Icon size={22} color={COLORS.inkMuted48} strokeWidth={1.6} />
      <Text style={styles.navLabel}>{label}</Text>
    </TouchableOpacity>
  );
}

