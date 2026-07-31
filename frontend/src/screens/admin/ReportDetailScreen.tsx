import React, { useCallback, useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Image,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { LinearGradient } from 'expo-linear-gradient';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import HazeBackground from '../../components/HazeBackground';
import MainHeader from '../../components/MainHeader';
import SpringButton from '../../components/SpringButton';
import { useToast } from '../../components/Toast';
import { colors, fonts } from '../../theme';
import { AD, ConfirmAction, ConfirmPopup } from './_parts';
import {
  adminApi,
  AdminReportDetail,
  getAdminErrorMessage,
} from './adminApi';

export default function ReportDetailScreen({ navigation, route }: any) {
  const insets = useSafeAreaInsets();
  const toast = useToast();
  const reportId = Number(
    route?.params?.reportId ?? route?.params?.report?.report_id,
  );

  const [report, setReport] = useState<AdminReportDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [action, setAction] = useState<ConfirmAction>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [imageError, setImageError] = useState(false);

  const load = useCallback(async () => {
    if (!Number.isInteger(reportId) || reportId <= 0) {
      setError('신고 번호가 올바르지 않습니다.');
      setLoading(false);
      setRefreshing(false);
      return;
    }

    setError('');
    setImageError(false);

    try {
      setReport(await adminApi.getReport(reportId));
    } catch (loadError) {
      setError(getAdminErrorMessage(loadError));
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [reportId]);

  useEffect(() => {
    void load();
  }, [load]);

  const confirm = async () => {
    if (!action || !report) {
      return;
    }

    setBusy(true);

    try {
      if (action === 'delete') {
        await adminApi.approvePostDeletion(report.report_id);
      } else {
        await adminApi.approveUserDeactivation(report.report_id);
      }

      toast.show(
        action === 'delete'
          ? '게시글 삭제 승인이 완료되었습니다'
          : '사용자 비활성 처리가 완료되었습니다',
      );

      setAction(null);
      navigation.goBack();
    } catch (confirmError) {
      toast.show(getAdminErrorMessage(confirmError));
    } finally {
      setBusy(false);
    }
  };

  return (
    <View style={styles.root}>
      <StatusBar style="light" />
      <HazeBackground />

      <MainHeader
        showBack
        title="신고 상세"
        onBack={() => navigation.goBack()}
      />

      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator color={colors.primaryDark} />
          <Text style={styles.muted}>신고 정보를 불러오는 중입니다.</Text>
        </View>
      ) : (
        <ScrollView
          contentContainerStyle={[
            styles.body,
            { paddingBottom: insets.bottom + 96 },
          ]}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={() => {
                setRefreshing(true);
                void load();
              }}
            />
          }
        >
          {error ? <Text style={styles.error}>{error}</Text> : null}

          {report ? (
            <>
              <Text style={styles.date}>
                신고 일자:{' '}
                {new Date(report.created_at).toLocaleString('ko-KR')}
              </Text>

              <View style={styles.mediaCard}>
                <Text style={styles.mediaTitle}>신고된 게시물 사진</Text>

                {report.post_media_url && !imageError ? (
                  <Image
                    source={{ uri: report.post_media_url }}
                    style={styles.postImage}
                    resizeMode="contain"
                    onError={() => setImageError(true)}
                  />
                ) : (
                  <View style={styles.imageEmpty}>
                    <Text style={styles.imageEmptyText}>
                      {imageError
                        ? '게시물 사진을 불러오지 못했습니다.'
                        : '삭제되었거나 등록된 게시물 사진이 없습니다.'}
                    </Text>
                  </View>
                )}
              </View>

              <View style={styles.card}>
                <Text style={styles.title}>신고 #{report.report_id}</Text>
                <Text style={styles.line}>상태: {report.status}</Text>
                <Text style={styles.line}>
                  신고자 ID: {report.reporter_id}
                </Text>
                <Text style={styles.line}>
                  게시글 ID: {report.post_id ?? '삭제됨 또는 없음'}
                </Text>
                <Text style={styles.line}>
                  처리 관리자 ID: {report.reviewed_by ?? '미처리'}
                </Text>
              </View>

              <View style={styles.reasonBox}>
                <Text style={styles.reasonTitle}>신고 사유</Text>
                <Text style={styles.reason}>{report.reason}</Text>
              </View>
            </>
          ) : null}
        </ScrollView>
      )}

      <LinearGradient
        colors={['rgba(238,246,240,0)', colors.screenBg]}
        locations={[0, 0.4]}
        style={[
          styles.footer,
          { paddingBottom: insets.bottom + 20 },
        ]}
      >
        <SpringButton
          disabled={busy || !report}
          style={[styles.btn, styles.block]}
          onPress={() => setAction('block')}
        >
          <Text style={styles.btnText}>사용자 비활성</Text>
        </SpringButton>

        <SpringButton
          disabled={busy || !report}
          style={[styles.btn, styles.delete]}
          onPress={() => setAction('delete')}
        >
          <Text style={styles.btnText}>게시글 삭제</Text>
        </SpringButton>
      </LinearGradient>

      <ConfirmPopup
        action={action}
        onConfirm={() => void confirm()}
        onCancel={() => setAction(null)}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: colors.screenBg,
  },
  body: {
    padding: 16,
  },
  center: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
  },
  muted: {
    color: AD.muted,
    fontFamily: fonts.bodyR,
  },
  error: {
    color: AD.red,
    fontFamily: fonts.bodyM,
    marginBottom: 12,
  },
  date: {
    fontSize: 13,
    color: AD.muted,
    fontFamily: fonts.bodyR,
    marginBottom: 12,
  },
  mediaCard: {
    backgroundColor: colors.white,
    borderWidth: 1,
    borderColor: AD.cardBorder,
    borderRadius: 12,
    padding: 14,
    marginBottom: 14,
  },
  mediaTitle: {
    fontFamily: fonts.bodyB,
    fontSize: 14,
    color: colors.primaryDark,
    marginBottom: 10,
  },
  postImage: {
    width: '100%',
    height: 300,
    borderRadius: 10,
    backgroundColor: colors.screenBg,
  },
  imageEmpty: {
    width: '100%',
    height: 180,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 20,
    backgroundColor: colors.screenBg,
  },
  imageEmptyText: {
    color: AD.muted,
    fontFamily: fonts.bodyR,
    fontSize: 13,
    textAlign: 'center',
  },
  card: {
    backgroundColor: colors.white,
    borderWidth: 1,
    borderColor: AD.cardBorder,
    borderRadius: 12,
    padding: 14,
    marginBottom: 14,
  },
  title: {
    fontFamily: fonts.pixel,
    fontSize: 16,
    color: colors.primaryDark,
    marginBottom: 10,
  },
  line: {
    fontFamily: fonts.bodyR,
    fontSize: 14,
    color: colors.primaryDark,
    lineHeight: 24,
  },
  reasonBox: {
    backgroundColor: AD.detailInfoBg,
    borderRadius: 10,
    padding: 14,
    marginBottom: 14,
  },
  reasonTitle: {
    fontFamily: fonts.bodyB,
    fontSize: 14,
    color: colors.primaryDark,
    marginBottom: 8,
  },
  reason: {
    fontFamily: fonts.bodyR,
    fontSize: 14,
    color: colors.primaryDark,
    lineHeight: 22,
  },
  footer: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    flexDirection: 'row',
    gap: 10,
    paddingHorizontal: 16,
    paddingTop: 12,
  },
  btn: {
    flex: 1,
    height: 50,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  block: {
    backgroundColor: colors.primaryDark,
  },
  delete: {
    backgroundColor: AD.red,
  },
  btnText: {
    color: colors.white,
    fontFamily: fonts.pixel,
    fontSize: 15,
  },
});