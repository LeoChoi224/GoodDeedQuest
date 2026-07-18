/**
 * SCREEN 3 · 신고 / 검토 목록 — route "ReportList" (back). 최신순 filter, infinite
 * scroll (onEndReached appends, dots loader), NEW badge (pulse) on fresh reports.
 * Tapping a card → navigate('ReportDetail', { report }). The per-card 삭제하기 /
 * 차단하기 buttons open the 차단/삭제 확인 팝업 (3A); confirm → Toast + removes the row.
 */
import React, { useEffect, useRef, useState } from 'react';
import { View, Text, StyleSheet, Pressable, FlatList } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Animated, { FadeInDown } from 'react-native-reanimated';
import { colors, fonts } from '../../theme';
import HazeBackground from '../../components/HazeBackground';
import MainHeader from '../../components/MainHeader';
import SpringButton from '../../components/SpringButton';
import EmptyState from '../../components/EmptyState';
import { useToast } from '../../components/Toast';
import {
  AD, Avatar, ChevronDown, NewBadge, LoadingDots, SkeletonCard, ConfirmPopup, ConfirmAction,
  makeReports, AdminReport,
} from './_parts';

const MAX_PAGES = 4;

function FilterRow() {
  return (
    <View style={styles.filterRow}>
      <Pressable style={styles.filterChip}>
        <Text style={styles.filterText}>최신순</Text>
        <ChevronDown />
      </Pressable>
    </View>
  );
}

export default function ReportListScreen({ navigation }: any) {
  const insets = useSafeAreaInsets();
  const toast = useToast();

  const [initialLoading, setInitialLoading] = useState(true);
  const [reports, setReports] = useState<AdminReport[]>([]);
  const [loadingMore, setLoadingMore] = useState(false);
  const [pending, setPending] = useState<{ action: ConfirmAction; report: AdminReport } | null>(null);
  const pageRef = useRef(0);

  useEffect(() => {
    const t = setTimeout(() => {
      setReports(makeReports(0));
      setInitialLoading(false);
    }, 700);
    return () => clearTimeout(t);
  }, []);

  const loadMore = () => {
    if (initialLoading || loadingMore || pageRef.current >= MAX_PAGES) return;
    setLoadingMore(true);
    setTimeout(() => {
      pageRef.current += 1;
      setReports((prev) => [...prev, ...makeReports(pageRef.current)]);
      setLoadingMore(false);
    }, 900);
  };

  const confirm = () => {
    if (!pending) return;
    const { action, report } = pending;
    setPending(null);
    setReports((prev) => prev.filter((r) => r.id !== report.id));
    toast.show(action === 'delete' ? '게시물이 삭제되었습니다' : '유저를 차단했습니다');
  };

  const renderReport = ({ item, index }: { item: AdminReport; index: number }) => (
    <Animated.View entering={FadeInDown.delay(Math.min(index, 6) * 55).duration(450)} style={styles.reportCard}>
      <Pressable style={styles.reportTop} onPress={() => navigation.navigate('ReportDetail', { report: item })}>
        <Avatar av={item.av} />
        <View style={styles.reportInfo}>
          <View style={styles.nameRow}>
            {item.isNew ? <NewBadge /> : null}
            <Text style={styles.reportName}>{item.name}</Text>
          </View>
          <Text style={styles.reporter}>신고자 : {item.reporter}</Text>
        </View>
        <Text style={styles.reportDate}>{item.date}</Text>
      </Pressable>
      <View style={styles.actionRow}>
        <SpringButton style={styles.actionBtn} pressScale={0.92} onPress={() => setPending({ action: 'delete', report: item })}>
          <Text style={styles.actionText}>삭제하기</Text>
        </SpringButton>
        <SpringButton style={styles.actionBtn} pressScale={0.92} onPress={() => setPending({ action: 'block', report: item })}>
          <Text style={styles.actionText}>차단하기</Text>
        </SpringButton>
      </View>
    </Animated.View>
  );

  return (
    <View style={styles.root}>
      <StatusBar style="light" />
      <HazeBackground />
      <MainHeader showBack title="신고 / 검토" onBack={() => navigation.goBack()} />

      {initialLoading ? (
        <View style={styles.listPad}>
          <FilterRow />
          <View style={{ gap: 10 }}>
            {[0, 1, 2, 3].map((i) => <SkeletonCard key={i} height={100} />)}
          </View>
        </View>
      ) : (
        <FlatList
          data={reports}
          keyExtractor={(r) => r.id}
          renderItem={renderReport}
          ListHeaderComponent={FilterRow}
          ListEmptyComponent={<EmptyState icon="✅" message="처리할 신고 건이 없습니다" />}
          contentContainerStyle={[styles.listPad, { paddingBottom: insets.bottom + 24 }]}
          ItemSeparatorComponent={() => <View style={{ height: 10 }} />}
          showsVerticalScrollIndicator={false}
          onEndReached={loadMore}
          onEndReachedThreshold={0.4}
          ListFooterComponent={
            loadingMore ? <LoadingDots /> : pageRef.current >= MAX_PAGES ? <View style={{ height: 8 }} /> : <View style={{ height: 20 }} />
          }
        />
      )}

      {/* 차단/삭제 확인 팝업 (3A) */}
      <ConfirmPopup action={pending?.action ?? null} onConfirm={confirm} onCancel={() => setPending(null)} />
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.screenBg },
  listPad: { paddingHorizontal: 16, paddingTop: 14 },

  filterRow: { flexDirection: 'row', justifyContent: 'flex-end', marginBottom: 12 },
  filterChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: colors.white,
    borderWidth: 1,
    borderColor: colors.pixelBorder,
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  filterText: { fontSize: 12, fontWeight: '700', color: colors.primaryDark, fontFamily: fonts.bodyB },

  reportCard: {
    backgroundColor: colors.white,
    borderWidth: 1,
    borderColor: AD.cardBorder,
    borderRadius: 12,
    padding: 14,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 2,
  },
  reportTop: { flexDirection: 'row', alignItems: 'flex-start', gap: 12 },
  reportInfo: { flex: 1, minWidth: 0 },
  nameRow: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  reportName: { fontSize: 15, fontWeight: '600', color: colors.primaryDark, fontFamily: fonts.bodyM },
  reporter: { fontSize: 13, color: AD.muted, fontFamily: fonts.bodyR, marginTop: 2 },
  reportDate: { fontSize: 12, color: AD.muted, fontFamily: fonts.bodyR },
  actionRow: { flexDirection: 'row', justifyContent: 'flex-end', gap: 8, marginTop: 10 },
  actionBtn: { backgroundColor: AD.red, borderRadius: 6, paddingHorizontal: 12, paddingVertical: 6 },
  actionText: { color: colors.white, fontSize: 12, fontWeight: '700', fontFamily: fonts.bodyB },
});
