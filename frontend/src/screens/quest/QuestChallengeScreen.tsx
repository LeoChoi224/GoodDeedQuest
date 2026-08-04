/**
 * SCREEN · 추가 인증 (route QuestChallenge)
 * 진위가 의심스러운 제출에 서버가 발급한 4자리 코드를 보여주고,
 * 사용자가 종이에 손으로 적어 찍은 사진을 받아 최종 판정한다.
 */
import React, { useState } from 'react';
import { View, Text, Image, StyleSheet, Pressable, ScrollView } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import * as ImagePicker from 'expo-image-picker';
import { colors, fonts, radii, shadow } from '../../theme';
import HazeBackground from '../../components/HazeBackground';
import MainHeader from '../../components/MainHeader';
import SpringButton from '../../components/SpringButton';
import { useToast } from '../../components/Toast';
import { uploadOne, submitChallenge } from '../../api/questVerification';
import { CameraIcon, SpinnerRing } from './_parts';

type Stage = 'form' | 'uploading' | 'verifying';

export default function QuestChallengeScreen({ navigation, route }: any) {
  const insets = useSafeAreaInsets();
  const toast = useToast();
  const code = route?.params?.code ?? '----';
  const submissionId = route?.params?.submissionId;
  const questId = route?.params?.questId ?? 1;
  const title = route?.params?.title ?? '퀘스트';

  const [photoUri, setPhotoUri] = useState<string | null>(null);
  const [stage, setStage] = useState<Stage>('form');

  const disabled = !photoUri || stage !== 'form';

  const takePhoto = async () => {
    if (stage !== 'form') return;
    const permission = await ImagePicker.requestCameraPermissionsAsync();
    if (!permission.granted) {
      toast.show('카메라 권한을 허용해 주세요.');
      return;
    }
    const result = await ImagePicker.launchCameraAsync({ mediaTypes: ['images'], quality: 0.7 });
    if (!result.canceled) setPhotoUri(result.assets[0].uri);
  };

  const choosePhoto = async () => {
    if (stage !== 'form') return;
    const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!permission.granted) {
      toast.show('사진 접근 권한을 허용해 주세요.');
      return;
    }
    const result = await ImagePicker.launchImageLibraryAsync({ mediaTypes: ['images'], quality: 0.7 });
    if (!result.canceled) setPhotoUri(result.assets[0].uri);
  };

  const onSubmit = async () => {
    if (disabled || !photoUri) return;
    if (!submissionId) {
      toast.show('인증 정보를 찾을 수 없습니다. 처음부터 다시 시도해 주세요.');
      return;
    }
    setStage('uploading');
    try {
      const s3Key = await uploadOne(questId, photoUri);
      setStage('verifying');
      const result = await submitChallenge(submissionId, s3Key);

      if (result.verified) {
        navigation.replace('QuestComplete', {
          exp: result.xp_gained,
          point: result.points_gained,
          title,
          unlockedBadges: result.unlocked_badges,
        });
      } else {
        setStage('form');
        toast.show(result.reason, 4000);
      }
    } catch (err: any) {
      setStage('form');
      const detail = err?.response?.data?.detail;
      toast.show(typeof detail === 'string' ? detail : '인증 처리 중 오류가 발생했습니다. 다시 시도해 주세요.');
    }
  };

  return (
    <View style={styles.root}>
      <StatusBar style="dark" />
      <HazeBackground />
      <MainHeader showBack title="추가 인증" onBack={() => navigation.goBack()} />

      <ScrollView contentContainerStyle={[styles.body, { paddingBottom: insets.bottom + 120 }]} showsVerticalScrollIndicator={false}>
        <Text style={styles.h1}>본인 확인이 필요해요</Text>
        <Text style={styles.desc}>
          제출하신 자료의 진위를 확인하기 위해 한 번만 더 확인할게요.{'\n'}
          아래 번호를 종이에 <Text style={styles.bold}>손으로 적고</Text> 사진을 찍어 주세요.
        </Text>

        <View style={styles.codeCard}>
          <Text style={styles.codeLabel}>인증 번호</Text>
          <Text style={styles.code}>{code}</Text>
        </View>

        <View style={styles.tipBox}>
          <Text style={styles.tipText}>
            · 화면에 띄운 숫자나 인쇄물은 인정되지 않아요{'\n'}
            · 번호가 잘 보이게 찍어 주세요
          </Text>
        </View>

        <Pressable onPress={photoUri ? undefined : takePhoto} style={styles.photoWrap}>
          {photoUri ? (
            <View style={styles.photoFill}>
              <Image source={{ uri: photoUri }} style={StyleSheet.absoluteFill} resizeMode="cover" />
              <Pressable onPress={() => setPhotoUri(null)} hitSlop={8} style={styles.photoClear}>
                <Text style={styles.photoClearX}>×</Text>
              </Pressable>
            </View>
          ) : (
            <View style={styles.photoEmpty}>
              <CameraIcon size={40} color="#8AA598" />
              <Text style={styles.photoAdd}>사진 촬영하기</Text>
            </View>
          )}
        </Pressable>

        {!photoUri && (
          <Pressable onPress={choosePhoto} hitSlop={6} style={styles.galleryBtn}>
            <Text style={styles.galleryText}>이미 찍어둔 사진 선택하기</Text>
          </Pressable>
        )}
      </ScrollView>

      <View style={[styles.footer, { paddingBottom: insets.bottom + 20 }]}>
        <SpringButton
          onPress={onSubmit}
          disabled={disabled}
          style={[styles.submit, shadow.button, { backgroundColor: photoUri ? colors.primaryDark : colors.disabled }]}
        >
          {stage !== 'form' ? (
            <View style={styles.loadingRow}>
              <SpinnerRing size={18} />
              <Text style={styles.submitText}>{stage === 'uploading' ? '사진 업로드 중...' : 'AI가 확인 중...'}</Text>
            </View>
          ) : (
            <Text style={styles.submitText}>{photoUri ? '제출하기' : '사진을 촬영해주세요'}</Text>
          )}
        </SpringButton>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.screenBg },
  body: { paddingHorizontal: 20, paddingTop: 24 },
  h1: { fontSize: 20, fontWeight: '700', color: colors.textPrimary, marginBottom: 10, fontFamily: fonts.bodyB },
  desc: { fontSize: 14, lineHeight: 21, color: colors.textSecondary, marginBottom: 22, fontFamily: fonts.bodyR },
  bold: { fontWeight: '700', color: colors.primaryDark, fontFamily: fonts.bodyB },

  codeCard: {
    backgroundColor: colors.white, borderRadius: radii.card, borderWidth: 2, borderColor: colors.primaryDark,
    alignItems: 'center', paddingVertical: 22, marginBottom: 14,
  },
  codeLabel: { fontSize: 12, fontWeight: '600', color: colors.textMuted, marginBottom: 8, fontFamily: fonts.bodyM },
  code: { fontSize: 44, letterSpacing: 10, color: colors.primaryDark, fontFamily: fonts.pixel },

  tipBox: { backgroundColor: colors.white, borderRadius: 10, paddingHorizontal: 14, paddingVertical: 12, marginBottom: 20 },
  tipText: { fontSize: 12, lineHeight: 19, color: colors.textMuted, fontFamily: fonts.bodyR },

  photoWrap: { height: 200, borderRadius: radii.input, overflow: 'hidden' },
  photoEmpty: {
    flex: 1, borderRadius: radii.input, borderWidth: 2, borderColor: colors.primaryDark, borderStyle: 'dashed',
    backgroundColor: colors.white, alignItems: 'center', justifyContent: 'center', gap: 8,
  },
  photoAdd: { fontSize: 15, color: colors.textSecondary, fontWeight: '600', fontFamily: fonts.bodyM },
  photoFill: { flex: 1, borderRadius: radii.input, borderWidth: 2, borderColor: colors.primaryDark, overflow: 'hidden' },
  photoClear: {
    position: 'absolute', top: 8, right: 8, width: 26, height: 26, borderRadius: 13,
    backgroundColor: colors.white, alignItems: 'center', justifyContent: 'center',
  },
  photoClearX: { fontSize: 15, lineHeight: 17, color: colors.textPrimary },

  galleryBtn: { alignSelf: 'center', marginTop: 14 },
  galleryText: { fontSize: 13, fontWeight: '600', color: colors.primaryDark, textDecorationLine: 'underline', fontFamily: fonts.bodyM },

  footer: { position: 'absolute', bottom: 0, left: 0, right: 0, paddingHorizontal: 20, paddingTop: 16, backgroundColor: colors.screenBg },
  submit: { height: 52, borderRadius: radii.button, alignItems: 'center', justifyContent: 'center' },
  submitText: { color: colors.white, fontSize: 16, fontWeight: '700', fontFamily: fonts.bodyB },
  loadingRow: { flexDirection: 'row', alignItems: 'center', gap: 10 },
});
