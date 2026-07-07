// 54-AdminReportDetail.js — React Native (Expo) 신고/검토 상세보기 (+ 55번 처리 확인 팝업 통합)
// 선행퀘스트 / 스토리보드 54·55번 기준 — 경고 발송/계정 정지/신고 반려 처리 + 확인 팝업

import React, { useState } from 'react';
import { View, Text, TouchableOpacity, ScrollView, Modal, Pressable, StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { ChevronLeft, X } from 'lucide-react-native';

import { COLORS } from '../../../shared/디자인/tokens';
import { GreenGradientBG } from '../../../shared/기능/components';
import { AdminHamburgerButton, AdminHamburgerMenu } from '../../../shared/admin/기능/components';
import { styles } from '../디자인/AdminReportDetail.styles';

const REPORTS = [
  { id: 'r1', type: '욕설/비방', target: '@quest_lover92', targetInitial: 'Q', reporter: '@sun_walker', reasonFull: '채팅 중 지속적인 욕설 및 비방 표현을 사용해 다른 유저가 불쾌감을 느꼈다는 신고가 접수되었습니다. 동일 채팅방 내 3회 이상 반복된 정황이 있습니다.', date: '07-05 14:20', status: '대기' },
  { id: 'r2', type: '허위 인증', target: '@green_runner', targetInitial: 'G', reporter: '@happy_days', reasonFull: '퀘스트 인증 사진이 실제 봉사 활동 현장과 무관한 이미지로 확인되어 허위 인증이 의심된다는 신고입니다.', date: '07-05 11:02', status: '대기' },
  { id: 'r3', type: '스팸', target: '@point_hunter', targetInitial: 'P', reporter: '@team_leader', reasonFull: '커뮤니티 게시판에 짧은 시간 내 동일한 홍보성 게시글을 반복적으로 게시했다는 신고입니다.', date: '07-04 20:41', status: '대기' },
  { id: 'r4', type: '부적절한 닉네임', target: '@***욕설닉네임', targetInitial: '#', reporter: '@peace_walker', reasonFull: '닉네임에 부적절한 표현이 포함되어 있어 다른 유저들에게 불쾌감을 줄 수 있다는 신고입니다.', date: '07-04 09:15', status: '처리완료', resolvedNote: '경고 발송 및 닉네임 변경 요청 처리 완료 (07-04 15:30)' },
  { id: 'r5', type: '욕설/비방', target: '@night_owl22', targetInitial: 'N', reporter: '@morning_star', reasonFull: '커뮤니티 댓글에서 타 유저를 비하하는 발언을 했다는 신고입니다.', date: '07-03 18:02', status: '반려', resolvedNote: '검토 결과 일반적인 의견 표현으로 판단되어 반려 처리되었습니다 (07-03 21:10)' },
];

const STATUS_STYLE = {
  대기: { color: COLORS.gold, bg: COLORS.goldTint },
  처리완료: { color: '#1F8A5B', bg: '#E3F5E7' },
  반려: { color: COLORS.inkMuted48, bg: COLORS.parchment },
};

const ACTION_COPY = {
  warn: { title: '경고를 발송할까요?', desc: '해당 유저에게 신고 사유에 대한 경고 알림이 발송됩니다.', confirmLabel: '경고 발송', confirmColor: COLORS.primary },
  suspend: { title: '계정을 정지할까요?', desc: '해당 유저는 정지 해제 전까지 서비스를 이용할 수 없어요.', confirmLabel: '계정 정지', confirmColor: '#B23A34' },
  reject: { title: '신고를 반려할까요?', desc: '이 신고는 별다른 조치 없이 반려 처리됩니다.', confirmLabel: '신고 반려', confirmColor: COLORS.inkMuted48 },
};

export default function AdminReportDetailScreen({ navigation, route }) {
  const reportId = route?.params?.reportId ?? 'r1';
  const [menuVisible, setMenuVisible] = useState(false);
  const [pendingAction, setPendingAction] = useState(null); // 'warn' | 'suspend' | 'reject' | null
  const [resolvedStatus, setResolvedStatus] = useState(null);
  const [toast, setToast] = useState('');

  const raw = REPORTS.find((r) => r.id === reportId) || REPORTS[0];
  const status = resolvedStatus || raw.status;
  const st = STATUS_STYLE[status];
  const actionable = status === '대기';

  const showToast = (text) => {
    setToast(text);
    setTimeout(() => setToast(''), 1600);
  };

  const onConfirmAction = () => {
    const map = { warn: '경고가 발송되었어요', suspend: '계정이 정지되었어요', reject: '신고가 반려되었어요' };
    if (pendingAction === 'suspend' || pendingAction === 'reject') setResolvedStatus(pendingAction === 'reject' ? '반려' : '처리완료');
    if (pendingAction === 'warn') setResolvedStatus('처리완료');
    showToast(map[pendingAction]);
    setPendingAction(null);
  };

  return (
    <GreenGradientBG>
      <SafeAreaView style={{ flex: 1, backgroundColor: 'transparent' }}>
        <View style={styles.header}>
          <TouchableOpacity onPress={() => navigation.navigate('AdminReports')} hitSlop={10} style={{ padding: 4 }}>
            <ChevronLeft size={22} color={COLORS.ink} />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>신고 상세</Text>
          <View style={{ flex: 1 }} />
          <AdminHamburgerButton onPress={() => setMenuVisible(true)} />
        </View>

        <ScrollView contentContainerStyle={styles.content}>
          <View style={styles.card}>
            <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}>
              <View style={styles.typeTag}>
                <Text style={styles.typeTagText}>{raw.type}</Text>
              </View>
              <View style={[styles.statusChip, { backgroundColor: st.bg }]}>
                <Text style={[styles.statusChipText, { color: st.color }]}>{status}</Text>
              </View>
            </View>
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 10 }}>
              <View style={styles.avatar}>
                <Text style={styles.avatarText}>{raw.targetInitial}</Text>
              </View>
              <View style={{ flex: 1, minWidth: 0, gap: 1 }}>
                <Text style={styles.targetTitle}>신고 대상 · {raw.target}</Text>
                <Text style={styles.metaText}>
                  신고자 {raw.reporter} · {raw.date}
                </Text>
              </View>
              <TouchableOpacity style={styles.viewUserButton} onPress={() => navigation.navigate('UserDetail', { userId: raw.target })}>
                <Text style={styles.viewUserButtonText}>유저 보기</Text>
              </TouchableOpacity>
            </View>
          </View>

          <View style={{ gap: 8 }}>
            <Text style={styles.sectionTitle}>신고 사유</Text>
            <View style={styles.reasonBox}>
              <Text style={styles.reasonText}>{raw.reasonFull}</Text>
            </View>
          </View>

          <View style={{ gap: 8 }}>
            <Text style={styles.sectionTitle}>증빙 자료</Text>
            <View style={{ flexDirection: 'row', gap: 10 }}>
              <View style={styles.evidenceBox}>
                <Text style={styles.evidenceText}>증빙 스크린샷 1</Text>
              </View>
              <View style={styles.evidenceBox}>
                <Text style={styles.evidenceText}>증빙 스크린샷 2</Text>
              </View>
            </View>
          </View>

          {(raw.resolvedNote || resolvedStatus) && (
            <View style={{ gap: 8 }}>
              <Text style={styles.sectionTitle}>처리 결과</Text>
              <View style={styles.resolvedBox}>
                <Text style={styles.resolvedText}>{raw.resolvedNote || '관리자 처리가 완료되었습니다.'}</Text>
              </View>
            </View>
          )}
        </ScrollView>

        {actionable && (
          <View style={styles.actionFooter}>
            <View style={{ flexDirection: 'row', gap: 8 }}>
              <TouchableOpacity style={styles.warnButton} onPress={() => setPendingAction('warn')}>
                <Text style={styles.warnButtonText}>경고 발송</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.suspendButton} onPress={() => setPendingAction('suspend')}>
                <Text style={styles.suspendButtonText}>계정 정지</Text>
              </TouchableOpacity>
            </View>
            <TouchableOpacity style={styles.rejectButton} onPress={() => setPendingAction('reject')}>
              <Text style={styles.rejectButtonText}>신고 반려</Text>
            </TouchableOpacity>
          </View>
        )}

        <AdminHamburgerMenu visible={menuVisible} onClose={() => setMenuVisible(false)} navigation={navigation} />

        {!!toast && (
          <View style={styles.toast}>
            <Text style={styles.toastText}>{toast}</Text>
          </View>
        )}

        {/* 처리 확인 팝업 (55번) */}
        <Modal statusBarTranslucent visible={!!pendingAction} transparent animationType="fade" onRequestClose={() => setPendingAction(null)}>
          <View style={styles.confirmOverlay}>
            <Pressable style={StyleSheet.absoluteFill} onPress={() => setPendingAction(null)} />
            {pendingAction && (
              <View style={styles.confirmCard}>
                <View style={{ flexDirection: 'row', alignItems: 'flex-start', justifyContent: 'space-between' }}>
                  <Text style={styles.confirmTitle}>{ACTION_COPY[pendingAction].title}</Text>
                  <TouchableOpacity onPress={() => setPendingAction(null)} hitSlop={8}>
                    <X size={18} color={COLORS.inkMuted48} />
                  </TouchableOpacity>
                </View>
                <Text style={styles.confirmDesc}>{ACTION_COPY[pendingAction].desc}</Text>
                <View style={{ flexDirection: 'row', gap: 8, width: '100%' }}>
                  <TouchableOpacity style={styles.confirmCancel} onPress={() => setPendingAction(null)}>
                    <Text style={styles.confirmCancelText}>취소</Text>
                  </TouchableOpacity>
                  <TouchableOpacity style={[styles.confirmOk, { backgroundColor: ACTION_COPY[pendingAction].confirmColor }]} onPress={onConfirmAction}>
                    <Text style={styles.confirmOkText}>{ACTION_COPY[pendingAction].confirmLabel}</Text>
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

