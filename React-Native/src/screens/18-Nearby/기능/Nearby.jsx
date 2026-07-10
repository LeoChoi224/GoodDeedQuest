// 18-Nearby.js — React Native (Expo) 내 주변 페이지 (+핀 클릭 팝업 상태 포함)
// 선행퀘스트 / 스토리보드 18·19번 기준 (19번은 18번의 "핀 클릭해 팝업이 뜬" 상태와 동일 화면)
// 3km 반경 지도(일러스트) + 퀘스트/봉사센터 핀 토글 + 핀 클릭 시 하단 팝업 카드

import React, { useState } from 'react';
import { View, Text, TouchableOpacity } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { X } from 'lucide-react-native';

import { COLORS } from '../../../shared/디자인/tokens';
import { CareIcon, BottomNav, HamburgerMenu, HamburgerButton } from '../../../shared/기능/components';
import { styles } from '../디자인/Nearby.styles';

const QUEST_PINS = [
  { id: 'q1', title: '동네 어르신 짐 들어드리기', location: '행복빌라 앞', difficulty: '쉬움', exp: 20, point: 30, x: '22%', y: '30%' },
  { id: 'q2', title: '유기동물 보호소 봉사', location: '사랑동물보호센터', difficulty: '보통', exp: 40, point: 60, x: '64%', y: '20%' },
  { id: 'q3', title: '공원 쓰레기 줍기', location: '시민공원', difficulty: '쉬움', exp: 15, point: 20, x: '46%', y: '56%' },
  { id: 'q4', title: '헌혈하기', location: '중앙헌혈의집', difficulty: '보통', exp: 30, point: 50, x: '80%', y: '68%' },
  { id: 'q5', title: '횡단보도 교통 봉사', location: '초록초등학교 앞', difficulty: '어려움', exp: 18, point: 25, x: '16%', y: '80%' },
];

const CENTER_PINS = [
  { id: 'c1', name: '행복나눔 복지관', address: '중구 행복로 12', distance: '0.4km', desc: '노인 및 취약계층 지원 봉사를 상시 모집하고 있어요.', x: '28%', y: '22%' },
  { id: 'c2', name: '사랑동물보호센터', address: '서구 사랑길 8', distance: '1.2km', desc: '유기동물 보호 및 산책 봉사를 진행합니다.', x: '64%', y: '20%' },
  { id: 'c3', name: '푸른급식소', address: '남구 나눔길 3', distance: '0.8km', desc: '무료 급식 준비와 배식을 돕는 봉사입니다.', x: '50%', y: '52%' },
  { id: 'c4', name: '초록환경센터', address: '북구 초록로 20', distance: '2.1km', desc: '지역 환경 정화 캠페인을 운영해요.', x: '78%', y: '70%' },
];

function PinMarker({ x, y, bg, shadowColor, onPress, children }) {
  return (
    <TouchableOpacity onPress={onPress} style={{ position: 'absolute', left: x, top: y, transform: [{ translateX: -17 }, { translateY: -34 }] }}>
      <View style={[styles.pin, { backgroundColor: bg, shadowColor }]}>
        <View style={{ transform: [{ rotate: '-45deg' }] }}>{children}</View>
      </View>
    </TouchableOpacity>
  );
}

export default function NearbyScreen({ navigation }) {
  const [menuVisible, setMenuVisible] = useState(false);
  const [activeTab, setActiveTab] = useState('quest');
  const [selectedQuestId, setSelectedQuestId] = useState(null);
  const [selectedCenterId, setSelectedCenterId] = useState(null);

  const selectedQuest = selectedQuestId ? QUEST_PINS.find((p) => p.id === selectedQuestId) : null;
  const selectedCenter = selectedCenterId ? CENTER_PINS.find((p) => p.id === selectedCenterId) : null;

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <View style={styles.logoBadge}>
          <CareIcon size={18} />
        </View>
        <Text style={styles.logo}>선·퀘</Text>
        <View style={{ flex: 1 }} />
        <HamburgerButton onPress={() => setMenuVisible(true)} />
      </View>

      <View style={styles.mapArea}>
        {/* 도로/블록 일러스트 (간이) */}
        <View style={[styles.roadH, { top: '14%' }]} />
        <View style={[styles.roadH, { top: '44%', height: 20 }]} />
        <View style={[styles.roadH, { top: '74%', height: 14 }]} />
        <View style={[styles.roadV, { left: '20%' }]} />
        <View style={[styles.roadV, { left: '58%', width: 18 }]} />
        <View style={[styles.roadV, { left: '85%', width: 12 }]} />
        <View style={[styles.block, { top: 20, left: 24, width: '15%', height: '11%' }]} />
        <View style={[styles.block, { top: 20, left: '26%', width: '26%', height: '9%' }]} />
        <View style={[styles.blockGreen, { top: 20, right: '6%', width: '16%', height: '12%' }]} />
        <View style={[styles.block, { top: '20%', left: 24, width: '15%', height: '20%' }]} />
        <View style={[styles.block, { top: '22%', left: '26%', width: '26%', height: '18%' }]} />
        <View style={[styles.blockGreen, { top: '48%', left: '26%', width: '26%', height: '22%' }]} />
        <View style={[styles.block, { bottom: 20, left: 24, width: '15%', height: '16%' }]} />
        <View style={[styles.block, { bottom: 20, left: '26%', width: '26%', height: '16%' }]} />
        <View style={[styles.block, { bottom: 20, left: '64%', width: '30%', height: '16%' }]} />

        {activeTab === 'quest' &&
          QUEST_PINS.map((p) => (
            <PinMarker key={p.id} x={p.x} y={p.y} bg={COLORS.primary} shadowColor="rgba(3,50,54,0.3)" onPress={() => setSelectedQuestId(p.id)}>
              <CareIcon size={16} color="#fff" />
            </PinMarker>
          ))}
        {activeTab === 'center' &&
          CENTER_PINS.map((p) => (
            <PinMarker key={p.id} x={p.x} y={p.y} bg={COLORS.gold} shadowColor="rgba(201,162,39,0.35)" onPress={() => setSelectedCenterId(p.id)}>
              <Text style={{ color: '#fff', fontSize: 14 }}>⌂</Text>
            </PinMarker>
          ))}

        {selectedQuest && (
          <View style={styles.popupCard}>
            <View style={{ flexDirection: 'row', alignItems: 'flex-start', gap: 12 }}>
              <View style={styles.popupIcon}>
                <CareIcon size={19} color="#fff" />
              </View>
              <View style={{ flex: 1, minWidth: 0, gap: 4 }}>
                <Text style={styles.popupTitle}>{selectedQuest.title}</Text>
                <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
                  <Text style={styles.popupSub}>{selectedQuest.location}</Text>
                  <Text style={styles.difficultyBadge}>{selectedQuest.difficulty}</Text>
                </View>
              </View>
              <TouchableOpacity onPress={() => setSelectedQuestId(null)} hitSlop={8}>
                <X size={18} color={COLORS.inkMuted48} />
              </TouchableOpacity>
            </View>
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 14, marginTop: 12 }}>
              <View style={{ flexDirection: 'row', gap: 8, flex: 1 }}>
                <View style={styles.rewardPill}>
                  <Text style={styles.rewardPillLabel}>EXP</Text>
                  <Text style={styles.rewardPillValue}>+{selectedQuest.exp}</Text>
                </View>
                <View style={styles.rewardPill}>
                  <Text style={styles.rewardPillLabel}>포인트</Text>
                  <Text style={styles.rewardPillValue}>+{selectedQuest.point}</Text>
                </View>
              </View>
              <TouchableOpacity style={styles.detailButton} onPress={() => navigation.navigate('QuestDetail', { quest: { title: selectedQuest.title, exp: selectedQuest.exp, points: selectedQuest.point } })}>
                <Text style={styles.detailButtonText}>자세히 보기</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}

        {selectedCenter && (
          <View style={styles.popupCard}>
            <View style={{ flexDirection: 'row', alignItems: 'flex-start', gap: 12 }}>
              <View style={[styles.popupIcon, { backgroundColor: COLORS.gold }]}>
                <Text style={{ color: '#fff', fontSize: 16 }}>⌂</Text>
              </View>
              <View style={{ flex: 1, minWidth: 0, gap: 2 }}>
                <Text style={styles.popupTitle}>{selectedCenter.name}</Text>
                <Text style={styles.popupSub}>
                  {selectedCenter.address} · {selectedCenter.distance}
                </Text>
              </View>
              <TouchableOpacity onPress={() => setSelectedCenterId(null)} hitSlop={8}>
                <X size={18} color={COLORS.inkMuted48} />
              </TouchableOpacity>
            </View>
            <Text style={[styles.popupDesc, { marginTop: 10 }]}>{selectedCenter.desc}</Text>
            <TouchableOpacity style={[styles.detailButton, { marginTop: 10, alignSelf: 'flex-start' }]} onPress={() => navigation.navigate('CenterDetail')}>
              <Text style={styles.detailButtonText}>자세히 보기</Text>
            </TouchableOpacity>
          </View>
        )}

        <View style={styles.tabToggleWrap}>
          <View style={styles.tabToggle}>
            <TouchableOpacity
              style={[styles.tabButton, activeTab === 'center' && { backgroundColor: COLORS.primary }]}
              onPress={() => { setActiveTab('center'); setSelectedQuestId(null); }}
            >
              <Text style={[styles.tabButtonText, activeTab === 'center' && { color: '#fff' }]}>봉사센터</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.tabButton, activeTab === 'quest' && { backgroundColor: COLORS.primary }]}
              onPress={() => { setActiveTab('quest'); setSelectedCenterId(null); }}
            >
              <Text style={[styles.tabButtonText, activeTab === 'quest' && { color: '#fff' }]}>퀘스트</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>

      <BottomNav navigation={navigation} active="map" />
      <HamburgerMenu visible={menuVisible} onClose={() => setMenuVisible(false)} navigation={navigation} />
    </SafeAreaView>
  );
}

