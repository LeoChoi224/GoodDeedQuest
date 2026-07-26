/**
 * 인증용 동영상 선택기 — GOOD_DEED(개인 선행) 퀘스트에서 사용.
 * 고른 영상을 바로 재생해 확인할 수 있고, 길이 제한을 넘으면 선택을 거절한다.
 */
import React, { useEffect } from 'react';
import { View, Text, StyleSheet, Pressable } from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { useVideoPlayer, VideoView } from 'expo-video';
import { colors, fonts, radii } from '../theme';
import { useToast } from './Toast';
import { CameraIcon } from '../screens/quest/_parts';

type Props = {
  videoUri: string | null;
  onChange: (uri: string | null) => void;
  maxSeconds?: number;
  disabled?: boolean;
};

export default function VideoPicker({ videoUri, onChange, maxSeconds = 30, disabled = false }: Props) {
  const toast = useToast();
  const player = useVideoPlayer(videoUri, (p) => {
    p.loop = true;
  });

  // 영상을 지웠다가 다시 고를 때 이전 재생이 남지 않도록 정지
  useEffect(() => {
    if (!videoUri) player.pause();
  }, [videoUri]);

  const pick = async () => {
    if (disabled) return;
    const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!permission.granted) {
      toast.show('사진 접근 권한을 허용해 주세요.');
      return;
    }
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ['videos'],
      quality: 0.7,
    });
    if (result.canceled) return;

    const asset = result.assets[0];
    // duration은 밀리초. 너무 긴 영상은 업로드·판정 비용이 커져 미리 막는다.
    const seconds = asset.duration ? asset.duration / 1000 : 0;
    if (seconds > maxSeconds) {
      toast.show(`${maxSeconds}초 이하의 영상만 올릴 수 있어요.`);
      return;
    }
    onChange(asset.uri);
  };

  return (
    <View>
      <Pressable onPress={videoUri ? undefined : pick} style={styles.wrap}>
        {videoUri ? (
          <View style={styles.fill}>
            <VideoView player={player} style={StyleSheet.absoluteFill} contentFit="cover" nativeControls />
            <Pressable onPress={() => onChange(null)} hitSlop={8} style={styles.clear}>
              <Text style={styles.clearX}>×</Text>
            </Pressable>
          </View>
        ) : (
          <View style={styles.empty}>
            <CameraIcon size={40} color="#8AA598" />
            <Text style={styles.emptyText}>동영상 추가하기</Text>
            <Text style={styles.hint}>{maxSeconds}초 이하</Text>
          </View>
        )}
      </Pressable>

      {videoUri && (
        <Pressable onPress={pick} hitSlop={6} style={styles.changeBtn}>
          <Text style={styles.changeText}>다른 영상 고르기</Text>
        </Pressable>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { height: 200, borderRadius: radii.input, overflow: 'hidden' },
  empty: {
    flex: 1, borderRadius: radii.input, borderWidth: 2, borderColor: colors.primaryDark,
    borderStyle: 'dashed', backgroundColor: colors.screenBg,
    alignItems: 'center', justifyContent: 'center', gap: 6,
  },
  emptyText: { fontSize: 15, color: colors.textSecondary, fontWeight: '600', fontFamily: fonts.bodyM },
  hint: { fontSize: 11, color: colors.textMuted, fontFamily: fonts.bodyR },
  fill: { flex: 1, borderRadius: radii.input, borderWidth: 2, borderColor: colors.primaryDark, overflow: 'hidden', backgroundColor: '#000' },
  clear: {
    position: 'absolute', top: 8, right: 8, width: 26, height: 26, borderRadius: 13,
    backgroundColor: colors.white, alignItems: 'center', justifyContent: 'center', zIndex: 2,
  },
  clearX: { fontSize: 15, lineHeight: 17, color: colors.textPrimary },
  changeBtn: { alignSelf: 'flex-start', marginTop: 8 },
  changeText: { fontSize: 12, fontWeight: '700', color: colors.primaryDark, textDecorationLine: 'underline', fontFamily: fonts.bodyM },
});
