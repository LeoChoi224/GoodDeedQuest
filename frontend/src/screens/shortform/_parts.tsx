/**
 * Shortform flow (08) — screen-local building blocks shared by the 3 screens.
 * Icons the shared PixelIcons set doesn't cover (music note, play/pause triangles),
 * the render spinner, the AI-script GamePopup, and the dark music BottomSheet.
 * Motion = Reanimated (transform/opacity + progress-bar fill, matching PixelProgress).
 */
import React, { useEffect, useRef, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Pressable,
  TextInput,
  ScrollView,
  useWindowDimensions,
} from 'react-native';
import Svg, { Path, Circle } from 'react-native-svg';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withRepeat,
  withTiming,
  cancelAnimation,
  Easing,
} from 'react-native-reanimated';
import { colors, fonts } from '../../theme';
import GamePopup from '../../components/GamePopup';
import BottomSheet from '../../components/BottomSheet';
import SpringButton from '../../components/SpringButton';
import Shimmer from '../../components/Shimmer';

/* ----------------------------------------------------------------- palette */
// Dark music-sheet surface (design linear-gradient #0C4249→#052024, approximated solid).
export const sf = {
  sheetBg: '#073A40',
  cream: '#F5ECCB',
  scriptText: '#DCE7DB',
  trackSub: '#8FA79A',
  goldSoft: 'rgba(212,160,23,0.35)',
  goldLine: 'rgba(212,160,23,0.2)',
  glassFill: 'rgba(255,255,255,0.07)',
  chipInactive: 'rgba(255,255,255,0.08)',
  greenTint: 'rgba(76,175,80,0.12)',
} as const;

/* ------------------------------------------------------------------- icons */
export const MusicNoteIcon = ({ size = 30, color = colors.gold }: { size?: number; color?: string }) => (
  <Svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
    <Path d="M9 18V5l10-2v13" />
    <Circle cx={6} cy={18} r={3} />
    <Circle cx={16} cy={16} r={3} />
  </Svg>
);

export const PlayTri = ({ size = 14, color = sf.cream }: { size?: number; color?: string }) => (
  <Svg width={size} height={size} viewBox="0 0 24 24" fill={color}>
    <Path d="M8 5v14l11-7z" />
  </Svg>
);

export const PauseBars = ({ size = 14, color = sf.cream }: { size?: number; color?: string }) => (
  <Svg width={size} height={size} viewBox="0 0 24 24" fill={color}>
    <Path d="M7 5h3v14H7zM14 5h3v14h-3z" />
  </Svg>
);

/* --------------------------------------------------------- render spinner */
// Generating screen: 56×56 ring, top-arc teal, rotating (design sf-spin .8s linear).
export function Spinner() {
  const spin = useSharedValue(0);
  useEffect(() => {
    spin.value = withRepeat(withTiming(1, { duration: 800, easing: Easing.linear }), -1, false);
    return () => cancelAnimation(spin);
  }, []);
  const st = useAnimatedStyle(() => ({ transform: [{ rotate: `${spin.value * 360}deg` }] }));
  return <Animated.View style={[spStyles.ring, st]} />;
}

const spStyles = StyleSheet.create({
  ring: {
    width: 56,
    height: 56,
    borderRadius: 28,
    borderWidth: 5,
    borderColor: '#E7EFE8',
    borderTopColor: colors.primaryDark,
  },
});

/* ----------------------------------------------------- AI 대본 popup (dark) */
const SCRIPT_DEFAULT =
  '오늘도 우리 동네 골목을 깨끗하게 만들었어요.\n작은 손길이 모여 큰 변화를 만듭니다.\n당신의 선행이 세상을 바꿉니다. 🌱';
const SCRIPT_GENERATED =
  '작은 실천이 모여 우리 동네가 환해졌어요.\n오늘의 선행이 내일의 희망이 됩니다.\n함께라서 더 빛나는 하루였어요. 🌱';
const SCRIPT_OPTIMAL =
  '매일의 작은 선행이 세상을 바꿉니다.\n오늘도 따뜻한 마음을 나눴어요.\n당신의 하루가 누군가에겐 큰 힘이 됩니다. ✨';

export function AiScriptPopup({ visible, onClose }: { visible: boolean; onClose: () => void }) {
  const { width } = useWindowDimensions();
  const [text, setText] = useState(SCRIPT_DEFAULT);
  const [loading, setLoading] = useState(false);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => () => { if (timer.current) clearTimeout(timer.current); }, []);

  const close = () => {
    if (timer.current) clearTimeout(timer.current);
    setLoading(false);
    onClose();
  };

  const onGenerate = () => {
    // LLM Story Agent 호출 → 로딩(shimmer) 후 표시
    setLoading(true);
    if (timer.current) clearTimeout(timer.current);
    timer.current = setTimeout(() => {
      setText(SCRIPT_GENERATED);
      setLoading(false);
    }, 1200);
  };

  const onAuto = () => {
    // 최적 대본 자동 삽입 후 닫힘
    setText(SCRIPT_OPTIMAL);
    close();
  };

  return (
    <GamePopup visible={visible} onClose={close} width={Math.min(width - 48, 360)}>
      <View style={ai.header}>
        <Text style={ai.title}>AI대본</Text>
        <Pressable onPress={close} hitSlop={10}>
          <Text style={ai.x}>✕</Text>
        </Pressable>
      </View>

      <View style={ai.scriptBox}>
        {loading ? (
          <View style={{ gap: 12 }}>
            <Shimmer width="100%" height={12} radius={6} />
            <Shimmer width="88%" height={12} radius={6} />
            <Shimmer width="94%" height={12} radius={6} />
            <Shimmer width="62%" height={12} radius={6} />
          </View>
        ) : (
          <TextInput
            value={text}
            onChangeText={setText}
            multiline
            textAlignVertical="top"
            style={ai.scriptInput}
            selectionColor={colors.gold}
          />
        )}
      </View>

      <View style={ai.btnRow}>
        <View style={ai.btnHalf}>
          <SpringButton onPress={onGenerate} style={[ai.btn, ai.btnGenerate]}>
            <Text style={ai.btnGenerateText}>생성하기</Text>
          </SpringButton>
        </View>
        <View style={ai.btnHalf}>
          <SpringButton onPress={onAuto} style={[ai.btn, ai.btnAuto]}>
            <Text style={ai.btnAutoText}>자동 생성</Text>
          </SpringButton>
        </View>
      </View>
    </GamePopup>
  );
}

const ai = StyleSheet.create({
  header: {
    width: '100%',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 14,
  },
  title: { fontFamily: fonts.pixel, fontSize: 18, color: sf.cream },
  x: { color: sf.cream, fontSize: 20 },
  scriptBox: {
    width: '100%',
    minHeight: 240,
    backgroundColor: sf.glassFill,
    borderWidth: 1,
    borderColor: sf.goldSoft,
    borderRadius: 8,
    padding: 14,
  },
  scriptInput: {
    flex: 1,
    minHeight: 212,
    fontSize: 14,
    lineHeight: 24,
    color: sf.scriptText,
    fontFamily: fonts.bodyR,
    padding: 0,
  },
  btnRow: { width: '100%', flexDirection: 'row', gap: 10, marginTop: 16 },
  btnHalf: { flex: 1 },
  btn: { height: 46, borderRadius: 8, alignItems: 'center', justifyContent: 'center' },
  btnGenerate: { backgroundColor: colors.primaryDark, borderWidth: 1.5, borderColor: colors.gold },
  btnGenerateText: { fontFamily: fonts.pixel, fontSize: 15, color: colors.parchment },
  btnAuto: { backgroundColor: colors.xpGreen },
  btnAutoText: { fontFamily: fonts.pixel, fontSize: 15, color: colors.white },
});

/* ------------------------------------------------ 음악 preview inline bar */
function PreviewBar({ name, initPlaying = true }: { name: string; initPlaying?: boolean }) {
  const [playing, setPlaying] = useState(initPlaying);
  const p = useSharedValue(0.12);

  useEffect(() => {
    if (playing) {
      p.value = 0.12;
      p.value = withRepeat(withTiming(0.72, { duration: 3000, easing: Easing.linear }), -1, false);
    } else {
      cancelAnimation(p);
    }
    return () => cancelAnimation(p);
  }, [playing]);

  const fill = useAnimatedStyle(() => ({ width: `${p.value * 100}%` }));

  return (
    <View style={ms.preview}>
      <View style={{ flex: 1 }}>
        <Text style={ms.previewName}>{name}</Text>
        <View style={ms.progTrack}>
          <Animated.View style={[ms.progFill, fill]} />
        </View>
      </View>
      <SpringButton onPress={() => setPlaying((v) => !v)} style={ms.playBtn} pressScale={0.9}>
        {playing ? <PauseBars /> : <PlayTri />}
      </SpringButton>
    </View>
  );
}

/* ---------------------------------------------------- 음악 선택 bottom sheet */
const MUSIC_CATS = ['신나는 노래', '슬픈 노래', '잔잔한', '시끄러운'];
const TRACKS = [
  { name: '따스한 봄날', cat: '잔잔한 · 어쿠스틱' },
  { name: '희망의 아침', cat: '신나는 · 팝' },
  { name: '조용한 위로', cat: '슬픈 · 피아노' },
  { name: '도전의 순간', cat: '시끄러운 · 록' },
  { name: '평화로운 오후', cat: '잔잔한 · 로파이' },
];

export function MusicSheet({ visible, onClose }: { visible: boolean; onClose: () => void }) {
  const { height } = useWindowDimensions();
  const [cat, setCat] = useState(0);
  const [open, setOpen] = useState(0); // index of expanded/previewing track

  return (
    <BottomSheet
      visible={visible}
      onClose={onClose}
      contentStyle={[ms.sheet, { height: Math.round(height * 0.62) }]}
    >
      <View style={{ flex: 1 }}>
        <View style={ms.header}>
          <Text style={ms.title}>음악선택</Text>
          <Pressable onPress={onClose} hitSlop={10}>
            <Text style={ms.x}>✕</Text>
          </Pressable>
        </View>

        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          style={ms.chipsScroll}
          contentContainerStyle={ms.chipsRow}
        >
          {MUSIC_CATS.map((label, i) => {
            const active = i === cat;
            return (
              <Pressable
                key={label}
                onPress={() => setCat(i)}
                style={[ms.chip, active ? ms.chipActive : ms.chipInactive]}
              >
                <Text style={[ms.chipText, active ? ms.chipTextActive : ms.chipTextInactive]}>{label}</Text>
              </Pressable>
            );
          })}
        </ScrollView>

        <ScrollView style={{ flex: 1 }} contentContainerStyle={ms.listPad} showsVerticalScrollIndicator={false}>
          {TRACKS.map((t, i) => (
            <View key={t.name}>
              <Pressable
                style={ms.trackRow}
                onPress={() => setOpen((cur) => (cur === i ? -1 : i))}
              >
                <MusicNoteIcon />
                <View style={{ flex: 1 }}>
                  <Text style={ms.trackName}>{t.name}</Text>
                  <Text style={ms.trackCat}>{t.cat}</Text>
                </View>
              </Pressable>
              {open === i ? <PreviewBar name={t.name} /> : null}
            </View>
          ))}
        </ScrollView>
      </View>
    </BottomSheet>
  );
}

const ms = StyleSheet.create({
  sheet: {
    backgroundColor: sf.sheetBg,
    borderTopWidth: 2,
    borderTopColor: colors.gold,
    paddingHorizontal: 0,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 12,
  },
  title: { fontFamily: fonts.pixel, fontSize: 18, color: sf.cream },
  x: { color: sf.cream, fontSize: 20 },
  chipsScroll: { flexGrow: 0 },
  chipsRow: { gap: 8, paddingHorizontal: 20, paddingTop: 2, paddingBottom: 12 },
  chip: { borderRadius: 20, paddingHorizontal: 14, paddingVertical: 6, borderWidth: 1 },
  chipActive: { backgroundColor: colors.primaryDark, borderColor: colors.gold },
  chipInactive: { backgroundColor: sf.chipInactive, borderColor: sf.goldSoft },
  chipText: { fontSize: 13, fontWeight: '700', fontFamily: fonts.bodyB },
  chipTextActive: { color: colors.parchment },
  chipTextInactive: { color: sf.cream },
  listPad: { paddingHorizontal: 20, paddingBottom: 8 },
  trackRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    paddingVertical: 14,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: sf.goldLine,
  },
  trackName: { fontSize: 15, fontWeight: '600', color: sf.cream, fontFamily: fonts.bodyM },
  trackCat: { fontSize: 13, color: sf.trackSub, fontFamily: fonts.bodyR, marginTop: 2 },
  preview: {
    backgroundColor: sf.greenTint,
    borderWidth: 1,
    borderColor: colors.xpGreen,
    borderRadius: 8,
    paddingVertical: 12,
    paddingHorizontal: 14,
    marginBottom: 10,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  previewName: { fontFamily: fonts.pixel, fontSize: 14, color: sf.cream },
  progTrack: {
    height: 4,
    backgroundColor: 'rgba(255,255,255,0.15)',
    borderRadius: 2,
    marginTop: 8,
    overflow: 'hidden',
  },
  progFill: { height: '100%', backgroundColor: colors.xpGreen, borderRadius: 2 },
  playBtn: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: colors.primaryDark,
    borderWidth: 1.5,
    borderColor: colors.gold,
    alignItems: 'center',
    justifyContent: 'center',
  },
});
