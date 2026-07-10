// 51-AdminUserList.js — React Native (Expo) 유저 목록 (+ 52번 유저 상세 팝업 통합)
// 선행퀘스트 / 스토리보드 51·52번 기준 — 검색/필터 + 하단 시트 상세(경고/정지 처리)

import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, ScrollView, Modal, Pressable } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { ChevronLeft, Search, X, Grid2X2, Users, Flag } from 'lucide-react-native';

import { COLORS } from '../../../shared/디자인/tokens';
import { GreenGradientBG } from '../../../shared/기능/components';
import { AdminHamburgerButton, AdminHamburgerMenu } from '../../../shared/admin/기능/components';
import { styles } from '../디자인/AdminUserList.styles';

const USERS = [
  { id: 'u1', nickname: '민선행', initial: '민', email: 'sunhaeng@gmail.com', joined: '2026-07-05', status: '활성', level: 12, questCount: 84, point: 480 },
  { id: 'u2', nickname: '봉사왕진호', initial: '봉', email: 'jinho.vol@gmail.com', joined: '2026-07-05', status: '활성', level: 9, questCount: 61, point: 320 },
  { id: 'u3', nickname: '따뜻한하루', initial: '따', email: 'warmday@gmail.com', joined: '2026-07-04', status: '활성', level: 7, questCount: 45, point: 210 },
  { id: 'u4', nickname: '선행러너', initial: '선', email: 'goodrunner@gmail.com', joined: '2026-07-04', status: '정지', level: 5, questCount: 22, point: 90 },
  { id: 'u5', nickname: '이웃사랑', initial: '이', email: 'neighborlove@gmail.com', joined: '2026-07-03', status: '활성', level: 15, questCount: 112, point: 640 },
  { id: 'u6', nickname: '초록발걸음', initial: '초', email: 'greensteps@gmail.com', joined: '2026-07-02', status: '활성', level: 8, questCount: 53, point: 275 },
  { id: 'u7', nickname: '나눔지기', initial: '나', email: 'sharekeeper@gmail.com', joined: '2026-07-01', status: '정지', level: 4, questCount: 18, point: 60 },
  { id: 'u8', nickname: '햇살가득', initial: '햇', email: 'sunnyday@gmail.com', joined: '2026-06-30', status: '활성', level: 11, questCount: 77, point: 405 },
];

export default function AdminUserListScreen({ navigation, route }) {
  const [menuVisible, setMenuVisible] = useState(false);
  const [query, setQuery] = useState('');
  const [filter, setFilter] = useState('all');
  const [detailId, setDetailId] = useState(route?.params?.userId ?? null);
  const [suspendedOverride, setSuspendedOverride] = useState({});
  const [toast, setToast] = useState('');

  const showToast = (text) => {
    setToast(text);
    setTimeout(() => setToast(''), 1600);
  };

  const q = query.trim();
  let filtered = USERS;
  if (filter === 'active') filtered = filtered.filter((u) => u.status === '활성');
  if (filter === 'suspended') filtered = filtered.filter((u) => u.status === '정지');
  if (q) filtered = filtered.filter((u) => u.nickname.includes(q) || u.email.includes(q));

  const rawUser = detailId ? USERS.find((u) => u.id === detailId) : null;
  const isSuspended = rawUser && (suspendedOverride[rawUser.id] != null ? suspendedOverride[rawUser.id] : rawUser.status === '정지');

  const onToggleSuspend = () => {
    setSuspendedOverride((s) => ({ ...s, [rawUser.id]: !isSuspended }));
    showToast(!isSuspended ? '계정이 정지되었어요' : '정지가 해제되었어요');
  };

  return (
    <GreenGradientBG>
      <SafeAreaView style={{ flex: 1, backgroundColor: 'transparent' }}>
        <View style={styles.header}>
          <TouchableOpacity onPress={() => navigation.navigate('AdminDashboard')} hitSlop={10} style={{ padding: 4 }}>
            <ChevronLeft size={22} color={COLORS.ink} />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>유저 목록</Text>
          <View style={{ flex: 1 }} />
          <AdminHamburgerButton onPress={() => setMenuVisible(true)} />
        </View>

        <ScrollView contentContainerStyle={styles.content}>
          <View style={styles.searchBar}>
            <Search size={17} color={COLORS.inkMuted48} />
            <TextInput style={styles.searchInput} placeholder="닉네임, 이메일로 검색" placeholderTextColor={COLORS.inkMuted48} value={query} onChangeText={setQuery} />
            {!!query && (
              <TouchableOpacity onPress={() => setQuery('')} hitSlop={6}>
                <X size={16} color={COLORS.inkMuted48} />
              </TouchableOpacity>
            )}
          </View>

          <View style={{ flexDirection: 'row', gap: 8 }}>
            {[
              ['all', '전체'],
              ['active', '활성'],
              ['suspended', '정지'],
            ].map(([key, label]) => (
              <TouchableOpacity key={key} style={[styles.filterChip, filter === key && styles.filterChipActive]} onPress={() => setFilter(key)}>
                <Text style={[styles.filterChipText, filter === key && { color: '#fff' }]}>{label}</Text>
              </TouchableOpacity>
            ))}
          </View>

          <Text style={styles.countText}>총 {filtered.length}명</Text>

          <View style={styles.listCard}>
            {filtered.map((u) => (
              <TouchableOpacity key={u.id} style={styles.userRow} onPress={() => setDetailId(u.id)}>
                <View style={styles.avatar}>
                  <Text style={styles.avatarText}>{u.initial}</Text>
                </View>
                <View style={{ flex: 1, minWidth: 0, gap: 2 }}>
                  <Text style={styles.userNickname}>{u.nickname}</Text>
                  <Text style={styles.userEmail} numberOfLines={1}>
                    {u.email} · {u.joined} 가입
                  </Text>
                </View>
                <View style={[styles.statusChip, { backgroundColor: u.status === '정지' ? '#FBEAE8' : '#E3F5E7' }]}>
                  <Text style={[styles.statusChipText, { color: u.status === '정지' ? '#B23A34' : '#1F8A5B' }]}>{u.status}</Text>
                </View>
              </TouchableOpacity>
            ))}
            {filtered.length === 0 && (
              <View style={{ paddingVertical: 40, alignItems: 'center' }}>
                <Text style={{ fontSize: 14, color: COLORS.inkMuted48 }}>해당하는 유저가 없어요</Text>
              </View>
            )}
          </View>
        </ScrollView>

        <View style={styles.bottomNav}>
          <AdminNavItem Icon={Grid2X2} label="대시보드" onPress={() => navigation.navigate('AdminDashboard')} />
          <AdminNavItem Icon={Users} label="유저 관리" active onPress={() => {}} />
          <AdminNavItem Icon={Flag} label="신고 검토" onPress={() => navigation.navigate('AdminReports')} />
        </View>

        <AdminHamburgerMenu visible={menuVisible} onClose={() => setMenuVisible(false)} navigation={navigation} />

        {!!toast && (
          <View style={styles.toast}>
            <Text style={styles.toastText}>{toast}</Text>
          </View>
        )}

        {/* 유저 상세 팝업 (52번) */}
        <Modal statusBarTranslucent visible={!!rawUser} transparent animationType="slide" onRequestClose={() => setDetailId(null)}>
          <View style={styles.sheetOverlay}>
            <Pressable style={{ flex: 1 }} onPress={() => setDetailId(null)} />
            {rawUser && (
              <View style={styles.sheet}>
                <View style={styles.sheetHandle} />
                <View style={{ flexDirection: 'row', alignItems: 'center', gap: 12 }}>
                  <View style={[styles.avatar, { width: 52, height: 52 }]}>
                    <Text style={[styles.avatarText, { fontSize: 19 }]}>{rawUser.initial}</Text>
                  </View>
                  <View style={{ flex: 1, minWidth: 0, gap: 3 }}>
                    <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
                      <Text style={styles.detailNickname}>{rawUser.nickname}</Text>
                      <View style={[styles.statusChip, { backgroundColor: isSuspended ? '#FBEAE8' : '#E3F5E7' }]}>
                        <Text style={[styles.statusChipText, { color: isSuspended ? '#B23A34' : '#1F8A5B' }]}>{isSuspended ? '정지' : '활성'}</Text>
                      </View>
                    </View>
                    <Text style={styles.userEmail}>{rawUser.email}</Text>
                  </View>
                  <TouchableOpacity onPress={() => setDetailId(null)} hitSlop={8}>
                    <X size={18} color={COLORS.inkMuted48} />
                  </TouchableOpacity>
                </View>

                <View style={styles.statGrid}>
                  <StatBox label="가입일" value={rawUser.joined} />
                  <StatBox label="레벨" value={`Lv.${rawUser.level}`} />
                  <StatBox label="완료 퀘스트" value={`${rawUser.questCount}건`} />
                  <StatBox label="보유 포인트" value={`${rawUser.point.toLocaleString()}P`} />
                </View>

                <View style={{ flexDirection: 'row', gap: 10 }}>
                  <TouchableOpacity style={styles.warnButton} onPress={() => showToast('경고가 발송되었어요')}>
                    <Text style={styles.warnButtonText}>경고 보내기</Text>
                  </TouchableOpacity>
                  <TouchableOpacity style={[styles.suspendButton, { backgroundColor: isSuspended ? '#1F8A5B' : '#B23A34' }]} onPress={onToggleSuspend}>
                    <Text style={styles.suspendButtonText}>{isSuspended ? '정지 해제' : '계정 정지'}</Text>
                  </TouchableOpacity>
                </View>
              </View>
            )}
          </View>
        </Modal>
      </SafeAreaView>
    </GreenGradientBG>
  );
}

function StatBox({ label, value }) {
  return (
    <View style={styles.statBox}>
      <Text style={styles.statLabel}>{label}</Text>
      <Text style={styles.statValue}>{value}</Text>
    </View>
  );
}

function AdminNavItem({ Icon, label, onPress, active }) {
  return (
    <TouchableOpacity style={styles.navItem} onPress={onPress}>
      <Icon size={21} color={active ? COLORS.primary : COLORS.inkMuted48} strokeWidth={active ? 2 : 1.6} />
      <Text style={[styles.navLabel, active && { color: COLORS.primary, fontWeight: '600' }]}>{label}</Text>
    </TouchableOpacity>
  );
}

