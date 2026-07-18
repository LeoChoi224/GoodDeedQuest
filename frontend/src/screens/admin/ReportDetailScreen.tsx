/**
 * SCREEN 4 · 신고 / 검토 상세보기 — route "ReportDetail" (back). Reads route.params.report.
 * 신고 일자 · 신고 유저 카드 · 16:9 신고 이미지 검토 영역(neutral placeholder) · 신고자 ID /
 * 사유. Pinned footer 차단하기 / 삭제하기 → 차단/삭제 확인 팝업 (3A); confirm → Toast + goBack.
 */
import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, Pressable } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { LinearGradient } from 'expo-linear-gradient';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { colors, fonts } from '../../theme';
import HazeBackground from '../../components/HazeBackground';
import MainHeader from '../../components/MainHeader';
import SpringButton from '../../components/SpringButton';
import { useToast } from '../../components/Toast';
import { AD, AVATARS, Avatar, ConfirmPopup, ConfirmAction } from './_parts';

export default function ReportDetailScreen({ navigation, route }: any) {
  const insets = useSafeAreaInsets();
  const toast = useToast();
  const report = route?.params?.report ?? {};

  const [action, setAction] = useState<ConfirmAction>(null);

  const name = report.name ?? '문제유저01';
  const av = report.av ?? AVATARS[2];
  const reportDate = report.date ?? '2026.07.10';
  const reporter = report.reporter ?? 'user_kim';

  const confirm = () => {
    const a = action;
    setAction(null);
    toast.show(a === 'delete' ? '게시물이 삭제되었습니다' : '유저를 차단했습니다');
    setTimeout(() => navigation.goBack(), 260);
  };

  return (
    <View style={styles.root}>
      <StatusBar style="light" />
      <HazeBackground />
      <MainHeader showBack title="신고 상세" onBack={() => navigation.goBack()} />

      <ScrollView
        contentContainerStyle={[styles.body, { paddingBottom: insets.bottom + 96 }]}
        showsVerticalScrollIndicator={false}
      >
        <Text style={styles.reportDate}>신고 일자 : {reportDate} 21:14</Text>

        <Pressable
          style={styles.userCard}
          onPress={() => navigation.navigate('UserDetail', { user: { name, title: '알 수 없음', level: 4 }, moderation: true })}
        >
          <Avatar av={av} />
          <View style={{ flex: 1 }}>
            <Text style={styles.userName}>{name}</Text>
            <Text style={styles.userSub}>알 수 없음 · LV.4</Text>
          </View>
        </Pressable>

        <View style={styles.imageBox}>
          <Text style={styles.imageText}>악용 이미지 검토 및{'\n'}신고 게시물 이미지</Text>
        </View>

        <View style={styles.infoBox}>
          <Text style={styles.infoText}>신고자 ID : {reporter}</Text>
          <Text style={styles.infoText}>신고 사유 : 퀘스트와 무관한 부적절 사진 업로드</Text>
        </View>
      </ScrollView>

      {/* pinned footer */}
      <LinearGradient
        colors={['rgba(238,246,240,0)', colors.screenBg]}
        locations={[0, 0.4]}
        style={[styles.footer, { paddingBottom: insets.bottom + 20 }]}
      >
        <SpringButton style={[styles.footerBtn, styles.blockBtn]} onPress={() => setAction('block')}>
          <Text style={styles.blockText}>차단하기</Text>
        </SpringButton>
        <SpringButton style={[styles.footerBtn, styles.deleteBtn]} onPress={() => setAction('delete')}>
          <Text style={styles.deleteText}>삭제하기</Text>
        </SpringButton>
      </LinearGradient>

      {/* 차단/삭제 확인 팝업 (3A) */}
      <ConfirmPopup action={action} onConfirm={confirm} onCancel={() => setAction(null)} />
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.screenBg },
  body: { padding: 16 },
  reportDate: { fontSize: 14, color: AD.muted, fontFamily: fonts.bodyR, marginBottom: 12 },
  userCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    backgroundColor: colors.screenBg,
    borderWidth: 1,
    borderColor: AD.reportedCardBorder,
    borderRadius: 8,
    padding: 12,
    marginBottom: 14,
  },
  userName: { fontSize: 15, fontWeight: '600', color: colors.primaryDark, fontFamily: fonts.bodyM },
  userSub: { fontSize: 13, color: colors.gold, fontFamily: fonts.bodyR, marginTop: 1 },
  imageBox: {
    width: '100%',
    aspectRatio: 16 / 9,
    backgroundColor: AD.imgBg,
    borderWidth: 1,
    borderColor: AD.cardBorder,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
    marginBottom: 14,
  },
  imageText: { textAlign: 'center', color: AD.muted, fontSize: 13, fontFamily: fonts.bodyR, lineHeight: 20 },
  infoBox: { backgroundColor: AD.detailInfoBg, borderRadius: 8, padding: 14 },
  infoText: { fontSize: 14, color: colors.primaryDark, fontFamily: fonts.bodyR, lineHeight: 25 },
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
  footerBtn: { flex: 1, height: 50, borderRadius: 8, alignItems: 'center', justifyContent: 'center' },
  blockBtn: { backgroundColor: colors.primaryDark },
  blockText: { color: colors.parchment, fontFamily: fonts.pixel, fontSize: 16 },
  deleteBtn: { backgroundColor: AD.red },
  deleteText: { color: colors.white, fontFamily: fonts.pixel, fontSize: 16 },
});
