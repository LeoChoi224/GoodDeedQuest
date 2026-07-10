// 31-RoomFind.js — React Native (Expo) 방 찾기 (검색/필터 + 비밀번호 팝업)
// 선행퀘스트 / 스토리보드 31번 기준

import React, { useState, useRef } from 'react';
import { View, Text, TextInput, TouchableOpacity, ScrollView, Modal, Pressable, StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { ChevronLeft, Search, Lock, X } from 'lucide-react-native';

import { COLORS } from '../../../shared/디자인/tokens';
import { CareIcon, GreenGradientBG } from '../../../shared/기능/components';
import { styles } from '../디자인/RoomFind.styles';

const FILTER_LABELS = ['전체', '봉사', '환경', '나눔', '동물', '지역사회', '기타'];

const ROOMS = [
  { id: 'r1', name: '저녁마다 산책 인증', category: '봉사', hostId: '@min_kindness', hostInitial: '민', hostColor: COLORS.mint, memberCount: 5, maxMembers: 8, isPrivate: false },
  { id: 'r2', name: '한 달 헌혈 챌린지', category: '나눔', hostId: '@haneul_92', hostInitial: '하', hostColor: COLORS.gold, memberCount: 3, maxMembers: 6, isPrivate: false },
  { id: 'r3', name: '주말 유기동물 봉사단', category: '동물', hostId: '@jiwoo_k', hostInitial: '지', hostColor: '#D18F7A', memberCount: 8, maxMembers: 10, isPrivate: true },
  { id: 'r4', name: '동네 줍깅 모임', category: '환경', hostId: '@soo_bright', hostInitial: '수', hostColor: '#7AA9D1', memberCount: 4, maxMembers: 4, isPrivate: false },
  { id: 'r5', name: '이웃 어르신 돕기', category: '지역사회', hostId: '@bomi_lee', hostInitial: '보', hostColor: '#9B8BD1', memberCount: 2, maxMembers: 6, isPrivate: false },
];

export default function RoomFindScreen({ navigation }) {
  const [query, setQuery] = useState('');
  const [filter, setFilter] = useState('전체');
  const [pwRoom, setPwRoom] = useState(null);
  const [password, setPassword] = useState('');
  const toastTimer = useRef(null);
  const [toast, setToast] = useState('');

  const showToast = (text) => {
    clearTimeout(toastTimer.current);
    setToast(text);
    toastTimer.current = setTimeout(() => setToast(''), 1600);
  };

  const q = query.trim().toLowerCase();
  const filtered = ROOMS.filter((r) => (filter === '전체' || r.category === filter) && (!q || r.name.toLowerCase().includes(q)));

  const onJoin = (room) => {
    const isFull = room.memberCount >= room.maxMembers;
    if (isFull) return;
    if (room.isPrivate) {
      setPwRoom(room);
      setPassword('');
      return;
    }
    navigation.navigate('TeamDetail', { roomName: room.name, category: room.category });
  };

  const onSubmitPassword = () => {
    if (!password.trim()) return;
    setPwRoom(null);
    navigation.navigate('TeamDetail', { roomName: pwRoom.name, category: pwRoom.category });
  };

  return (
    <GreenGradientBG>
      <SafeAreaView style={{ flex: 1, backgroundColor: 'transparent' }}>
        <View style={styles.header}>
          <TouchableOpacity onPress={() => navigation.navigate('TeamChallenge')} hitSlop={10} style={{ padding: 4 }}>
            <ChevronLeft size={22} color={COLORS.ink} />
          </TouchableOpacity>
          <View style={styles.logoBadge}>
            <CareIcon size={18} />
          </View>
          <Text style={styles.logo}>선·퀘</Text>
        </View>

        <View style={styles.searchSection}>
          <Text style={styles.title}>함께할 방을{'\n'}찾아보세요</Text>
          <View style={styles.searchBar}>
            <Search size={17} color={COLORS.inkMuted48} />
            <TextInput style={styles.searchInput} placeholder="방 이름으로 검색" placeholderTextColor={COLORS.inkMuted48} value={query} onChangeText={setQuery} />
          </View>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: 8 }}>
            {FILTER_LABELS.map((label) => {
              const selected = filter === label;
              return (
                <TouchableOpacity key={label} style={[styles.filterChip, selected && styles.filterChipSelected]} onPress={() => setFilter(label)}>
                  <Text style={[styles.filterChipText, selected && styles.filterChipTextSelected]}>{label}</Text>
                </TouchableOpacity>
              );
            })}
          </ScrollView>
        </View>

        <ScrollView contentContainerStyle={styles.list}>
          {filtered.map((room) => {
            const isFull = room.memberCount >= room.maxMembers;
            const joinLabel = isFull ? '정원 마감' : room.isPrivate ? '초대 코드로 참여' : '참여하기';
            return (
              <View key={room.id} style={styles.roomCard}>
                <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
                  <View style={styles.categoryTag}>
                    <Text style={styles.categoryTagText}>{room.category}</Text>
                  </View>
                  {room.isPrivate && <Lock size={13} color={COLORS.inkMuted48} />}
                  <View style={{ flex: 1 }} />
                  <Text style={styles.memberCountText}>
                    {room.memberCount}/{room.maxMembers}명
                  </Text>
                </View>
                <Text style={styles.roomName}>{room.name}</Text>
                <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
                  <View style={[styles.hostAvatar, { backgroundColor: room.hostColor }]}>
                    <Text style={styles.hostAvatarText}>{room.hostInitial}</Text>
                  </View>
                  <Text style={styles.hostId}>{room.hostId}</Text>
                </View>
                <TouchableOpacity
                  style={[styles.joinButton, isFull && { backgroundColor: COLORS.hairline }]}
                  disabled={isFull}
                  onPress={() => onJoin(room)}
                >
                  <Text style={[styles.joinButtonText, isFull && { color: COLORS.inkMuted48 }]}>{joinLabel}</Text>
                </TouchableOpacity>
              </View>
            );
          })}
          {filtered.length === 0 && (
            <View style={{ alignItems: 'center', gap: 8, paddingVertical: 48 }}>
              <Text style={{ fontSize: 14, fontWeight: '600', color: COLORS.inkMuted48 }}>검색 결과가 없어요</Text>
              <Text style={{ fontSize: 12.5, color: COLORS.inkMuted48 }}>다른 검색어나 카테고리로 찾아보세요</Text>
            </View>
          )}
        </ScrollView>

        {!!toast && (
          <View style={styles.toast}>
            <Text style={styles.toastText}>{toast}</Text>
          </View>
        )}

        {/* 비밀번호 팝업 (비공개방) */}
        <Modal statusBarTranslucent visible={!!pwRoom} transparent animationType="fade" onRequestClose={() => setPwRoom(null)}>
          <View style={styles.pwOverlay}>
            <Pressable style={StyleSheet.absoluteFill} onPress={() => setPwRoom(null)} />
            <View style={styles.pwCard}>
              <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}>
                <Text style={styles.pwTitle}>비공개방이에요</Text>
                <TouchableOpacity onPress={() => setPwRoom(null)} hitSlop={8}>
                  <X size={18} color={COLORS.inkMuted48} />
                </TouchableOpacity>
              </View>
              <Text style={styles.pwSubtitle}>{pwRoom?.name}에 참여하려면 초대 코드를 입력해주세요</Text>
              <TextInput
                style={styles.pwInput}
                placeholder="초대 코드 입력"
                placeholderTextColor={COLORS.inkMuted48}
                value={password}
                onChangeText={setPassword}
                secureTextEntry
              />
              <TouchableOpacity style={[styles.pwSubmit, { backgroundColor: password.trim() ? COLORS.primary : COLORS.hairline }]} disabled={!password.trim()} onPress={onSubmitPassword}>
                <Text style={[styles.pwSubmitText, { color: password.trim() ? '#fff' : COLORS.inkMuted48 }]}>참여하기</Text>
              </TouchableOpacity>
            </View>
          </View>
        </Modal>
      </SafeAreaView>
    </GreenGradientBG>
  );
}

