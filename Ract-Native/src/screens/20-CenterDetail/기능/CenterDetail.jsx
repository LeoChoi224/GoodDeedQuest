// 20-CenterDetail.js — React Native (Expo) 봉사센터 상세정보
// 선행퀘스트 / 스토리보드 20번 기준
// 경로: 내 주변(18) 핀 카드 "자세히 보기" -> 이 화면. 신청하기 -> (실제로는 VMS 외부 연결, 데모는 토스트)

import React, { useState, useRef } from 'react';
import { View, Text, TouchableOpacity, ScrollView } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { ChevronLeft, Calendar, MapPin, Target } from 'lucide-react-native';

import { COLORS } from '../../../shared/디자인/tokens';
import { CareIcon, BottomNav, HamburgerMenu, HamburgerButton } from '../../../shared/기능/components';
import { styles } from '../디자인/CenterDetail.styles';

const CENTER = {
  name: '행복나눔 복지관',
  address: '대전광역시 중구 행복로 12',
  period: '2025.07.15 ~ 2025.08.30',
  place: '행복나눔 복지관 1층 로비',
  target: '지역 어르신 및 취약계층 20명',
  desc: '거동이 불편한 어르신들을 위한 말벗, 식사보조, 생필품 전달 봉사입니다. 준비물은 없으며 활동복은 현장에서 대여 가능합니다.',
};

export default function CenterDetailScreen({ navigation }) {
  const [menuVisible, setMenuVisible] = useState(false);
  const [showToast, setShowToast] = useState(false);
  const toastTimer = useRef(null);

  const onApply = () => {
    clearTimeout(toastTimer.current);
    setShowToast(true);
    toastTimer.current = setTimeout(() => setShowToast(false), 2200);
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.navigate('Nearby')} hitSlop={10} style={{ padding: 4 }}>
          <ChevronLeft size={22} color={COLORS.ink} />
        </TouchableOpacity>
        <View style={styles.logoBadge}>
          <CareIcon size={18} />
        </View>
        <Text style={styles.logo}>선·퀘</Text>
        <View style={{ flex: 1 }} />
        <HamburgerButton onPress={() => setMenuVisible(true)} />
      </View>

      <ScrollView contentContainerStyle={styles.content}>
        <View style={{ gap: 4 }}>
          <Text style={styles.centerName}>{CENTER.name}</Text>
          <Text style={styles.centerAddress}>{CENTER.address}</Text>
        </View>

        <View style={styles.miniMap}>
          <View style={styles.pinWrap}>
            <View style={styles.pin}>
              <Text style={{ color: '#fff', fontSize: 16, transform: [{ rotate: '-45deg' }] }}>⌂</Text>
            </View>
          </View>
        </View>

        <View style={styles.infoCard}>
          <InfoRow Icon={Calendar} label="활동기간" value={CENTER.period} />
          <InfoRow Icon={MapPin} label="봉사장소" value={CENTER.place} />
          <InfoRow Icon={Target} label="봉사대상" value={CENTER.target} />
          <View style={styles.divider} />
          <View style={{ gap: 4 }}>
            <Text style={styles.infoLabel}>활동 설명</Text>
            <Text style={styles.infoDesc}>{CENTER.desc}</Text>
          </View>
        </View>
      </ScrollView>

      <View style={styles.footer}>
        <TouchableOpacity style={styles.applyButton} activeOpacity={0.9} onPress={onApply}>
          <Text style={styles.applyButtonText}>신청하기</Text>
        </TouchableOpacity>
      </View>

      <BottomNav navigation={navigation} active="map" />
      <HamburgerMenu visible={menuVisible} onClose={() => setMenuVisible(false)} navigation={navigation} />

      {showToast && (
        <View style={styles.toast}>
          <Text style={styles.toastText}>VMS 신청 페이지로 이동합니다</Text>
        </View>
      )}
    </SafeAreaView>
  );
}

function InfoRow({ Icon, label, value }) {
  return (
    <View style={{ flexDirection: 'row', alignItems: 'flex-start', gap: 12 }}>
      <View style={styles.infoIconBadge}>
        <Icon size={17} color={COLORS.primary} strokeWidth={1.8} />
      </View>
      <View style={{ gap: 2, minWidth: 0 }}>
        <Text style={styles.infoLabel}>{label}</Text>
        <Text style={styles.infoValue}>{value}</Text>
      </View>
    </View>
  );
}

