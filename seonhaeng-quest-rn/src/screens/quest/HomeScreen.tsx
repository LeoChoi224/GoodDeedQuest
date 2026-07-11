/**
 * SCREEN 1 · 메인 홈 (route QuestHome) — 홈 탭 ROOT.
 * MainHeader (no back). 진행중 퀘스트 드래그 캐러셀(빈 상태 토글) · 오늘의 추천 리스트
 * (스태거 페이드업) · 다시 추천 받기 · 퀘스트 등록 / 커스텀 추천 액션.
 */
import React, { useRef, useState } from 'react';
import {
  View,
  Text,
  Image,
  StyleSheet,
  ScrollView,
  Pressable,
  useWindowDimensions,
  NativeSyntheticEvent,
  NativeScrollEvent,
} from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { LinearGradient } from 'expo-linear-gradient';
import Animated, { FadeInDown } from 'react-native-reanimated';
import { colors, fonts, radii, CATEGORY_ICONS } from '../../theme';
import HazeBackground from '../../components/HazeBackground';
import MainHeader from '../../components/MainHeader';
import SpringButton from '../../components/SpringButton';
import { Coin, Star, DiffChip, ChevRight, ChevLeft, EmptyScroll, FloatSpark, Bob } from './_parts';

const RECOMMENDED = [
  { title: '유기견 산책 봉사', category: 'animal', diff: '쉬움', point: '200P', exp: '80 EXP' },
  { title: '독거 어르신 안부 전화', category: 'community', diff: '보통', point: '300P', exp: '120 EXP' },
  { title: '공원 플로깅', category: 'environment', diff: '쉬움', point: '250P', exp: '100 EXP' },
  { title: '무료급식 배식 봉사', category: 'sharing', diff: '보통', point: '400P', exp: '150 EXP' },
  { title: '헌혈 참여', category: 'volunteer', diff: '어려움', point: '500P', exp: '200 EXP' },
];

const ACTIVE = [
  { title: '골목길 쓰레기 줍기', category: 'environment', prog: 60, point: '250 P', exp: '100 EXP' },
  { title: '플리마켓 물품 기부', category: 'sharing', prog: 35, point: '300 P', exp: '120 EXP' },
  { title: '공원 플로깅', category: 'environment', prog: 80, point: '250 P', exp: '100 EXP' },
];

const num = (s: string) => parseInt(s.replace(/[^0-9]/g, ''), 10) || 0;

export default function HomeScreen({ navigation }: any) {
  const { width } = useWindowDimensions();
  // 진행중 퀘스트 유무 (실서비스에선 데이터에서 결정). 기본 false = 카러셀 표시.
  const empty = false;
  const [idx, setIdx] = useState(0);
  const [recRot, setRecRot] = useState(0);
  const scrollRef = useRef<ScrollView>(null);

  const r = recRot % RECOMMENDED.length;
  const recList = [...RECOMMENDED.slice(r), ...RECOMMENDED.slice(0, r)];

  const INNER = width - 32; // ScrollView horizontal padding 16 each side
  const CARD_W = INNER * 0.84;
  const STEP = CARD_W + 12;

  const openDetail = (q: { title: string; category: string; point: string; exp: string }, active: boolean) => {
    navigation.navigate('QuestDetail', {
      title: q.title,
      category: q.category,
      point: num(q.point),
      exp: num(q.exp),
      active,
    });
  };

  const onCarouselEnd = (e: NativeSyntheticEvent<NativeScrollEvent>) => {
    const i = Math.round(e.nativeEvent.contentOffset.x / STEP);
    setIdx(Math.max(0, Math.min(ACTIVE.length - 1, i)));
  };
  const goTo = (i: number) => {
    const n = Math.max(0, Math.min(ACTIVE.length - 1, i));
    setIdx(n);
    scrollRef.current?.scrollTo({ x: n * STEP, animated: true });
  };

  return (
    <View style={styles.root}>
      <StatusBar style="light" />
      <HazeBackground />
      <MainHeader />

      <ScrollView contentContainerStyle={styles.body} showsVerticalScrollIndicator={false}>
        {/* ── 진행중 퀘스트 header ── */}
        <View style={styles.sectionHead}>
          <Text style={styles.sectionTitle}>진행중 퀘스트</Text>
          <View style={styles.headRight}>
            <Pressable onPress={() => goTo(idx - 1)} hitSlop={6}>
              <ChevLeft />
            </Pressable>
            <Pressable onPress={() => goTo(idx + 1)} hitSlop={6}>
              <ChevRight />
            </Pressable>
          </View>
        </View>

        {empty ? (
          <View style={styles.emptyBox}>
            <EmptyScroll />
            <Text style={styles.emptyText}>진행중인 퀘스트가 없어요</Text>
            <Pressable onPress={() => openDetail(RECOMMENDED[2], false)} hitSlop={6}>
              <Text style={styles.emptyLink}>퀘스트 시작하기</Text>
            </Pressable>
          </View>
        ) : (
          <View style={styles.carouselWrap}>
            <ScrollView
              ref={scrollRef}
              horizontal
              showsHorizontalScrollIndicator={false}
              decelerationRate="fast"
              snapToInterval={STEP}
              snapToAlignment="start"
              disableIntervalMomentum
              onMomentumScrollEnd={onCarouselEnd}
              contentContainerStyle={styles.carouselContent}
            >
              {ACTIVE.map((q, i) => (
                <Pressable
                  key={q.title + i}
                  onPress={() => openDetail(q, true)}
                  style={[styles.activeCard, { width: CARD_W, marginRight: i === ACTIVE.length - 1 ? 0 : 12 }]}
                >
                  <LinearGradient
                    colors={['#0E4F40', '#033236']}
                    start={{ x: 0, y: 0 }}
                    end={{ x: 0.5, y: 1 }}
                    style={StyleSheet.absoluteFill}
                  />
                  <FloatSpark left="14%" top="52%" delay={0} size={12} />
                  <FloatSpark left="82%" top="30%" delay={700} size={10} />
                  <FloatSpark left="46%" top="24%" delay={1300} glyph="✦" color="#7FD69A" size={9} />
                  <View style={styles.activeRow}>
                    <Bob amp={4} style={styles.activeIconTile}>
                      <Image source={CATEGORY_ICONS[q.category]} style={styles.activeIcon} />
                    </Bob>
                    <View style={{ flex: 1, minWidth: 0 }}>
                      <Text style={styles.activeTitle} numberOfLines={1}>{q.title}</Text>
                      <View style={styles.rewardRow}>
                        <View style={styles.rewardItem}>
                          <Coin />
                          <Text style={styles.coinText}>{q.point}</Text>
                        </View>
                        <View style={styles.rewardItem}>
                          <Star />
                          <Text style={styles.expText}>{q.exp}</Text>
                        </View>
                      </View>
                    </View>
                    <View style={styles.progBadge}>
                      <Text style={styles.progBadgeText}>진행중</Text>
                    </View>
                  </View>
                </Pressable>
              ))}
            </ScrollView>
            <View style={styles.dots}>
              {ACTIVE.map((_, i) => (
                <View key={i} style={[styles.dot, i === idx ? styles.dotOn : styles.dotOff]} />
              ))}
            </View>
          </View>
        )}

        {/* ── 오늘의 추천 퀘스트 ── */}
        <View style={styles.sectionHead}>
          <Text style={styles.sectionTitle}>오늘의 추천 퀘스트</Text>
        </View>
        <View style={styles.recList}>
          {recList.map((q, i) => (
            <Animated.View key={`${q.title}-${recRot}`} entering={FadeInDown.delay(60 + i * 80).duration(460)}>
              <SpringButton onPress={() => openDetail(q, false)} pressScale={0.97} style={styles.recCard}>
                <Image source={CATEGORY_ICONS[q.category]} style={styles.recIcon} />
                <View style={{ flex: 1, minWidth: 0 }}>
                  <Text style={styles.recTitle} numberOfLines={2}>{q.title}</Text>
                  <View style={styles.recMeta}>
                    <DiffChip diff={q.diff} />
                    <View style={styles.rewardItem}>
                      <Coin />
                      <Text style={styles.coinText}>{q.point}</Text>
                    </View>
                    <View style={styles.rewardItem}>
                      <Star />
                      <Text style={styles.expText}>{q.exp}</Text>
                    </View>
                  </View>
                </View>
                <ChevRight color="#B8A57F" />
              </SpringButton>
            </Animated.View>
          ))}
        </View>

        <SpringButton onPress={() => setRecRot((v) => v + 1)} style={styles.retryBtn}>
          <Text style={styles.retryText}>다시 추천 받기</Text>
        </SpringButton>

        <View style={styles.actionRow}>
          <SpringButton onPress={() => navigation.navigate('QuestRegister')} style={[styles.actionBtn, styles.actionDark]}>
            <Text style={styles.actionDarkText}>퀘스트 등록</Text>
          </SpringButton>
          <SpringButton onPress={() => navigation.navigate('AiRecommend')} style={[styles.actionBtn, styles.actionGold]}>
            <Text style={styles.actionGoldText}>커스텀 추천</Text>
          </SpringButton>
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.screenBg },
  body: { paddingHorizontal: 16, paddingTop: 20, paddingBottom: 28 },

  sectionHead: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 },
  sectionTitle: { fontFamily: fonts.pixel, fontSize: 16, color: colors.primaryDark },
  headRight: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  toggleChip: { borderWidth: 1, borderColor: '#D6E7DC', borderRadius: 999, paddingHorizontal: 8, paddingVertical: 3, backgroundColor: colors.white },
  toggleText: { fontSize: 11, color: colors.textSecondary, fontFamily: fonts.bodyR },

  emptyBox: {
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    borderWidth: 2,
    borderColor: '#C9D6CE',
    borderStyle: 'dashed',
    borderRadius: radii.card,
    paddingVertical: 26,
    paddingHorizontal: 16,
    backgroundColor: 'rgba(255,255,255,0.5)',
    marginBottom: 26,
  },
  emptyText: { fontSize: 13, color: colors.textMuted, fontFamily: fonts.bodyR },
  emptyLink: { fontSize: 13, fontWeight: '700', color: colors.primaryDark, textDecorationLine: 'underline', fontFamily: fonts.bodyB },

  carouselWrap: { marginBottom: 24, marginHorizontal: -16 },
  carouselContent: { paddingHorizontal: 16, paddingVertical: 6 },
  activeCard: {
    borderRadius: radii.card,
    borderWidth: 2,
    borderColor: colors.gold,
    overflow: 'hidden',
    paddingVertical: 14,
    paddingHorizontal: 16,
  },
  activeRow: { flexDirection: 'row', alignItems: 'center', gap: 10, zIndex: 2 },
  activeIconTile: {
    width: 46,
    height: 46,
    borderRadius: 11,
    backgroundColor: 'rgba(255,255,255,0.12)',
    borderWidth: 1,
    borderColor: 'rgba(212,160,23,0.5)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  activeIcon: { width: 34, height: 34 },
  activeTitle: { fontFamily: fonts.pixel, fontSize: 15, color: '#F5EFD8', marginBottom: 5 },
  // 진행중 배지 — QuestCard 배지 스타일 그대로
  progBadge: {
    backgroundColor: 'transparent',
    borderWidth: 1,
    borderColor: '#57C878',
    borderRadius: 999,
    paddingHorizontal: 10,
    paddingVertical: 3,
  },
  progBadgeText: { fontSize: 10, fontWeight: '800', color: '#A8ECBF', fontFamily: fonts.bodyB },

  dots: { flexDirection: 'row', justifyContent: 'center', gap: 6, marginTop: 10 },
  dot: { height: 7, borderRadius: 4 },
  dotOn: { width: 18, backgroundColor: colors.primaryDark },
  dotOff: { width: 7, backgroundColor: '#C9D6CE' },

  recList: { gap: 10, marginBottom: 16 },
  recCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    backgroundColor: colors.parchment,
    borderWidth: 2,
    borderColor: colors.pixelBorder,
    borderRadius: radii.button,
    padding: 11,
  },
  recIcon: { width: 44, height: 44, borderRadius: 10 },
  recTitle: { fontFamily: fonts.pixel, fontSize: 13, color: '#3A2A12', lineHeight: 17, marginBottom: 6 },
  recMeta: { flexDirection: 'row', alignItems: 'center', gap: 6, flexWrap: 'wrap' },

  rewardRow: { flexDirection: 'row', gap: 8 },
  rewardItem: { flexDirection: 'row', alignItems: 'center', gap: 3 },
  coinText: { fontSize: 11, fontWeight: '700', color: '#F2D783', fontFamily: fonts.bodyB },
  expText: { fontSize: 11, fontWeight: '700', color: '#F2D783', fontFamily: fonts.bodyB },

  retryBtn: {
    height: 44,
    borderWidth: 1,
    borderColor: '#D6E7DC',
    borderRadius: radii.input,
    backgroundColor: colors.screenBg,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 14,
  },
  retryText: { fontSize: 14, fontWeight: '700', color: colors.primaryDark, fontFamily: fonts.bodyB },

  actionRow: { flexDirection: 'row', gap: 10 },
  actionBtn: { flex: 1, height: 50, borderRadius: radii.button, alignItems: 'center', justifyContent: 'center' },
  actionDark: { backgroundColor: colors.primaryDark },
  actionDarkText: { color: colors.white, fontSize: 14, fontWeight: '700', fontFamily: fonts.bodyB },
  actionGold: { backgroundColor: colors.gold },
  actionGoldText: { color: '#3A2A12', fontSize: 14, fontWeight: '700', fontFamily: fonts.bodyB },
});
