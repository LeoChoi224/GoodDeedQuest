/**
 * SCREEN 08-5 · 생성 완료 & 재생 (route: Player — back).
 * ✓ 생성 완료 · 영상 플레이어(video_url 실재생 + ▶/⏸ 토글 + progress) ·
 * 다운로드 → useToast('다운로드 완료') + "영상이 저장되었습니다!" 성공 칩 · 공유.
 * Video aspect follows the design source (08_shortform_flow.dc.html) 16:9 player.
 */
import React, { useState } from 'react';
import { View, Text, StyleSheet, Share, Platform, ActivityIndicator } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Animated, { ZoomIn } from 'react-native-reanimated';
import { useVideoPlayer, VideoView } from 'expo-video';
import { useEvent } from 'expo';
import { File, Paths } from 'expo-file-system';
import * as MediaLibrary from 'expo-media-library';
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
  const [saved, setSaved] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const videoUrl: string | null = route?.params?.videoUrl ?? null;

  const player = useVideoPlayer(videoUrl, (p) => {
    p.loop = true;
    p.timeUpdateEventInterval = 0.25;
  });

  const { isPlaying } = useEvent(player, 'playingChange', { isPlaying: player.playing });
  const { currentTime } = useEvent(player, 'timeUpdate', {
    currentTime: player.currentTime,
    currentLiveTimestamp: null,
    currentOffsetFromLive: null,
    bufferedPosition: 0,
  });
  const duration = player.duration || 0;
  const progress = duration > 0 ? Math.min(currentTime / duration, 1) : 0;

  const togglePlay = () => (isPlaying ? player.pause() : player.play());

  const onDownload = async () => {
    if (!videoUrl) {
      toast.show('영상을 찾을 수 없습니다.');
      return;
    }
    if (downloading) return;
    setDownloading(true);
    try {
      const permission = await MediaLibrary.requestPermissionsAsync();
      if (!permission.granted) {
        toast.show('사진 접근 권한을 허용해 주세요.');
        return;
      }
      const file = await File.downloadFileAsync(videoUrl, Paths.cache);
      await MediaLibrary.saveToLibraryAsync(file.uri);
      setSaved(true);
      toast.show('다운로드 완료');
    } catch (error) {
      console.error('영상 다운로드 실패:', error);
      toast.show('다운로드에 실패했습니다.');
    } finally {
      setDownloading(false);
    }
  };

  const onShare = async () => {
    if (!videoUrl) {
      toast.show('영상을 찾을 수 없습니다.');
      return;
    }
    try {
      await Share.share(Platform.OS === 'ios' ? { url: videoUrl } : { message: videoUrl });
    } catch (error) {
      console.error('공유 실패:', error);
    }
  };

  return (
    <View style={styles.root}>
      <StatusBar style="light" />
      <HazeBackground />
      <MainHeader showBack onBack={() => navigation.goBack()} />

      <View style={[styles.body, { paddingBottom: insets.bottom + 16 }]}>
        <Text style={styles.done}>✓ 생성 완료</Text>

        {/* 세로형 숏폼 결과 · 영상 플레이어 */}
        <View style={styles.player}>
          <VideoView
            player={player}
            style={StyleSheet.absoluteFill}
            contentFit="cover"
            nativeControls={false}
          />
          <SpringButton onPress={togglePlay} style={styles.playBtn} pressScale={0.9}>
            {isPlaying ? (
              <PauseBars size={26} color={colors.primaryDark} />
            ) : (
              <PlayTri size={26} color={colors.primaryDark} />
            )}
          </SpringButton>
          <View style={styles.progTrack}>
            <View style={[styles.progFill, { width: `${progress * 100}%` }]} />
          </View>
        </View>

        <SpringButton onPress={onDownload} disabled={downloading} style={styles.downloadBtn}>
          {downloading ? (
            <ActivityIndicator color={colors.parchment} />
          ) : (
            <Text style={styles.downloadText}>다운로드</Text>
          )}
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
