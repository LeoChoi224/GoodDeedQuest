/**
 * SCREEN 08-4 · 숏폼 생성 로딩 (route: Generating — fade in, no back while generating).
 * 진입 시 /generate 호출 후 /status를 4초 간격으로 폴링한다.
 * COMPLETED면 Player로 replace, FAILED면 error_message를 보여주고 뒤로 갈 수 있게 한다.
 */
import React, { useEffect, useRef, useState } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import Animated, { FadeIn } from 'react-native-reanimated';
import HazeBackground from '../../components/HazeBackground';
import MainHeader from '../../components/MainHeader';
import SpringButton from '../../components/SpringButton';
import { colors, fonts } from '../../theme';
import { GeneratingProgressBar } from './_parts'; // ⭐ 수정: 원형 스피너 제거, 진행 바만 사용
import { generateVideo, getShortformStatus, CaptionItem } from '../../api/shortform';

const POLL_INTERVAL_MS = 4000;

// ⭐ 수정: 백엔드가 세부 진행률(%)을 내려주지 않으므로, 폴링 틱마다 한 단계씩
// 넘어가는 연출용 단계 문구. 실제 파이프라인 순서(자막/BGM 확정 → 장면 합성 →
// 렌더링 → 업로드)를 대략적으로 따라간다.
const GENERATING_STAGES = [
  '요청을 접수하고 있어요...',
  '자막과 배경음악을 확인하고 있어요...',
  '장면을 이어붙이고 있어요...',
  '영상을 렌더링하고 있어요...',
  '마무리하고 있어요...',
];

export default function GeneratingScreen({ navigation, route }: any) {
  const shortsId: number | undefined = route?.params?.shortsId;
  const mediaKeys: string[] = route?.params?.mediaKeys ?? [];
  const captions: CaptionItem[] | null = route?.params?.captions ?? null;

  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [stageIndex, setStageIndex] = useState(0); // ⭐ 수정: 진행 연출용 단계 인덱스
  const pollTimer = useRef<ReturnType<typeof setInterval> | null>(null);
  const stopped = useRef(false);

  useEffect(() => {
    stopped.current = false;
    setStageIndex(0); // ⭐ 수정

    const stopPolling = () => {
      if (pollTimer.current) {
        clearInterval(pollTimer.current);
        pollTimer.current = null;
      }
    };

    const startPolling = () => {
      pollTimer.current = setInterval(async () => {
        try {
          const result = await getShortformStatus(shortsId as number);
          if (stopped.current) return;
          if (result.status === 'COMPLETED') {
            stopPolling();
            navigation.replace('Player', { videoUrl: result.video_url, shortsId });
          } else if (result.status === 'FAILED') {
            stopPolling();
            setErrorMessage(result.error_message ?? '영상 생성에 실패했습니다.');
          } else {
            // ⭐ 수정: 아직 진행 중 — 폴링 틱마다 한 단계씩 진행 연출을 넘긴다
            setStageIndex((i) => Math.min(i + 1, GENERATING_STAGES.length - 1));
          }
        } catch (error: any) {
          // ⭐ 임시 진단 로깅 (이슈 #196) - 원인 파악되면 제거
          console.error('숏폼 상태 조회 실패:', {
            message: error?.message,
            code: error?.code,
            url: error?.config?.url,
            baseURL: error?.config?.baseURL,
          });
        }
      }, POLL_INTERVAL_MS);
    };

    (async () => {
      // shortsId/captions는 PhotoSelectScreen에서 navigate 파라미터로 전달되는데,
      // AI 대본 없이(=captions가 비어있는 채로) 여기까지 왔다면 /generate가 400을 뱉기 전에
      // 미리 걸러서 사용자에게 원인을 보여준다.
      if (!shortsId || !captions || captions.length === 0) {
        setErrorMessage('대본이 준비되지 않았습니다. 이전 화면에서 AI 대본을 먼저 생성해주세요.');
        return;
      }
      try {
        await generateVideo(shortsId, mediaKeys, captions);
        if (stopped.current) return;
        startPolling();
      } catch (error: any) {
        console.error('영상 생성 요청 실패:', error);
        const detail = error?.response?.data?.detail;
        setErrorMessage(typeof detail === 'string' ? detail : '영상 생성 요청에 실패했습니다.');
      }
    })();

    return () => {
      stopped.current = true;
      stopPolling();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [shortsId]);

  if (errorMessage) {
    return (
      <View style={styles.root}>
        <StatusBar style="light" />
        <HazeBackground />
        <MainHeader showBack onBack={() => navigation.goBack()} />

        <Animated.View entering={FadeIn.duration(260)} style={styles.center}>
          <Text style={styles.errorTitle}>영상 생성에 실패했습니다</Text>
          <Text style={styles.errorSub}>{errorMessage}</Text>
          <SpringButton onPress={() => navigation.goBack()} style={styles.retryBtn}>
            <Text style={styles.retryText}>돌아가기</Text>
          </SpringButton>
        </Animated.View>
      </View>
    );
  }

  return (
    <View style={styles.root}>
      <StatusBar style="light" />
      <HazeBackground />
      <MainHeader />

      {/* ⭐ 수정: 원형 스피너 제거 — 텍스트 + 진행 바만 화면 중앙에 배치 */}
      <Animated.View entering={FadeIn.duration(260)} style={styles.center}>
        <Text style={styles.title}>영상을 생성하는 중입니다...</Text>
        <Text style={styles.sub}>{GENERATING_STAGES[stageIndex]}</Text>
        <GeneratingProgressBar progress={(stageIndex + 1) / GENERATING_STAGES.length} />
      </Animated.View>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.screenBg },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 24 },
  title: { fontFamily: fonts.pixel, fontSize: 16, color: colors.primaryDark, marginBottom: 8 }, // ⭐ 수정: 스피너 제거로 marginTop 불필요
  sub: { fontSize: 12, color: '#888', textAlign: 'center', fontFamily: fonts.bodyR },

  errorTitle: { fontFamily: fonts.pixel, fontSize: 16, color: colors.danger, marginBottom: 10, textAlign: 'center' },
  errorSub: { fontSize: 13, color: '#888', textAlign: 'center', fontFamily: fonts.bodyR, marginBottom: 24, lineHeight: 20 },
  retryBtn: {
    height: 46,
    minWidth: 160,
    borderRadius: 8,
    backgroundColor: colors.primaryDark,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 24,
  },
  retryText: { fontFamily: fonts.pixel, fontSize: 15, color: colors.parchment },
});
