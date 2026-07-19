/**
 * SCREEN 03·1 — 커뮤니티 메인 · 피드 (route: Feed, 커뮤니티 tab ROOT).
 * MainHeader (no back) + 상단 탭(팀 챌린지 / 피드 작성) + 피드 리스트.
 * · 좋아요 하트: 빈 회색 → 채운 빨강 #E53935 +1, scale bounce (HeartButton)
 * · 좋아요 수 탭 → 좋아요창(BottomSheet) / 댓글 → 댓글창(BottomSheet) / ⋯ → 더보기(BottomSheet)
 * · 더보기 → 신고하기 → 신고 팝업(GamePopup) · 관심없음 → 피드 숨김 + "숨겼어요" 토스트
 * · 피드 작성 탭 → NewPost · 로딩: shimmer 스켈레톤 · 빈 상태: "아직 게시물이 없어요"
 */
import React, { useEffect, useMemo, useState } from 'react';
import { View, Text, StyleSheet, ScrollView, Pressable, TextInput, useWindowDimensions } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import Animated, { FadeInDown } from 'react-native-reanimated';
import { colors, fonts, gamePopup } from '../../theme';
import HazeBackground from '../../components/HazeBackground';
import MainHeader from '../../components/MainHeader';
import SpringButton from '../../components/SpringButton';
import BottomSheet from '../../components/BottomSheet';
import GamePopup from '../../components/GamePopup';
import Shimmer from '../../components/Shimmer';
import { useToast } from '../../components/Toast';
import {
  Avatar,
  GradientFill,
  PlayBadge,
  DotsIcon,
  CommentIcon,
  SirenIcon,
  XCircleIcon,
  HeartButton,
  SheetTitle,
  SheetCloseChevron,
} from './_parts';

/* ---------- data (verbatim from 03_community_flow.dc.html) ---------- */
type Feed = {
  key: string;
  user: string;
  av: [string, string];
  im: [string, string];
  tag: string;
  video: boolean;
  caption: string;
  comments: number;
  like0: number;
};

const FEEDS: Feed[] = [
  {
    key: 'a',
    user: 'green_hero',
    av: ['#4CAF50', '#2E7D32'],
    im: ['#5B8C6E', '#3E6B52'],
    tag: '공원 플로깅 인증',
    video: false,
    caption: '오늘 공원 한 바퀴 돌면서 쓰레기 주웠어요! 🌱',
    comments: 5,
    like0: 24,
  },
  {
    key: 'b',
    user: 'kind_kim',
    av: ['#5B9BD5', '#2E5A9B'],
    im: ['#3A5A7A', '#24405E'],
    tag: '유기견 산책 봉사',
    video: true,
    caption: '보호소 아이들과 산책 다녀왔습니다.',
    comments: 8,
    like0: 12,
  },
];

const AVS: [string, string][] = [
  ['#4CAF50', '#2E7D32'],
  ['#5B9BD5', '#2E5A9B'],
  ['#E57373', '#B04A4A'],
  ['#FF9E5A', '#B96A28'],
  ['#B27BD0', '#7A4A9B'],
];

const COMMENTS = [
  { user: 'kind_kim', text: '멋져요! 저도 참여하고 싶어요 👏', av: AVS[1] },
  { user: 'eco_lee', text: '환경 지킴이 인정합니다', av: AVS[2] },
  { user: 'sunny', text: '오늘도 선행 한 스푼 🥄', av: AVS[3] },
];

const LIKERS = ['kind_kim', 'eco_lee', 'sunny_day', 'volunteer_2', 'green_soul'].map((u, i) => ({
  user: u,
  av: AVS[i % AVS.length],
}));

type LikeState = { liked: boolean; count: number };

export default function FeedScreen({ navigation }: any) {
  const toast = useToast();

  const [loading, setLoading] = useState(true);
  const [likes, setLikes] = useState<Record<string, LikeState>>(
    Object.fromEntries(FEEDS.map((f) => [f.key, { liked: false, count: f.like0 }])),
  );
  const [hidden, setHidden] = useState<Record<string, boolean>>({});

  const [commentsOpen, setCommentsOpen] = useState(false);
  const [likesKey, setLikesKey] = useState<string | null>(null);
  const [moreKey, setMoreKey] = useState<string | null>(null);
  const [reportKey, setReportKey] = useState<string | null>(null);

  // loading skeleton → feed (shimmer)
  useEffect(() => {
    const t = setTimeout(() => setLoading(false), 900);
    return () => clearTimeout(t);
  }, []);

  const visible = useMemo(() => FEEDS.filter((f) => !hidden[f.key]), [hidden]);

  const toggleLike = (k: string) =>
    setLikes((s) => {
      const on = !s[k].liked;
      return { ...s, [k]: { liked: on, count: s[k].count + (on ? 1 : -1) } };
    });

  const hideFeed = (k: string) => {
    setMoreKey(null);
    setHidden((s) => ({ ...s, [k]: true }));
    toast.show('숨겼어요');
  };

  return (
    <View style={styles.root}>
      <StatusBar style="light" />
      <HazeBackground />
      <MainHeader />

      {/* 상단 액션 버튼: 팀 챌린지 · 피드 작성 */}
      <View style={styles.topActions}>
        <SpringButton style={[styles.actBtn, styles.actOutline]} onPress={() => navigation.navigate('TeamHome')}>
          <Text style={styles.actOutlineText}>⚔ 팀 챌린지</Text>
        </SpringButton>
        <SpringButton style={[styles.actBtn, styles.actFill]} onPress={() => navigation.navigate('NewPost')}>
          <Text style={styles.actFillText}>✎ 피드 작성</Text>
        </SpringButton>
      </View>

      {loading ? (
        <View style={styles.skeletonWrap}>
          {[0, 1].map((i) => (
            <View key={i} style={styles.card}>
              <View style={styles.cardHead}>
                <Shimmer width={36} height={36} radius={18} />
                <Shimmer width={110} height={12} radius={6} style={{ marginLeft: 10 }} />
              </View>
              <Shimmer width="100%" height={0} radius={0} style={styles.skelPhoto} />
              <View style={styles.cardBody}>
                <Shimmer width={140} height={12} radius={6} />
                <Shimmer width="86%" height={12} radius={6} style={{ marginTop: 10 }} />
              </View>
            </View>
          ))}
        </View>
      ) : visible.length === 0 ? (
        <View style={styles.empty}>
          <Text style={styles.emptyText}>아직 게시물이 없어요</Text>
        </View>
      ) : (
        <ScrollView contentContainerStyle={styles.listContent} showsVerticalScrollIndicator={false}>
          {visible.map((f, i) => {
            const ls = likes[f.key];
            return (
              <Animated.View
                key={f.key}
                entering={FadeInDown.delay(50 + i * 100).duration(380)}
                style={styles.card}
              >
                {/* head */}
                <View style={styles.cardHead}>
                  <Pressable
                    style={styles.authorBtn}
                    onPress={() => navigation.navigate('UserDetail', { user: { name: f.user, grad: f.av } })}
                  >
                    <Avatar grad={f.av} />
                    <Text style={styles.userName}>{f.user}</Text>
                  </Pressable>
                  <Pressable onPress={() => setMoreKey(f.key)} hitSlop={6} style={styles.dotsBtn}>
                    <DotsIcon />
                  </Pressable>
                </View>

                {/* photo */}
                <GradientFill grad={f.im} style={styles.photo}>
                  <Text style={styles.photoTag}>{f.tag}</Text>
                  {f.video ? (
                    <View style={styles.photoPlay}>
                      <PlayBadge />
                    </View>
                  ) : null}
                </GradientFill>

                {/* body */}
                <View style={styles.cardBody}>
                  <View style={styles.actionRow}>
                    <View style={styles.likeGroup}>
                      <HeartButton liked={ls.liked} onToggle={() => toggleLike(f.key)} />
                      <Pressable onPress={() => setLikesKey(f.key)} hitSlop={6}>
                        <Text style={styles.likeCount}>{ls.count}개</Text>
                      </Pressable>
                    </View>
                    <Pressable style={styles.commentGroup} onPress={() => setCommentsOpen(true)} hitSlop={6}>
                      <CommentIcon />
                      <Text style={styles.commentCount}>{f.comments}</Text>
                    </Pressable>
                  </View>

                  <Text style={styles.caption}>
                    <Text style={styles.captionUser}>{f.user}</Text> {f.caption}
                  </Text>

                  <Pressable onPress={() => setCommentsOpen(true)} hitSlop={4}>
                    <Text style={styles.viewComments}>댓글 {f.comments}개 모두 보기</Text>
                  </Pressable>
                </View>
              </Animated.View>
            );
          })}
        </ScrollView>
      )}

      {/* ===== 댓글창 ===== */}
      <BottomSheet visible={commentsOpen} onClose={() => setCommentsOpen(false)}>
        <SheetTitle text={`댓글 ${COMMENTS.length}개`} />
        <View style={styles.sheetList}>
          {COMMENTS.map((c) => (
            <Pressable
              key={c.user}
              style={styles.commentRow}
              onPress={() => {
                setCommentsOpen(false);
                navigation.navigate('UserDetail', { user: { name: c.user, grad: c.av } });
              }}
            >
              <Avatar grad={c.av as [string, string]} />
              <View style={styles.commentTextWrap}>
                <Text style={styles.rowUser}>{c.user}</Text>
                <Text style={styles.commentText}>{c.text}</Text>
              </View>
            </Pressable>
          ))}
        </View>
        <SheetCloseChevron onPress={() => setCommentsOpen(false)} />
      </BottomSheet>

      {/* ===== 좋아요창 ===== */}
      <BottomSheet visible={likesKey !== null} onClose={() => setLikesKey(null)}>
        <SheetTitle text={`좋아요 ${likesKey ? likes[likesKey].count : 0}개`} />
        <View style={styles.sheetList}>
          {LIKERS.map((l) => (
            <Pressable
              key={l.user}
              style={styles.likerRow}
              onPress={() => {
                setLikesKey(null);
                navigation.navigate('UserDetail', { user: { name: l.user, grad: l.av } });
              }}
            >
              <Avatar grad={l.av as [string, string]} />
              <Text style={styles.likerUser}>{l.user}</Text>
            </Pressable>
          ))}
        </View>
        <SheetCloseChevron onPress={() => setLikesKey(null)} />
      </BottomSheet>

      {/* ===== 더보기 메뉴 ===== */}
      <BottomSheet visible={moreKey !== null} onClose={() => setMoreKey(null)}>
        <Pressable style={[styles.moreRow, styles.moreDivider]} onPress={() => moreKey && hideFeed(moreKey)}>
          <XCircleIcon />
          <Text style={styles.moreText}>관심없음</Text>
        </Pressable>
        <Pressable
          style={styles.moreRow}
          onPress={() => {
            const k = moreKey;
            setMoreKey(null);
            setReportKey(k);
          }}
        >
          <SirenIcon />
          <Text style={[styles.moreText, styles.moreDanger]}>신고하기</Text>
        </Pressable>
      </BottomSheet>

      {/* ===== 신고 팝업 ===== */}
      <ReportPopup
        visible={reportKey !== null}
        onClose={() => setReportKey(null)}
        onSubmit={() => {
          setReportKey(null);
          toast.show('신고가 접수되었습니다');
        }}
      />
    </View>
  );
}

/* ---------- 신고 팝업 (GamePopup, dark teal + gold) ---------- */
function ReportPopup({ visible, onClose, onSubmit }: { visible: boolean; onClose: () => void; onSubmit: () => void }) {
  const { width } = useWindowDimensions();
  const [reason, setReason] = useState('');
  const [focused, setFocused] = useState(false);
  const filled = reason.trim().length > 0;

  const close = () => {
    setReason('');
    setFocused(false);
    onClose();
  };

  return (
    <GamePopup visible={visible} onClose={close} width={Math.min(345, width - 48)} style={rp.frame}>
      <View style={rp.body}>
        <Text style={rp.title}>이 게시물을 신고하는 이유</Text>
        <Text style={rp.desc}>
          회원님의 신고는 익명으로 처리됩니다. 누군가 위급한 상황에 있다고 생각된다면 즉시 현지 응급 서비스 기관에
          연락하시기 바랍니다.
        </Text>

        <View style={[rp.field, { borderColor: focused ? colors.primaryDark : 'rgba(212,160,23,0.4)', borderWidth: focused ? 2 : 1.5 }]}>
          <TextInput
            value={reason}
            onChangeText={setReason}
            onFocus={() => setFocused(true)}
            onBlur={() => setFocused(false)}
            placeholder="신고 사유를 입력해주세요."
            placeholderTextColor="rgba(245,236,203,0.45)"
            multiline
            maxLength={200}
            style={rp.input}
          />
        </View>
        <Text style={rp.counter}>{reason.length}/200</Text>

        <View style={rp.btnRow}>
          <Pressable
            disabled={!filled}
            onPress={onSubmit}
            style={[rp.btn, filled ? rp.reportOn : rp.reportOff]}
          >
            <Text style={rp.reportText}>신고하기</Text>
          </Pressable>
          <Pressable onPress={close} style={[rp.btn, rp.cancel]}>
            <Text style={rp.cancelText}>취소</Text>
          </Pressable>
        </View>
      </View>
    </GamePopup>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.screenBg },

  topActions: {
    flexDirection: 'row',
    gap: 10,
    paddingHorizontal: 16,
    paddingVertical: 10,
    backgroundColor: colors.white,
    borderBottomWidth: 1,
    borderBottomColor: colors.inputBorder,
  },
  actBtn: { flex: 1, height: 42, borderRadius: 999, alignItems: 'center', justifyContent: 'center' },
  actOutline: { borderWidth: 1.5, borderColor: colors.primaryDark, backgroundColor: colors.white },
  actOutlineText: { fontSize: 14, fontWeight: '700', color: colors.primaryDark, fontFamily: fonts.bodyB },
  actFill: { backgroundColor: colors.primaryDark },
  actFillText: { fontSize: 14, fontWeight: '700', color: colors.parchment, fontFamily: fonts.bodyB },

  listContent: { paddingTop: 12, paddingBottom: 20 },
  skeletonWrap: { paddingTop: 12 },

  card: { backgroundColor: colors.white, marginBottom: 8 },
  cardHead: { flexDirection: 'row', alignItems: 'center', paddingVertical: 11, paddingHorizontal: 14 },
  authorBtn: { flex: 1, flexDirection: 'row', alignItems: 'center' },
  userName: { flex: 1, marginLeft: 10, fontSize: 13, fontWeight: '700', color: colors.textPrimary, fontFamily: fonts.bodyB },
  dotsBtn: { width: 32, height: 32, alignItems: 'center', justifyContent: 'center' },

  photo: { width: '100%', aspectRatio: 1, alignItems: 'center', justifyContent: 'center' },
  photoTag: { fontSize: 12, color: 'rgba(255,255,255,0.7)', fontFamily: fonts.bodyM },
  photoPlay: { ...StyleSheet.absoluteFillObject, alignItems: 'center', justifyContent: 'center' },
  skelPhoto: { aspectRatio: 1, height: undefined },

  cardBody: { paddingHorizontal: 14, paddingTop: 12, paddingBottom: 14 },
  actionRow: { flexDirection: 'row', alignItems: 'center', marginBottom: 10 },
  likeGroup: { flexDirection: 'row', alignItems: 'center', gap: 6, marginRight: 16 },
  likeCount: { fontSize: 13, fontWeight: '600', color: colors.textPrimary, fontFamily: fonts.bodyM },
  commentGroup: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  commentCount: { fontSize: 13, color: colors.textPrimary, fontFamily: fonts.bodyR },
  caption: { fontSize: 13, color: colors.textPrimary, lineHeight: 20, fontFamily: fonts.bodyR },
  captionUser: { fontWeight: '700', fontFamily: fonts.bodyB },
  viewComments: { fontSize: 13, color: colors.textSecondary, marginTop: 6, fontFamily: fonts.bodyR },

  empty: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  emptyText: { fontSize: 14, color: colors.textSecondary, fontFamily: fonts.bodyM },

  // sheets
  sheetList: { paddingTop: 4 },
  commentRow: { flexDirection: 'row', gap: 10, paddingVertical: 13 },
  commentTextWrap: { flex: 1 },
  rowUser: { fontSize: 13, fontWeight: '700', color: colors.textPrimary, fontFamily: fonts.bodyB },
  commentText: { fontSize: 13, color: colors.textPrimary, marginTop: 2, fontFamily: fonts.bodyR, lineHeight: 19 },
  likerRow: { flexDirection: 'row', alignItems: 'center', gap: 12, paddingVertical: 10 },
  likerUser: { fontSize: 14, fontWeight: '700', color: colors.textPrimary, fontFamily: fonts.bodyB },

  moreRow: { flexDirection: 'row', alignItems: 'center', gap: 14, height: 56, marginHorizontal: -20, paddingHorizontal: 20 },
  moreDivider: { borderBottomWidth: 1, borderBottomColor: colors.inputBorder },
  moreText: { fontSize: 15, color: colors.textPrimary, fontFamily: fonts.bodyR },
  moreDanger: { color: colors.danger, fontWeight: '700', fontFamily: fonts.bodyB },
});

const rp = StyleSheet.create({
  frame: { borderColor: colors.gold },
  body: { width: '100%' },
  title: { fontFamily: fonts.pixel, fontSize: 16, color: '#F5ECCB', textAlign: 'center', marginBottom: 12 },
  desc: { fontSize: 13, color: '#B9C9BD', textAlign: 'center', lineHeight: 21, marginBottom: 18 },
  field: { borderRadius: 10, backgroundColor: 'rgba(255,255,255,0.08)' },
  input: {
    height: 100,
    padding: 12,
    fontSize: 14,
    color: '#F5ECCB',
    fontFamily: fonts.bodyR,
    textAlignVertical: 'top',
  },
  counter: { alignSelf: 'flex-end', marginTop: 6, fontSize: 11, color: 'rgba(245,236,203,0.55)', fontFamily: fonts.bodyR },
  btnRow: { flexDirection: 'row', gap: 12, marginTop: 12 },
  btn: { flex: 1, height: 48, borderRadius: 10, alignItems: 'center', justifyContent: 'center' },
  reportOn: { backgroundColor: colors.danger, borderWidth: 1.5, borderColor: '#FF8A8A' },
  reportOff: { backgroundColor: colors.disabled, borderWidth: 1.5, borderColor: 'rgba(255,255,255,0.25)' },
  reportText: { color: colors.white, fontSize: 14, fontFamily: fonts.pixel },
  cancel: { backgroundColor: 'rgba(255,248,231,0.1)', borderWidth: 1, borderColor: '#5C6B60' },
  cancelText: { color: gamePopup.cream, fontSize: 14, fontFamily: fonts.pixel },
});
