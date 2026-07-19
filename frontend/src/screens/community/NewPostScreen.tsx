/**
 * SCREEN 03·6 — 새 피드 작성 (route: NewPost, back).
 * 진입 시 "퀘스트 인증 내역 불러오기" 팝업(2열 그리드, 셀 탭 → ✓ 토글, 동영상 셀 ▶) →
 * 불러오기 시 선택 미디어를 compose 영역에 로드 + 업로드 버튼 #033236 활성.
 * 본문 입력(글자수 카운터) → 업로드하기 → goBack + Toast('게시되었습니다').
 */
import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, Pressable, TextInput, Modal, KeyboardAvoidingView, Platform } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Animated, { FadeIn, FadeOut, ZoomIn } from 'react-native-reanimated';
import { colors, fonts, radii, shadow } from '../../theme';
import HazeBackground from '../../components/HazeBackground';
import MainHeader from '../../components/MainHeader';
import SpringButton from '../../components/SpringButton';
import { useToast } from '../../components/Toast';
import { GradientFill, WhiteCheck, PlayIcon } from './_parts';

type Media = { id: number; grad: [string, string]; video: boolean };

const MEDIA: Media[] = [
  { id: 0, grad: ['#5B8C6E', '#3E6B52'], video: false },
  { id: 1, grad: ['#3A5A7A', '#24405E'], video: true },
  { id: 2, grad: ['#8A6A4A', '#5E4630'], video: false },
  { id: 3, grad: ['#6A5A8A', '#42305E'], video: false },
];

const BODY_MAX = 500;

export default function NewPostScreen({ navigation }: any) {
  const insets = useSafeAreaInsets();
  const toast = useToast();

  const [modalOpen, setModalOpen] = useState(true); // 진입 시 인증 불러오기 팝업
  const [loaded, setLoaded] = useState<Media[]>([]); // compose 영역에 로드된 미디어
  const [body, setBody] = useState('');

  const hasMedia = loaded.length > 0;

  const onUpload = () => {
    if (!hasMedia) return;
    navigation.goBack();
    toast.show('게시되었습니다');
  };

  return (
    <View style={styles.root}>
      <StatusBar style="light" />
      <HazeBackground />
      <MainHeader showBack title="새 피드작성" onBack={() => navigation.goBack()} />

      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <ScrollView contentContainerStyle={styles.body} showsVerticalScrollIndicator={false} keyboardShouldPersistTaps="handled">
        {/* compose media */}
        <Pressable onPress={() => setModalOpen(true)}>
          {hasMedia ? (
            <GradientFill grad={loaded[0].grad} style={styles.mediaFilled}>
              {loaded.length > 1 ? (
                <View style={styles.countBadge}>
                  <Text style={styles.countBadgeText}>+{loaded.length - 1}</Text>
                </View>
              ) : null}
            </GradientFill>
          ) : (
            <View style={styles.mediaEmpty}>
              <Text style={styles.mediaEmptyText}>미디어를 선택하세요</Text>
            </View>
          )}
        </Pressable>

        {/* 본문 입력 */}
        <View style={styles.field}>
          <TextInput
            value={body}
            onChangeText={setBody}
            placeholder="오늘의 선행을 공유해보세요"
            placeholderTextColor={colors.textMuted}
            multiline
            maxLength={BODY_MAX}
            style={styles.input}
          />
        </View>
        <Text style={styles.counter}>
          {body.length}/{BODY_MAX}
        </Text>
      </ScrollView>

      {/* 업로드 버튼 (미디어 선택 시 활성) */}
      <View style={[styles.footer, { paddingBottom: insets.bottom + 16 }]}>
        <SpringButton
          onPress={onUpload}
          active={hasMedia}
          disabled={!hasMedia}
          bgColors={[colors.disabled, colors.primaryDark]}
          style={[styles.uploadBtn, hasMedia && shadow.button]}
        >
          <Text style={styles.uploadText}>업로드하기</Text>
        </SpringButton>
      </View>
      </KeyboardAvoidingView>

      {/* 퀘스트 인증 내역 불러오기 팝업 */}
      <LoadVerifyModal
        visible={modalOpen}
        onClose={() => setModalOpen(false)}
        onLoad={(sel) => {
          setLoaded(sel);
          setModalOpen(false);
        }}
      />
    </View>
  );
}

/* ---------- 퀘스트 인증 내역 불러오기 (centered white scale-in modal) ---------- */
function LoadVerifyModal({
  visible,
  onClose,
  onLoad,
}: {
  visible: boolean;
  onClose: () => void;
  onLoad: (sel: Media[]) => void;
}) {
  // 초기 선택: design 기본값 (0, 3번 셀 선택됨)
  const [sel, setSel] = useState<Record<number, boolean>>({ 0: true, 3: true });

  const toggle = (id: number) => setSel((s) => ({ ...s, [id]: !s[id] }));
  const chosen = MEDIA.filter((m) => sel[m.id]);

  return (
    <Modal visible={visible} transparent animationType="none" onRequestClose={onClose} statusBarTranslucent>
      <View style={m.center}>
        <Animated.View entering={FadeIn.duration(180)} exiting={FadeOut.duration(160)} style={StyleSheet.absoluteFill}>
          <Pressable style={m.backdrop} onPress={onClose} />
        </Animated.View>

        <Animated.View entering={ZoomIn.duration(200)} exiting={FadeOut.duration(140)} style={m.card}>
          <Text style={m.title}>퀘스트 인증 내역 불러오기</Text>

          <View style={m.grid}>
            {MEDIA.map((item) => (
              <Pressable key={item.id} style={m.cellWrap} onPress={() => toggle(item.id)}>
                <GradientFill grad={item.grad} style={m.cell}>
                  {sel[item.id] ? (
                    <View style={m.checkBadge}>
                      <WhiteCheck size={14} />
                    </View>
                  ) : null}
                  {item.video ? (
                    <View style={m.playSm}>
                      <PlayIcon size={12} />
                    </View>
                  ) : null}
                </GradientFill>
              </Pressable>
            ))}
          </View>

          <View style={m.btnRow}>
            <SpringButton onPress={() => onLoad(chosen)} style={[m.btn, m.load]}>
              <Text style={m.loadText}>불러오기</Text>
            </SpringButton>
            <SpringButton onPress={onClose} style={[m.btn, m.cancel]}>
              <Text style={m.cancelText}>취소</Text>
            </SpringButton>
          </View>
        </Animated.View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.screenBg },
  body: { padding: 16, paddingBottom: 32 },

  mediaEmpty: {
    width: '100%',
    aspectRatio: 1,
    borderRadius: 14,
    borderWidth: 2,
    borderStyle: 'dashed',
    borderColor: '#C9D6CE',
    backgroundColor: 'rgba(255,255,255,0.5)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  mediaEmptyText: { fontSize: 13, color: colors.textMuted, fontFamily: fonts.bodyR },
  mediaFilled: { width: '100%', aspectRatio: 1, borderRadius: 14, overflow: 'hidden' },
  countBadge: {
    position: 'absolute',
    top: 10,
    right: 10,
    paddingHorizontal: 10,
    height: 26,
    borderRadius: 13,
    backgroundColor: 'rgba(3,50,54,0.72)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  countBadgeText: { color: colors.white, fontSize: 12, fontWeight: '700', fontFamily: fonts.bodyB },

  field: {
    marginTop: 16,
    borderRadius: radii.input,
    borderWidth: 1,
    borderColor: colors.inputBorder,
    backgroundColor: colors.white,
  },
  input: { minHeight: 120, padding: 14, fontSize: 15, color: colors.textPrimary, fontFamily: fonts.bodyR, textAlignVertical: 'top' },
  counter: { alignSelf: 'flex-end', marginTop: 6, fontSize: 12, color: colors.textMuted, fontFamily: fonts.bodyR },

  footer: { position: 'absolute', bottom: 0, left: 0, right: 0, paddingHorizontal: 20, paddingTop: 12, backgroundColor: colors.screenBg },
  uploadBtn: { height: 52, borderRadius: radii.button, alignItems: 'center', justifyContent: 'center' },
  uploadText: { color: colors.white, fontSize: 16, fontWeight: '700', fontFamily: fonts.bodyB },
});

const m = StyleSheet.create({
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 16 },
  backdrop: { flex: 1, backgroundColor: 'rgba(0,0,0,0.45)' },
  card: {
    width: '100%',
    maxWidth: 361,
    backgroundColor: colors.white,
    borderRadius: 14,
    padding: 16,
    ...shadow.card,
    shadowOpacity: 0.35,
    shadowRadius: 50,
  },
  title: { textAlign: 'center', fontSize: 15, fontWeight: '700', color: colors.textPrimary, marginBottom: 14, fontFamily: fonts.bodyB },
  grid: { flexDirection: 'row', flexWrap: 'wrap', marginHorizontal: -3, marginBottom: 16 },
  cellWrap: { width: '50%', padding: 3 },
  cell: { width: '100%', aspectRatio: 1, borderRadius: 10, overflow: 'hidden' },
  checkBadge: {
    position: 'absolute',
    top: 6,
    right: 6,
    width: 22,
    height: 22,
    borderRadius: 11,
    backgroundColor: colors.primaryDark,
    alignItems: 'center',
    justifyContent: 'center',
  },
  playSm: {
    position: 'absolute',
    bottom: 6,
    left: 6,
    width: 22,
    height: 22,
    borderRadius: 11,
    backgroundColor: 'rgba(0,0,0,0.45)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  btnRow: { flexDirection: 'row', gap: 10 },
  btn: { flex: 1, height: 44, borderRadius: 10, alignItems: 'center', justifyContent: 'center' },
  load: { backgroundColor: colors.primaryDark },
  loadText: { color: colors.white, fontSize: 14, fontWeight: '700', fontFamily: fonts.bodyB },
  cancel: { backgroundColor: colors.googleBg },
  cancelText: { color: colors.textPrimary, fontSize: 14, fontWeight: '600', fontFamily: fonts.bodyM },
});
