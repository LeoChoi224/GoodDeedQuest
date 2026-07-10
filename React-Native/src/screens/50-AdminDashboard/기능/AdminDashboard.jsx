// 50-AdminDashboard.js — React Native (Expo) 관리자 메인페이지 (대시보드)
// 선행퀘스트 / 스토리보드 50번 기준 — KPI 카드 + 최근 가입 유저 + 신고 대기 미리보기
// 관리자 화면은 하단 3탭(대시보드/유저 관리/신고 검토) + 별도 admin 햄버거 메뉴를 씁니다.

import React, { useState } from 'react';
import { View, Text, TouchableOpacity, ScrollView } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Grid2X2, Users, Flag } from 'lucide-react-native';

import { COLORS } from '../../../shared/디자인/tokens';
import { CareIcon, GreenGradientBG } from '../../../shared/기능/components';
import { AdminHamburgerButton, AdminHamburgerMenu } from '../../../shared/admin/기능/components';
import { styles } from '../디자인/AdminDashboard.styles';

const KPIS = [
  { label: '전체 유저', value: '12,480명', delta: '+186 이번 주', danger: false },
  { label: '오늘 신규가입', value: '42명', delta: '+8% 어제 대비', danger: false },
  { label: '진행중 퀘스트', value: '3,214건', delta: '+124 오늘', danger: false },
  { label: '신고 대기', value: '7건', delta: '검토가 필요해요', danger: true },
];

const RECENT_USERS = [
  { id: 'u1', nickname: '민선행', initial: '민', email: 'sunhaeng@gmail.com', status: '활성' },
  { id: 'u2', nickname: '봉사왕진호', initial: '봉', email: 'jinho.vol@gmail.com', status: '활성' },
  { id: 'u3', nickname: '선행러너', initial: '선', email: 'goodrunner@gmail.com', status: '정지' },
];

const REPORT_QUEUE = [
  { id: 'r1', type: '욕설/비방', target: '@quest_lover92', reason: '채팅 중 지속적인 욕설 및 비방 사용', date: '07-05 14:20' },
  { id: 'r2', type: '허위 인증', target: '@green_runner', reason: '퀘스트 인증 사진이 실제 활동과 무관해 보임', date: '07-05 11:02' },
  { id: 'r3', type: '스팸', target: '@point_hunter', reason: '커뮤니티 게시판 반복 홍보성 게시글 작성', date: '07-04 20:41' },
];

export default function AdminDashboardScreen({ navigation }) {
  const [menuVisible, setMenuVisible] = useState(false);

  return (
    <GreenGradientBG>
      <SafeAreaView style={{ flex: 1, backgroundColor: 'transparent' }}>
        <View style={styles.header}>
          <View style={styles.logoBadge}>
            <CareIcon size={18} />
          </View>
          <Text style={styles.logo}>선·퀘</Text>
          <View style={styles.adminTag}>
            <Text style={styles.adminTagText}>ADMIN</Text>
          </View>
          <View style={{ flex: 1 }} />
          <AdminHamburgerButton onPress={() => setMenuVisible(true)} />
        </View>

        <ScrollView contentContainerStyle={styles.content}>
          <View style={styles.kpiGrid}>
            {KPIS.map((k) => (
              <View key={k.label} style={styles.kpiCard}>
                <Text style={styles.kpiLabel}>{k.label}</Text>
                <Text style={styles.kpiValue}>{k.value}</Text>
                <Text style={[styles.kpiDelta, { color: k.danger ? COLORS.gold : '#1F8A5B' }]}>{k.delta}</Text>
              </View>
            ))}
          </View>

          <View style={{ flexDirection: 'row', gap: 10 }}>
            <TouchableOpacity style={styles.shortcutGreen} onPress={() => navigation.navigate('AdminUserList')}>
              <Users size={16} color={COLORS.primary} />
              <Text style={styles.shortcutText}>유저 목록</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.shortcutGold} onPress={() => navigation.navigate('AdminReports')}>
              <Flag size={16} color={COLORS.primary} />
              <Text style={styles.shortcutText}>신고 검토</Text>
            </TouchableOpacity>
          </View>

          <View style={{ gap: 10 }}>
            <View style={styles.sectionHeaderRow}>
              <Text style={styles.sectionTitle}>최근 가입 유저</Text>
              <TouchableOpacity onPress={() => navigation.navigate('AdminUserList')}>
                <Text style={styles.seeAll}>전체보기</Text>
              </TouchableOpacity>
            </View>
            <View style={styles.listCard}>
              {RECENT_USERS.map((u) => (
                <TouchableOpacity key={u.id} style={styles.userRow} onPress={() => navigation.navigate('AdminUserList', { userId: u.id })}>
                  <View style={styles.avatar}>
                    <Text style={styles.avatarText}>{u.initial}</Text>
                  </View>
                  <View style={{ flex: 1, minWidth: 0, gap: 2 }}>
                    <Text style={styles.userNickname}>{u.nickname}</Text>
                    <Text style={styles.userEmail} numberOfLines={1}>
                      {u.email}
                    </Text>
                  </View>
                  <View style={[styles.statusChip, { backgroundColor: u.status === '정지' ? '#FBEAE8' : '#E3F5E7' }]}>
                    <Text style={[styles.statusChipText, { color: u.status === '정지' ? '#B23A34' : '#1F8A5B' }]}>{u.status}</Text>
                  </View>
                </TouchableOpacity>
              ))}
            </View>
          </View>

          <View style={{ gap: 10 }}>
            <View style={styles.sectionHeaderRow}>
              <Text style={styles.sectionTitle}>신고 대기</Text>
              <TouchableOpacity onPress={() => navigation.navigate('AdminReports')}>
                <Text style={styles.seeAll}>전체보기</Text>
              </TouchableOpacity>
            </View>
            {REPORT_QUEUE.map((r) => (
              <TouchableOpacity key={r.id} style={styles.reportCard} onPress={() => navigation.navigate('AdminReportDetail', { reportId: r.id })}>
                <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}>
                  <View style={styles.typeTag}>
                    <Text style={styles.typeTagText}>{r.type}</Text>
                  </View>
                  <Text style={styles.reportDate}>{r.date}</Text>
                </View>
                <Text style={styles.reportTarget}>{r.target}</Text>
                <Text style={styles.reportReason}>{r.reason}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </ScrollView>

        <View style={styles.bottomNav}>
          <AdminNavItem Icon={Grid2X2} label="대시보드" active onPress={() => {}} />
          <AdminNavItem Icon={Users} label="유저 관리" onPress={() => navigation.navigate('AdminUserList')} />
          <AdminNavItem Icon={Flag} label="신고 검토" onPress={() => navigation.navigate('AdminReports')} />
        </View>

        <AdminHamburgerMenu visible={menuVisible} onClose={() => setMenuVisible(false)} navigation={navigation} />
      </SafeAreaView>
    </GreenGradientBG>
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

