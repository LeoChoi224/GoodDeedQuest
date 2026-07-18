/**
 * SCREEN 4 · 인증 팝업 (route QuestVerify) — transparent modal over the detail screen.
 * 사진 업로드(placeholder 토글) + 설명 입력(글자수/200) + AI 검토(로딩 → 승인).
 * 인증은 항상 성공 → replace('QuestComplete').
 */
import React, { useState } from 'react';
import { View, Text, StyleSheet, TextInput, Pressable, KeyboardAvoidingView, Platform } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { LinearGradient } from 'expo-linear-gradient';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Animated, { SlideInDown } from 'react-native-reanimated';
import { colors, fonts, radii } from '../../theme';
import SpringButton from '../../components/SpringButton';
import { AiIcon, CameraIcon, SpinnerRing } from './_parts';

type Stage = 'form' | 'loading';

export default function QuestVerifyScreen({ navigation, route }: any) {
  const insets = useSafeAreaInsets();
  const title = route?.params?.title ?? '공원 플로깅';
  const exp = route?.params?.exp ?? 100;
  const point = route?.params?.point ?? 250;

  const [photo, setPhoto] = useState(false);
  const [desc, setDesc] = useState('');
  const [stage, setStage] = useState<Stage>('form');

  const over = desc.length > 200;
  const disabled = !photo || stage === 'loading';

  const onSubmit = () => {
    if (disabled) return;
    setStage('loading');
    // AI 검토는 항상 승인 → 인증 완료로 이동.
    setTimeout(() => {
      navigation.replace('QuestComplete', { exp, point, title });
    }, 1400);
  };

  const submitLabel = photo ? '제출하기' : '사진을 추가해주세요';

  return (
    <View style={styles.root}>
      <StatusBar style="light" />
      <Pressable style={styles.backdrop} onPress={() => navigation.goBack()} />

      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={styles.kav} pointerEvents="box-none">
        <Animated.View entering={SlideInDown.duration(260)} style={[styles.sheet, { paddingBottom: insets.bottom + 20 }]}>
          <View style={styles.handle} />
          <Text style={styles.title}>{title} 인증</Text>

          {/* upload area */}
          <Pressable onPress={() => setPhoto((v) => !v)} style={styles.uploadWrap}>
            {photo ? (
              <LinearGradient colors={['#5B8C6E', '#3E6B52']} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.photoFill}>
                <Text style={styles.photoText}>활동 사진 미리보기</Text>
                <View style={styles.photoClear}>
                  <Text style={styles.photoClearX}>✕</Text>
                </View>
              </LinearGradient>
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
            style={[styles.submit, { backgroundColor: photo ? colors.primaryDark : colors.disabled }]}
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
