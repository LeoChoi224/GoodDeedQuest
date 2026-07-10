// 53-AdminReports.js — React Native (Expo) 신고/검토 페이지
// 선행퀘스트 / 스토리보드 53번 기준 — 상태 탭(대기/처리완료/반려) + NEW 뱃지, 정렬

import React, { useState } from 'react';
import { View, Text, TouchableOpacity, ScrollView } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { ChevronLeft, ChevronRight, Grid2X2, Users, Flag } from 'lucide-react-native';

import { COLORS } from '../../../shared/디자인/tokens';
import { GreenGradientBG } from '../../../shared/기능/components';
import { AdminHamburgerButton, AdminHamburgerMenu } from '../../../shared/admin/기능/components';
import { styles } from '../디자인/AdminReports.styles';

const REPORTS = [
  { id: 'r1', type: '욕설/비방', target: '@quest_lover92', reporter: '@sun_walker', reason: '채팅 중 지속적인 욕설 및 비방 사용', date: '07-05 14:20', status: '대기', isNew: true },
  { id: 'r2', type: '허위 인증', target: '@green_runner', reporter: '@happy_days', reason: '퀘스트 인증 사진이 실제 활동과 무관해 보임', date: '07-05 11:02', status: '대기', isNew: true },
  { id: 'r3', type: '스팸', target: '@point_hunter', reporter: '@team_leader', reason: '커뮤니티 게시판 반복 홍보성 게시글 작성', date: '07-04 20:41', status: '대기', isNew: false },
  { id: 'r4', type: '부적절한 닉네임', target: '@***욕설닉네임', reporter: '@peace_walker', reason: '닉네임에 부적절한 표현 포함 신고 접수', date: '07-04 09:15', status: '처리완료', isNew: false },
  { id: 'r5', type: '욕설/비방', target: '@night_owl22', reporter: '@morning_star', reason: '커뮤니티 댓글에서 타 유저 비하 발언', date: '07-03 18:02', status: '반려', isNew: false },
];

const STATUS_STYLE = {
  대기: { color: COLORS.gold, bg: COLORS.goldTint },
  처리완료: { color: '#1F8A5B', bg: '#E3F5E7' },
  반려: { color: COLORS.inkMuted48, bg: COLORS.parchment },
};

export default function AdminReportsScreen({ navigation }) {
  const [menuVisible, setMenuVisible] = useState(false);
  const [tab, setTab] = useState('대기');

  // 최신순 정렬(대기 탭에서 NEW 신고 우선)
  const filtered = REPORTS.filter((r) => r.status === tab).sort((a, b) => (b.isNew ? 1 : 0) - (a.isNew ? 1 : 0));

  return (
    <GreenGradientBG>
      <SafeAreaView style={{ flex: 1, backgroundColor: 'transparent' }}>
        <View style={styles.header}>
          <TouchableOpacity onPress={() => navigation.navigate('AdminDashboard')} hitSlop={10} style={{ padding: 4 }}>
            <ChevronLeft size={22} color={COLORS.ink} />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>신고 / 검토</Text>
          <View style={{ flex: 1 }} />
          <AdminHamburgerButton onPress={() => setMenuVisible(true)} />
        </View>

        <ScrollView contentContainerStyle={styles.content}>
          <View style={{ flexDirection: 'row', gap: 8 }}>
            {['대기', '처리완료', '반려'].map((t) => (
              <TouchableOpacity key={t} style={[styles.tab, tab === t && styles.tabActive]} onPress={() => setTab(t)}>
                <Text style={[styles.tabText, tab === t && { color: '#fff' }]}>{t}</Text>
              </TouchableOpacity>
            ))}
          </View>

          <Text style={styles.countText}>총 {filtered.length}건</Text>

          <View style={{ gap: 10 }}>
            {filtered.map((r) => {
              const st = STATUS_STYLE[r.status];
              return (
                <TouchableOpacity key={r.id} style={styles.reportCard} onPress={() => navigation.navigate('AdminReportDetail', { reportId: r.id })}>
                  <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}>
                    <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
                      <View style={styles.typeTag}>
                        <Text style={styles.typeTagText}>{r.type}</Text>
                      </View>
                      {r.isNew && (
                        <View style={styles.newBadge}>
                          <Text style={styles.newBadgeText}>NEW</Text>
                        </View>
                      )}
                    </View>
                    <View style={[styles.statusChip, { backgroundColor: st.bg }]}>
                      <Text style={[styles.statusChipText, { color: st.color }]}>{r.status}</Text>
                    </View>
                  </View>
                  <Text style={styles.reportTarget}>{r.target}</Text>
                  <Text style={styles.reportReason}>{r.reason}</Text>
                  <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginTop: 2 }}>
                    <Text style={styles.reportMeta}>
                      신고자 {r.reporter} · {r.date}
                    </Text>
                    <ChevronRight size={15} color={COLORS.inkMuted48} />
                  </View>
                </TouchableOpacity>
              );
            })}
            {filtered.length === 0 && (
              <View style={{ paddingVertical: 40, alignItems: 'center' }}>
                <Text style={{ fontSize: 14, color: COLORS.inkMuted48 }}>해당하는 신고가 없어요</Text>
              </View>
            )}
          </View>
        </ScrollView>

        <View style={styles.bottomNav}>
          <AdminNavItem Icon={Grid2X2} label="대시보드" onPress={() => navigation.navigate('AdminDashboard')} />
          <AdminNavItem Icon={Users} label="유저 관리" onPress={() => navigation.navigate('AdminUserList')} />
          <AdminNavItem Icon={Flag} label="신고 검토" active onPress={() => {}} />
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

