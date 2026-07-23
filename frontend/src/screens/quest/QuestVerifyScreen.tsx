/**
 * SCREEN 4 · 인증 팝업 (route QuestVerify) — transparent modal over the detail screen.
 * 사진 업로드(placeholder 토글) + 설명 입력(글자수/200) + AI 검토(로딩 → 승인).
 * 인증은 항상 성공 → replace('QuestComplete').
 */
import React, { useState } from 'react';
import { View, Text, Image, StyleSheet, TextInput, Pressable, KeyboardAvoidingView, Platform } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Animated, { SlideInDown } from 'react-native-reanimated';
import * as ImagePicker from 'expo-image-picker';
import { colors, fonts, radii } from '../../theme';
import SpringButton from '../../components/SpringButton';
import { useToast } from '../../components/Toast';
import { getPresignedUrl, uploadToS3, submitVerification } from '../../api/questVerification';
import { AiIcon, CameraIcon, SpinnerRing } from './_parts';

type Stage = 'form' | 'loading';

export default function QuestVerifyScreen({ navigation, route }: any) {
  const insets = useSafeAreaInsets();
  const title = route?.params?.title ?? '공원 플로깅';
  const exp = route?.params?.exp ?? 100;
  const point = route?.params?.point ?? 250;
  const toast = useToast();
  const questId = route?.params?.questId ?? 1;
  const [photoUri, setPhotoUri] = useState<string | null>(null);
  const [desc, setDesc] = useState('');
  const [stage, setStage] = useState<Stage>('form');

  const over = desc.length > 200;
  const disabled = !photoUri || stage === 'loading';

const pickPhoto = async () => {
  const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
  if (!permission.granted) {
    toast.show('사진 접근 권한을 허용해 주세요.');
    return;
  }
  const result = await ImagePicker.launchImageLibraryAsync({
    mediaTypes: ['images'],
    quality: 0.7,
  });
  if (!result.canceled) {
    setPhotoUri(result.assets[0].uri);
  }
};

  const onSubmit = async () => {
    if (disabled || !photoUri) return;
    setStage('loading');
    try {
      const presign = await getPresignedUrl(questId, 'image/jpeg');
      await uploadToS3(presign.upload_url, photoUri, 'image/jpeg');
      const result = await submitVerification(questId, presign.s3_key);

      if (result.verified) {
        navigation.replace('QuestComplete', {
          exp: result.xp_gained,
          point: result.points_gained,
          title,
        });
      } else {
        setStage('form');
        toast.show(`인증 거절: ${result.reason}`, 4000);
      }
    } catch (err: any) {
      setStage('form');
      toast.show('인증 처리 중 오류가 발생했습니다. 다시 시도해 주세요.');
    }
  };

  const submitLabel = photoUri ? '제출하기' : '사진을 추가해주세요';

  return (
    <View style={styles.root}>
      <StatusBar style="light" />
      <Pressable style={styles.backdrop} onPress={() => navigation.goBack()} />

      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={styles.kav} pointerEvents="box-none">
        <Animated.View entering={SlideInDown.duration(260)} style={[styles.sheet, { paddingBottom: insets.bottom + 20 }]}>
          <View style={styles.handle} />
          <Text style={styles.title}>{title} 인증</Text>

          {/* upload area */}
          <Pressable onPress={pickPhoto} style={styles.uploadWrap}>
            {photoUri ? (
              <View style={styles.photoFill}>
                <Image source={{ uri: photoUri }} style={{ width: '100%', height: '100%' }} resizeMode="cover" />
              </View>
            ) : (
              <View style={styles.photoEmpty}>
                <CameraIcon size={40} color="#8AA598" />
                <Text style={styles.photoAdd}>사진 추가하기</Text>
              </View>
            )}
          </Pressable>

          {/* description */}
          <View style={styles.descWrap}>
            <TextInput
              value={desc}
              onChangeText={setDesc}
              placeholder="활동에 대한 설명을 입력해 주세요"
              placeholderTextColor={colors.textMuted}
              multiline
              style={[styles.textarea, { borderColor: over ? colors.danger : colors.inputBorder }]}
            />
            <Text style={[styles.counter, { color: over ? colors.danger : colors.textMuted }]}>{desc.length}/200</Text>
          </View>

          {/* AI status */}
          <View style={styles.aiInfo}>
            <AiIcon />
            <Text style={styles.aiInfoText}>제출하면 AI가 인증 사진을 검토해요</Text>
          </View>

          {/* submit */}
          <SpringButton
            onPress={onSubmit}
            disabled={disabled}
            style={[styles.submit, { backgroundColor: photoUri ? colors.primaryDark : colors.disabled }]}
          >
            {stage === 'loading' ? (
              <View style={styles.loadingRow}>
                <SpinnerRing size={18} />
                <Text style={styles.submitText}>AI가 검토 중...</Text>
              </View>
            ) : (
              <Text style={styles.submitText}>{submitLabel}</Text>
            )}
          </SpringButton>
        </Animated.View>
      </KeyboardAvoidingView>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1 },
  backdrop: { ...StyleSheet.absoluteFillObject, backgroundColor: 'rgba(0,0,0,0.5)' },
  kav: { flex: 1, justifyContent: 'flex-end' },
  sheet: {
    backgroundColor: colors.white,
    borderTopLeftRadius: radii.cardLg,
    borderTopRightRadius: radii.cardLg,
    paddingHorizontal: 20,
    paddingTop: 14,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -10 },
    shadowOpacity: 0.3,
    shadowRadius: 40,
    elevation: 20,
  },
  handle: { width: 40, height: 5, borderRadius: 3, backgroundColor: colors.inputBorder, alignSelf: 'center', marginBottom: 16 },
  title: { textAlign: 'center', fontFamily: fonts.pixel, fontSize: 16, color: '#3A2A12', marginBottom: 18 },

  uploadWrap: { height: 180, borderRadius: radii.input, overflow: 'hidden', marginBottom: 14 },
  photoEmpty: { flex: 1, borderRadius: radii.input, borderWidth: 2, borderColor: colors.primaryDark, borderStyle: 'dashed', backgroundColor: colors.screenBg, alignItems: 'center', justifyContent: 'center', gap: 8 },
  photoAdd: { fontSize: 15, color: colors.textSecondary, fontWeight: '600', fontFamily: fonts.bodyM },
  photoFill: { flex: 1, borderRadius: radii.input, borderWidth: 2, borderColor: colors.primaryDark, alignItems: 'center', justifyContent: 'center' },
  photoText: { color: 'rgba(255,255,255,0.85)', fontSize: 13, fontWeight: '600', fontFamily: fonts.bodyM },
  photoClear: { position: 'absolute', top: 8, right: 8, width: 26, height: 26, borderRadius: 13, backgroundColor: colors.white, alignItems: 'center', justifyContent: 'center' },
  photoClearX: { fontSize: 14, color: colors.textPrimary },

  descWrap: { position: 'relative', marginBottom: 14 },
  textarea: {
    height: 76,
    borderWidth: 1,
    borderRadius: radii.input,
    paddingTop: 12,
    paddingBottom: 12,
    paddingHorizontal: 14,
    fontSize: 14,
    color: colors.textPrimary,
    fontFamily: fonts.bodyR,
    textAlignVertical: 'top',
  },
  counter: { position: 'absolute', right: 12, bottom: 10, fontSize: 11, fontFamily: fonts.bodyR },

  aiInfo: { flexDirection: 'row', alignItems: 'center', gap: 8, backgroundColor: colors.screenBg, borderRadius: 10, paddingHorizontal: 12, paddingVertical: 10, marginBottom: 16 },
  aiInfoText: { fontSize: 12, fontWeight: '600', color: colors.primaryDark, fontFamily: fonts.bodyM },

  submit: { height: 52, borderRadius: radii.button, alignItems: 'center', justifyContent: 'center' },
  submitText: { color: colors.white, fontSize: 16, fontWeight: '700', fontFamily: fonts.bodyB },
  loadingRow: { flexDirection: 'row', alignItems: 'center', gap: 10 },
});
