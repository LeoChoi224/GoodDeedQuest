// 32-TeamDetail.js — React Native (Expo) 팀 상세 (방장/팀원 리스트) + 유저 초대 이용불가 팝업
// 선행퀘스트 / 스토리보드 32·34번 기준(34번 "유저 초대 이용 불가 팝업"은 이 화면의 모달로 통합)

import React, { useState } from 'react';
import { View, Text, TouchableOpacity, ScrollView, Modal, Pressable, StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { ChevronLeft, X, UserPlus } from 'lucide-react-native';

import { COLORS } from '../../../shared/디자인/tokens';
import { CareIcon, GreenGradientBG } from '../../../shared/기능/components';
import { styles } from '../디자인/TeamDetail.styles';

const MEMBERS = [
  { userId: '@min_kindness', initial: '민', color: COLORS.mint, isHost: true },
  { userId: '@haneul_92', initial: '하', color: COLORS.gold, isHost: false },
  { userId: '@doyoon_j', initial: '도', color: COLORS.primary, isHost: false },
  { userId: '@soo_bright', initial: '수', color: '#7AA9D1', isHost: false },
  { userId: '@jiwoo_k', initial: '지', color: '#D18F7A', isHost: false },
];

// 로그인한 내 계정이 방장인지 여부 데모용 플래그 — 실제로는 로그인 유저와 host 비교
const I_AM_HOST = false;

export default function TeamDetailScreen({ navigation, route }) {
  const roomName = route?.params?.roomName ?? '저녁마다 산책 인증';
  const category = route?.params?.category ?? '봉사';
  const description = '평일 저녁 8시, 동네를 산책하며 서로 인증샷을 나눠요. 편하게 참여하고 꾸준히 이어가는 게 목표예요.';
  const maxMembers = 8;
  const memberCount = MEMBERS.length;
  const host = MEMBERS.find((m) => m.isHost) || MEMBERS[0];

  const [joined, setJoined] = useState(false);
  const [showInviteBlocked, setShowInviteBlocked] = useState(false);
  const isFull = memberCount >= maxMembers;
  const canJoin = !joined && !isFull;
  let joinLabel = '참여하기';
  if (joined) joinLabel = '참여 중';
  else if (isFull) joinLabel = '정원 마감';

  const onInvitePress = () => {
    if (I_AM_HOST) navigation.navigate('UserRecommend');
    else setShowInviteBlocked(true);
  };

  return (
    <GreenGradientBG>
      <SafeAreaView style={{ flex: 1, backgroundColor: 'transparent' }}>
        <View style={styles.header}>
          <TouchableOpacity onPress={() => navigation.navigate('RoomFind')} hitSlop={10} style={{ padding: 4 }}>
            <ChevronLeft size={22} color={COLORS.ink} />
          </TouchableOpacity>
          <View style={styles.logoBadge}>
            <CareIcon size={18} />
          </View>
          <Text style={styles.logo}>선·퀘</Text>
        </View>

        <ScrollView contentContainerStyle={styles.content}>
          <View style={styles.teamCard}>
            <View style={styles.categoryTag}>
              <Text style={styles.categoryTagText}>{category}</Text>
            </View>
            <Text style={styles.teamName}>{roomName}</Text>
            <Text style={styles.teamMemberCount}>
              {memberCount}/{maxMembers}명 참여 중
            </Text>
          </View>

          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 10 }}>
            <View style={[styles.avatar, { backgroundColor: host.color }]}>
              <Text style={styles.avatarText}>{host.initial}</Text>
            </View>
            <View>
              <Text style={styles.hostId}>{host.userId}</Text>
              <Text style={styles.hostLabel}>방장</Text>
            </View>
          </View>

          <View style={{ gap: 6 }}>
            <Text style={styles.sectionLabel}>방 소개</Text>
            <Text style={styles.description}>{description}</Text>
          </View>

          <View style={{ gap: 10 }}>
            <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}>
              <Text style={styles.sectionLabel}>멤버 ({memberCount})</Text>
              <TouchableOpacity style={styles.inviteButton} onPress={onInvitePress}>
                <UserPlus size={14} color={COLORS.primary} />
                <Text style={styles.inviteButtonText}>초대하기</Text>
              </TouchableOpacity>
            </View>
            <View>
              {MEMBERS.map((m) => (
                <View key={m.userId} style={styles.memberRow}>
                  <View style={[styles.avatar, { width: 32, height: 32, backgroundColor: m.color }]}>
                    <Text style={[styles.avatarText, { fontSize: 12 }]}>{m.initial}</Text>
                  </View>
                  <Text style={styles.memberId}>{m.userId}</Text>
                  {m.isHost && (
                    <View style={styles.hostTag}>
                      <Text style={styles.hostTagText}>방장</Text>
                    </View>
                  )}
                </View>
              ))}
            </View>
          </View>
        </ScrollView>

        <View style={styles.footer}>
          <TouchableOpacity
            disabled={!canJoin}
            style={[styles.joinButton, { backgroundColor: canJoin ? COLORS.primary : COLORS.hairline }]}
            onPress={() => canJoin && setJoined(true)}
          >
            <Text style={[styles.joinButtonText, { color: canJoin ? '#fff' : COLORS.inkMuted48 }]}>{joinLabel}</Text>
          </TouchableOpacity>
        </View>

        {/* 유저 초대 이용 불가 팝업 (방장이 아닐 때) */}
        <Modal statusBarTranslucent visible={showInviteBlocked} transparent animationType="fade" onRequestClose={() => setShowInviteBlocked(false)}>
          <View style={styles.blockOverlay}>
            <Pressable style={StyleSheet.absoluteFill} onPress={() => setShowInviteBlocked(false)} />
            <View style={styles.blockCard}>
              <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}>
                <Text style={styles.blockTitle}>초대 권한이 없어요</Text>
                <TouchableOpacity onPress={() => setShowInviteBlocked(false)} hitSlop={8}>
                  <X size={18} color={COLORS.inkMuted48} />
                </TouchableOpacity>
              </View>
              <Text style={styles.blockDesc}>팀원 초대는 방장만 할 수 있어요. 방장에게 초대를 요청해보세요.</Text>
              <TouchableOpacity style={styles.blockOkButton} onPress={() => setShowInviteBlocked(false)}>
                <Text style={styles.blockOkText}>확인</Text>
              </TouchableOpacity>
            </View>
          </View>
        </Modal>
      </SafeAreaView>
    </GreenGradientBG>
  );
}

