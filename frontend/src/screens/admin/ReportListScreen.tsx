import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  FlatList,
  RefreshControl,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Animated, { FadeInDown } from 'react-native-reanimated';

import EmptyState from '../../components/EmptyState';
import HazeBackground from '../../components/HazeBackground';
import MainHeader from '../../components/MainHeader';
import SpringButton from '../../components/SpringButton';
import { useToast } from '../../components/Toast';
import { colors, fonts } from '../../theme';
import {
  AD,
  Avatar,
  AVATARS,
  ConfirmAction,
  ConfirmPopup,
  LoadingDots,
  NewBadge,
  SkeletonCard,
} from './_parts';
import {
  adminApi,
  AdminReport,
  getAdminErrorMessage,
} from './adminApi';

const LIMIT = 20;

export default function ReportListScreen({ navigation }: any) {
  const insets = useSafeAreaInsets();
  const toast = useToast();

  const [rows, setRows] = useState<AdminReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [more, setMore] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [error, setError] = useState('');
  const [pending, setPending] = useState<{
    action: ConfirmAction;
    report: AdminReport;
  } | null>(null);

  const skip = useRef(0);

  const load = useCallback(async (reset = false) => {
    if (reset) {
      setLoading(true);
      skip.current = 0;
    } else {
      setMore(true);
    }

    setError('');

    try {
      const data = await adminApi.getReports({
        status: 'PENDING',
        skip: skip.current,
        limit: LIMIT,
        newest_first: true,
      });

      setRows((previous) =>
        reset ? data : [...previous, ...data],
      );

      skip.current += data.length;
      setHasMore(data.length === LIMIT);
    } catch (loadError) {
      setError(getAdminErrorMessage(loadError));
    } finally {
      setLoading(false);
      setMore(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    void load(true);
  }, [load]);

  const confirm = async () => {
    if (!pending?.action) {
      return;
    }

    const { action, report } = pending;
    setPending(null);

    try {
      if (action === 'reject') {
        await adminApi.rejectReport(report.report_id);
      } else if (action === 'delete') {
        await adminApi.approvePostDeletion(report.report_id);
      } else {
        await adminApi.approveUserDeactivation(report.report_id);
      }

      setRows((previous) =>
        previous.filter(
          (item) => item.report_id !== report.report_id,
        ),
      );

      // PENDING 목록에서 한 건이 빠졌으므로 다음 페이지 offset도 보정합니다.
      skip.current = Math.max(0, skip.current - 1);

      toast.show(
        action === 'reject'
          ? '신고를 반려했습니다'
          : action === 'delete'
            ? '게시글 삭제 승인이 완료되었습니다'
            : '신고 대상 사용자 비활성 처리가 완료되었습니다',
      );
    } catch (confirmError) {
      toast.show(getAdminErrorMessage(confirmError));
    }
  };

  return (
    <View style={styles.root}>
      <StatusBar style="light" />
      <HazeBackground />

      <MainHeader
        showBack
        title="신고 / 검토"
        onBack={() => navigation.goBack()}
      />

      {loading ? (
        <View style={styles.pad}>
          {[0, 1, 2, 3].map((item) => (
            <SkeletonCard key={item} height={100} />
          ))}
        </View>
      ) : (
        <FlatList
          data={rows}
          keyExtractor={(report) => String(report.report_id)}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={() => {
                setRefreshing(true);
                void load(true);
              }}
            />
          }
          ListHeaderComponent={
            error ? <Text style={styles.error}>{error}</Text> : null
          }
          renderItem={({ item, index }) => (
            <Animated.View
              entering={FadeInDown
                .delay(Math.min(index, 6) * 45)
                .duration(400)}
              style={styles.card}
            >
              <View style={styles.top}>
                <SpringButton
                  style={styles.detailLink}
                  pressScale={0.98}
                  onPress={() =>
                    navigation.navigate('ReportDetail', {
                      reportId: item.report_id,
                      report: item,
                    })
                  }
                >
                  <Avatar
                    av={AVATARS[item.report_id % AVATARS.length]}
                  />

                  <View style={styles.info}>
                    <View style={styles.nameRow}>
                      {item.status === 'PENDING' ? <NewBadge /> : null}
                      <Text style={styles.name}>
                        신고 #{item.report_id}
                      </Text>
                    </View>

                    <Text style={styles.sub}>
                      신고자 ID: {item.reporter_id}
                    </Text>

                    <Text numberOfLines={1} style={styles.reason}>
                      {item.reason}
                    </Text>
                  </View>
                </SpringButton>

                <View style={styles.reportMeta}>
                  <Text style={styles.date}>
                    {new Date(item.created_at).toLocaleDateString(
                      'ko-KR',
                    )}
                  </Text>

                  <SpringButton
                    style={styles.rejectButton}
                    hitSlop={8}
                    pressScale={0.9}
                    onPress={() =>
                      setPending({
                        action: 'reject',
                        report: item,
                      })
                    }
                  >
                    <Text style={styles.rejectText}>×</Text>
                  </SpringButton>
                </View>
              </View>

              <View style={styles.actions}>
                <SpringButton
                  style={styles.delete}
                  onPress={() =>
                    setPending({ action: 'delete', report: item })
                  }
                >
                  <Text style={styles.actionText}>게시글 삭제</Text>
                </SpringButton>

                <SpringButton
                  style={styles.block}
                  onPress={() =>
                    setPending({ action: 'block', report: item })
                  }
                >
                  <Text style={styles.actionText}>사용자 비활성</Text>
                </SpringButton>
              </View>
            </Animated.View>
          )}
          ItemSeparatorComponent={() => <View style={styles.separator} />}
          ListEmptyComponent={
            <EmptyState icon="✅" message="처리할 신고 건이 없습니다" />
          }
          onEndReached={() => {
            if (!more && hasMore) {
              void load(false);
            }
          }}
          onEndReachedThreshold={0.4}
          ListFooterComponent={
            more ? <LoadingDots /> : <View style={styles.footerSpace} />
          }
          contentContainerStyle={[
            styles.pad,
            { paddingBottom: insets.bottom + 24 },
          ]}
        />
      )}

      <ConfirmPopup
        action={pending?.action ?? null}
        onConfirm={() => void confirm()}
        onCancel={() => setPending(null)}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: colors.screenBg,
  },
  pad: {
    paddingHorizontal: 16,
    paddingTop: 14,
    gap: 10,
  },
  error: {
    color: AD.red,
    fontFamily: fonts.bodyM,
    marginBottom: 10,
  },
  card: {
    backgroundColor: colors.white,
    borderWidth: 1,
    borderColor: AD.cardBorder,
    borderRadius: 12,
    padding: 14,
  },
  top: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 8,
  },
  detailLink: {
    flex: 1,
    minWidth: 0,
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
  },
  info: {
    flex: 1,
    minWidth: 0,
  },
  nameRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  name: {
    fontSize: 15,
    fontFamily: fonts.bodyM,
    color: colors.primaryDark,
  },
  sub: {
    fontSize: 12,
    fontFamily: fonts.bodyR,
    color: AD.muted,
    marginTop: 2,
  },
  reason: {
    fontSize: 13,
    fontFamily: fonts.bodyR,
    color: colors.textSecondary,
    marginTop: 4,
  },
  reportMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  date: {
    fontSize: 10,
    fontFamily: fonts.bodyR,
    color: AD.muted,
  },
  rejectButton: {
    width: 30,
    height: 30,
    borderRadius: 15,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: 'rgba(255, 68, 68, 0.25)',
    backgroundColor: 'rgba(255, 68, 68, 0.08)',
  },
  rejectText: {
    color: AD.red,
    fontSize: 23,
    lineHeight: 25,
    fontFamily: fonts.bodyR,
  },
  actions: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    gap: 8,
    marginTop: 10,
  },
  delete: {
    backgroundColor: AD.red,
    borderRadius: 6,
    paddingHorizontal: 10,
    paddingVertical: 7,
  },
  block: {
    backgroundColor: colors.primaryDark,
    borderRadius: 6,
    paddingHorizontal: 10,
    paddingVertical: 7,
  },
  actionText: {
    color: colors.white,
    fontFamily: fonts.bodyB,
    fontSize: 12,
  },
  separator: {
    height: 10,
  },
  footerSpace: {
    height: 16,
  },
});