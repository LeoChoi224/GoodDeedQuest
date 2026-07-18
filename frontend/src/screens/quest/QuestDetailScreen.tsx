/**
 * SCREEN 2 & 3 · 퀘스트 상세 (route QuestDetail) — 진행 전(idle)/진행 중(active).
 * RPG 퀘스트 카드(<QuestCard/> 재사용) + 진행 중일 때 목표 진행 바(PixelProgress).
 * "퀘스트 시작" → iris/scale 와이프 트랜지션 후 active 전환. "퀘스트 인증" → QuestVerify.
 */
import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { LinearGradient } from 'expo-linear-gradient';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { colors, fonts, radii } from '../../theme';
import HazeBackground from '../../components/HazeBackground';
import MainHeader from '../../components/MainHeader';
import SpringButton from '../../components/SpringButton';
import QuestCard from '../../components/QuestCard';
import PixelProgress from '../../components/PixelProgress';
import { SwordIcon } from '../../components/PixelIcons';
import { CameraIcon, StartTransition } from './_parts';

const DEFAULT_DESC =
  '집 근처 공원을 돌며 쓰레기를 주워 봉투에 담아 주세요. 30분 이상 활동하고 인증하면 보상을 받아요.';

export default function QuestDetailScreen({ navigation, route }: any) {
  const insets = useSafeAreaInsets();
  const p = route?.params ?? {};
  const title = p.title ?? '공원 플로깅';
  const category = p.category ?? 'environment';
  const desc = p.desc ?? DEFAULT_DESC;
  const point = p.point ?? 250;
  const exp = p.exp ?? 100;
  const goalLabel = p.goalLabel ?? '쓰레기 줍기';
  const goalMax = p.goalMax ?? 10;

  const [active, setActive] = useState<boolean>(!!p.active);
  const [starting, setStarting] = useState(false);
  const goalCur = active ? p.goalCur ?? 6 : 0;

  const onStart = () => {
    if (starting || active) return;
    setStarting(true);
  };

  return (
    <View style={styles.root}>
      <StatusBar style="light" />
      <HazeBackground />
      <MainHeader showBack title="퀘스트 상세" onBack={() => navigation.goBack()} />

      <ScrollView contentContainerStyle={[styles.body, { paddingBottom: 130 }]} showsVerticalScrollIndicator={false}>
        <QuestCard
          category={category}
          mode={active ? 'active' : 'idle'}
          title={title}
          desc={desc}
          point={point}
          exp={exp}
          showDesc
        />

        {active ? (
          <View style={styles.progressCard}>
            <View style={styles.progressHead}>
              <Text style={styles.progressLabel}>{goalLabel}</Text>
              <Text style={styles.progressCount}>
                {goalCur}
                <Text style={styles.progressMax}> / {goalMax}</Text>
              </Text>
            </View>
            <PixelProgress progress={goalCur / goalMax} height={12} />
          </View>
        ) : null}
      </ScrollView>

      {/* pinned footer */}
      <LinearGradient
        colors={['rgba(243,250,244,0)', '#F3FAF4']}
        locations={[0, 0.35]}
        style={[styles.footer, { paddingBottom: insets.bottom + 20 }]}
      >
        {active ? (
          <SpringButton onPress={() => navigation.navigate('QuestVerify', { title })} style={styles.ctaWrap}>
            <LinearGradient colors={['#0A4F55', colors.primaryDark]} start={{ x: 0.5, y: 0 }} end={{ x: 0.5, y: 1 }} style={styles.ctaGrad}>
              <CameraIcon />
              <Text style={styles.ctaText}>퀘스트 인증</Text>
            </LinearGradient>
          </SpringButton>
        ) : (
          <SpringButton onPress={onStart} style={styles.ctaWrap}>
            <LinearGradient colors={['#0A4F55', colors.primaryDark]} start={{ x: 0.5, y: 0 }} end={{ x: 0.5, y: 1 }} style={styles.ctaGrad}>
              <SwordIcon size={18} />
              <Text style={styles.ctaText}>퀘스트 시작</Text>
            </LinearGradient>
          </SpringButton>
        )}
      </LinearGradient>

      {starting ? (
        <StartTransition
          onDone={() => {
            setStarting(false);
            setActive(true);
          }}
        />
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.screenBg },
  body: { paddingHorizontal: 16, paddingTop: 22 },

  progressCard: {
    marginTop: 22,
    marginHorizontal: 6,
    backgroundColor: colors.white,
    borderRadius: radii.card,
    borderWidth: 1,
    borderColor: '#D6E7DC',
    padding: 16,
    gap: 12,
  },
  progressHead: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  progressLabel: { fontSize: 14, fontWeight: '700', color: colors.textPrimary, fontFamily: fonts.bodyB },
  progressCount: { fontSize: 16, fontWeight: '800', color: colors.xpGreen, fontFamily: fonts.bodyB },
  progressMax: { fontSize: 13, color: colors.textMuted, fontFamily: fonts.bodyR },

  footer: { position: 'absolute', bottom: 0, left: 0, right: 0, paddingHorizontal: 20, paddingTop: 16 },
  ctaWrap: {
    borderRadius: radii.button,
    borderWidth: 2,
    borderColor: '#C9A44C',
    shadowColor: colors.primaryDark,
    shadowOffset: { width: 0, height: 5 },
    shadowOpacity: 0.35,
    shadowRadius: 16,
    elevation: 6,
  },
  ctaGrad: { height: 54, borderRadius: radii.button - 2, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 9 },
  ctaText: { color: '#F5EFD8', fontSize: 16, fontWeight: '700', fontFamily: fonts.bodyB },
});
