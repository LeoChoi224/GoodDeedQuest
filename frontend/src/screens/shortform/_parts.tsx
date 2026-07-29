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
import { useToast } from '../../components/Toast';
import {
  generateScript,
  updateScript,
  getBackgroundMusicList,
  CaptionItem,
  ScriptGenerateResult,
  BackgroundMusic,
} from '../../api/shortform';

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
// captions(항목별 자막 배열) <-> 편집용 단일 textarea 사이 변환.
// 줄 수가 안 맞아도 원본 CaptionItem의 media_s3_key/order는 그대로 유지하고 caption 텍스트만 갈아끼운다.
function captionsToText(captions: CaptionItem[]): string {
  return captions
    .slice()
    .sort((a, b) => a.order - b.order)
    .map((c) => c.caption)
    .join('\n');
}
function textToCaptions(text: string, original: CaptionItem[]): CaptionItem[] {
  const lines = text.split('\n');
  return original.map((c, i) => ({ ...c, caption: (lines[i] ?? c.caption).slice(0, 200) }));
}

export function AiScriptPopup({
  visible,
  onClose,
  shortsId,
  mediaKeys,
  questTitleResolver,
  onConfirmed,
  onAutoGenerate,
}: {
  visible: boolean;
  onClose: () => void;
  shortsId: number | null;
  mediaKeys: string[];
  questTitleResolver: () => Promise<string>;
  onConfirmed: (result: ScriptGenerateResult) => void;
  /** "자동 생성" - 대본 생성뿐 아니라 음악 자동 매칭 + 숏폼 생성 화면 이동까지 부모가 전부 처리한다. */
  onAutoGenerate: () => Promise<void>;
}) {
  const { width } = useWindowDimensions();
  const toast = useToast();
  const [text, setText] = useState('');
  const [title, setTitle] = useState('');
  const [captions, setCaptions] = useState<CaptionItem[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [closing, setClosing] = useState(false);

  const runGenerate = async (): Promise<ScriptGenerateResult | null> => {
    if (shortsId == null || mediaKeys.length === 0) {
      toast.show('사진을 먼저 선택해주세요.');
      return null;
    }
    setLoading(true);
    try {
      const questTitle = await questTitleResolver();
      const result = await generateScript(shortsId, mediaKeys, questTitle);
      setCaptions(result.captions);
      setTitle(result.title);
      setText(captionsToText(result.captions));
      return result;
    } catch (error) {
      console.error('AI 대본 생성 실패:', error);
      toast.show('AI 대본 생성에 실패했습니다.');
      return null;
    } finally {
      setLoading(false);
    }
  };

  const onGenerate = () => {
    runGenerate();
  };

  // 대본을 팝업에서 보여주지 않고, 대본+음악 자동 매칭+숏폼 생성까지 부모가 한 번에 처리한다.
  const onAuto = async () => {
    if (mediaKeys.length === 0) {
      toast.show('사진을 먼저 선택해주세요.');
      return;
    }
    setLoading(true);
    try {
      await onAutoGenerate();
    } catch (error) {
      console.error('자동 생성 실패:', error);
      toast.show('자동 생성에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  // 사용자가 캡션을 수정했으면 닫히기 전에 검증(stateless)부터 통과시킨다 - 실패하면 닫지 않는다.
  const close = async () => {
    if (!captions) {
      onClose();
      return;
    }
    const edited = textToCaptions(text, captions);
    const changed = edited.some((c, i) => c.caption !== captions[i].caption);
    if (!changed) {
      onConfirmed({ shorts_id: shortsId as number, status: 'PENDING', title, captions });
      onClose();
      return;
    }
    try {
      setClosing(true);
      const validated = await updateScript(shortsId as number, title, edited);
      setCaptions(validated.captions);
      onConfirmed(validated);
      onClose();
    } catch (error: any) {
      const message = error?.response?.data?.detail ?? '수정한 대본 검증에 실패했습니다.';
      toast.show(message);
    } finally {
      setClosing(false);
    }
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
            placeholder="'생성하기'를 눌러 AI 대본을 만들어보세요"
            placeholderTextColor={sf.trackSub}
            style={ai.scriptInput}
            selectionColor={colors.gold}
            editable={!!captions}
          />
        )}
      </View>

      <View style={ai.btnRow}>
        <View style={ai.btnHalf}>
          <SpringButton onPress={onGenerate} disabled={loading || closing} style={[ai.btn, ai.btnGenerate]}>
            <Text style={ai.btnGenerateText}>생성하기</Text>
          </SpringButton>
        </View>
        <View style={ai.btnHalf}>
          <SpringButton onPress={onAuto} disabled={loading || closing} style={[ai.btn, ai.btnAuto]}>
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
// TODO: 실제 오디오 미리듣기 미구현 - BackgroundMusic.preview_url로 재생 붙이기 (현재는 애니메이션만).
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
export function MusicSheet({
  visible,
  onClose,
  selectedBgmId,
  onSelect,
}: {
  visible: boolean;
  onClose: () => void;
  selectedBgmId: number | null;
  onSelect: (bgm: BackgroundMusic) => void;
}) {
  const { height } = useWindowDimensions();
  const [cat, setCat] = useState(0);
  const [categories, setCategories] = useState<string[]>(['전체']);
  const [tracks, setTracks] = useState<BackgroundMusic[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState<number | null>(null); // index of expanded/previewing track
  const skipFirstFetch = useRef(true);

  // 시트를 열 때마다 전체 목록을 다시 받아와 트랙 + mood_tag 카테고리 칩을 구성한다.
  // (이전에 특정 카테고리로 필터링한 채 닫았어도 다음에 열면 '전체'로 리셋)
  useEffect(() => {
    if (!visible) return;
    skipFirstFetch.current = true;
    setCat(0);
    let mounted = true;
    (async () => {
      try {
        setLoading(true);
        setError(null);
        const result = await getBackgroundMusicList();
        if (!mounted) return;
        const moodTags = Array.from(
          new Set(result.items.map((t) => t.mood_tag).filter((t): t is string => !!t)),
        );
        setCategories(['전체', ...moodTags]);
        setTracks(result.items);
      } catch (e) {
        console.error('배경음악 목록 조회 실패:', e);
        if (mounted) setError('음악 목록을 불러오지 못했습니다.');
      } finally {
        if (mounted) setLoading(false);
      }
    })();
    return () => {
      mounted = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [visible]);

  // 카테고리 칩 선택 시 해당 mood_tag로 다시 조회한다 (최초 전체 조회 직후 1회는 건너뜀).
  useEffect(() => {
    if (skipFirstFetch.current) {
      skipFirstFetch.current = false;
      return;
    }
    let mounted = true;
    (async () => {
      try {
        setLoading(true);
        setError(null);
        const moodTag = cat === 0 ? undefined : categories[cat];
        const result = await getBackgroundMusicList(moodTag);
        if (mounted) setTracks(result.items);
      } catch (e) {
        console.error('배경음악 목록 조회 실패:', e);
        if (mounted) setError('음악 목록을 불러오지 못했습니다.');
      } finally {
        if (mounted) setLoading(false);
      }
    })();
    return () => {
      mounted = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cat]);

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
          {categories.map((label, i) => {
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

        {loading ? (
          <View style={ms.stateWrap}>
            <Text style={ms.stateText}>음악 목록을 불러오는 중입니다</Text>
          </View>
        ) : error ? (
          <View style={ms.stateWrap}>
            <Text style={ms.stateText}>{error}</Text>
          </View>
        ) : tracks.length === 0 ? (
          <View style={ms.stateWrap}>
            <Text style={ms.stateText}>이 분위기의 음악이 아직 없습니다</Text>
          </View>
        ) : (
          <ScrollView style={{ flex: 1 }} contentContainerStyle={ms.listPad} showsVerticalScrollIndicator={false}>
            {tracks.map((t, i) => {
              const selected = t.bgm_id === selectedBgmId;
              return (
                <View key={t.bgm_id}>
                  <Pressable
                    style={ms.trackRow}
                    onPress={() => {
                      setOpen((cur) => (cur === i ? null : i));
                      onSelect(t);
                    }}
                  >
                    <MusicNoteIcon />
                    <View style={{ flex: 1 }}>
                      <Text style={ms.trackName}>{t.title}</Text>
                      <Text style={ms.trackCat}>{t.mood_tag ?? ''}</Text>
                    </View>
                    {selected ? (
                      <View style={ms.selectedBadge}>
                        <Text style={ms.selectedBadgeText}>✓</Text>
                      </View>
                    ) : null}
                  </Pressable>
                  {open === i ? <PreviewBar name={t.title} /> : null}
                </View>
              );
            })}
          </ScrollView>
        )}
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
  selectedBadge: {
    width: 22,
    height: 22,
    borderRadius: 11,
    backgroundColor: colors.gold,
    alignItems: 'center',
    justifyContent: 'center',
  },
  selectedBadgeText: { color: colors.primaryDark, fontSize: 13, fontWeight: '800' },
  stateWrap: { paddingVertical: 40, alignItems: 'center', justifyContent: 'center' },
  stateText: { fontSize: 13, color: sf.trackSub, fontFamily: fonts.bodyR },
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
