/**
 * SCREEN 08-5 · 생성 완료 & 재생 (route: Player — back).
 * ✓ 생성 완료 · 영상 플레이어(placeholder 그라데이션 + ▶/⏸ 토글 + progress) ·
 * 다운로드 → useToast('다운로드 완료') + "영상이 저장되었습니다!" 성공 칩 · 공유.
 * Video aspect follows the design source (08_shortform_flow.dc.html) 16:9 player.
 */
import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { StatusBar } from 'expo-status-bar';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Animated, {
  ZoomIn,
  useSharedValue,
  useAnimatedStyle,
  withTiming,
  cancelAnimation,
  Easing,
} from 'react-native-reanimated';
import HazeBackground from '../../components/HazeBackground';
import MainHeader from '../../components/MainHeader';
import SpringButton from '../../components/SpringButton';
import { useToast } from '../../components/Toast';
import { CheckMark } from '../../components/PixelIcons';
import { colors, fonts } from '../../theme';
import { PlayTri, PauseBars } from './_parts';

export default function PlayerScreen({ navigation, route }: any) {
  const insets = useSafeAreaInsets();
  const toast = useToast();
  const [playing, setPlaying] = useState(false);
  const [saved, setSaved] = useState(false);

  const p = useSharedValue(0.35);
  useEffect(() => {
    if (playing) {
      p.value = withTiming(1, { duration: 8000, easing: Easing.linear });
    } else {
      cancelAnimation(p);
    }
    return () => cancelAnimation(p);
  }, [playing]);
  const fill = useAnimatedStyle(() => ({ width: `${p.value * 100}%` }));

  const onDownload = () => {
    setSaved(true);
    toast.show('다운로드 완료');
  };
  const onShare = () => toast.show('공유 링크가 복사되었습니다');

  return (
    <View style={styles.root}>
      <StatusBar style="light" />
      <HazeBackground />
      <MainHeader showBack onBack={() => navigation.goBack()} />

      <View style={[styles.body, { paddingBottom: insets.bottom + 16 }]}>
        <Text style={styles.done}>✓ 생성 완료</Text>

        {/* 세로형 숏폼 결과 · 영상 플레이어 (placeholder gradient) */}
        <View style={styles.player}>
          <LinearGradient
            colors={['#1a3a2e', '#0a1f18']}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
            style={StyleSheet.absoluteFill}
          />
          <SpringButton onPress={() => setPlaying((v) => !v)} style={styles.playBtn} pressScale={0.9}>
            {playing ? (
              <PauseBars size={26} color={colors.primaryDark} />
            ) : (
              <PlayTri size={26} color={colors.primaryDark} />
            )}
          </SpringButton>
          <View style={styles.progTrack}>
            <Animated.View style={[styles.progFill, fill]} />
          </View>
        </View>

        <SpringButton onPress={onDownload} style={styles.downloadBtn}>
          <Text style={styles.downloadText}>다운로드</Text>
        </SpringButton>

        {saved ? (
          <Animated.View entering={ZoomIn.duration(220)} style={styles.savedWrap}>
            <View style={styles.savedChip}>
              <CheckMark size={15} color="#fff" />
              <Text style={styles.savedText}>영상이 저장되었습니다!</Text>
            </View>
          </Animated.View>
        ) : null}

        <SpringButton onPress={onShare} style={styles.shareBtn}>
          <Text style={styles.shareText}>공유</Text>
        </SpringButton>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.screenBg },
  body: { flex: 1, paddingHorizontal: 16, paddingTop: 16 },
  done: { fontFamily: fonts.pixel, fontSize: 13, color: colors.gold, marginBottom: 8 },

  player: {
    width: '100%',
    aspectRatio: 16 / 9,
    backgroundColor: '#000',
    borderRadius: 12,
    overflow: 'hidden',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 14,
  },
  playBtn: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: 'rgba(255,255,255,0.9)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  progTrack: { position: 'absolute', bottom: 0, left: 0, right: 0, height: 4, backgroundColor: 'rgba(255,255,255,0.2)' },
  progFill: { height: '100%', backgroundColor: colors.gold },

  downloadBtn: {
    height: 52,
    borderRadius: 8,
    backgroundColor: colors.primaryDark,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: colors.primaryDark,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.28,
    shadowRadius: 14,
    elevation: 5,
  },
  downloadText: { fontFamily: fonts.pixel, fontSize: 18, color: colors.parchment },

  savedWrap: { alignItems: 'center', marginTop: 14 },
  savedChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: colors.xpGreen,
    borderRadius: 24,
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  savedText: { color: '#fff', fontSize: 13, fontWeight: '700', fontFamily: fonts.bodyB },

  shareBtn: {
    height: 46,
    borderRadius: 8,
    borderWidth: 1.5,
    borderColor: colors.pixelBorder,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 12,
  },
  shareText: { fontFamily: fonts.pixel, fontSize: 15, color: colors.primaryDark },
});
