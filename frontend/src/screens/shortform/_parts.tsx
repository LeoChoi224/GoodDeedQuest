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
import { useVideoPlayer, VideoView } from 'expo-video';
import { useEvent } from 'expo';
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
  savedCaptions,
  savedTitle,
}: {
  visible: boolean;
  onClose: () => void;
  shortsId: number | null;
  mediaKeys: string[];
  questTitleResolver: () => Promise<string>;
  onConfirmed: (result: ScriptGenerateResult) => void;
  /** 부모(사진 선택 화면)가 들고 있는, 마지막으로 저장된 대본. 팝업을 열 때마다
   * 이 값으로 텍스트박스를 동기화한다 - 부모가 사진 선택 변경 등으로 이 값을
   * null로 초기화했다면 팝업도 빈 텍스트박스로 열려야 하기 때문. */
  savedCaptions: CaptionItem[] | null;
  savedTitle: string | null;
}) {
  const { width } = useWindowDimensions();
  const toast = useToast();
  const [text, setText] = useState('');
  const [title, setTitle] = useState('');
  const [captions, setCaptions] = useState<CaptionItem[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [closing, setClosing] = useState(false);

  // ⭐ 수정: 팝업이 열릴 때마다 부모의 저장된 대본으로 내부 상태를 동기화한다.
  // 이게 없으면 부모가 captions를 초기화(예: 사진 선택 변경)해도 팝업은 이전에
  // 생성해둔 텍스트를 계속 들고 있어서(컴포넌트가 visible=false여도 unmount되지
  // 않음), 다시 열었을 때 텍스트박스에 낡은 대본이 그대로 보이는 버그가 있었다.
  useEffect(() => {
    if (!visible) return;
    if (savedCaptions) {
      setCaptions(savedCaptions);
      setTitle(savedTitle ?? '');
      setText(captionsToText(savedCaptions));
    } else {
      setCaptions(null);
      setTitle('');
      setText('');
    }
    // 팝업이 열리는 시점(visible: false -> true)에만 동기화한다. savedCaptions/savedTitle을
    // 의존성에 넣으면 팝업이 열려있는 동안 부모 상태가 바뀔 때마다 다시 동기화되어,
    // "생성하기"로 막 채운 텍스트박스를 덮어써버릴 수 있다.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [visible]);

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

  // ⭐ 수정: "자동 생성" → "적용하기". 새로 생성하지 않는다 - "생성하기"로 이미 만들어둔
  // 대본(현재 텍스트박스 내용)을 그대로 저장하고 사진 선택 화면으로 돌아간다.
  // close()와 동일한 저장 로직(편집했으면 검증 후 반영)을 그대로 재사용한다.
  const onApply = async () => {
    if (!captions) {
      toast.show('먼저 "생성하기"를 눌러 대본을 만들어주세요.');
      return;
    }
    await close();
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
          <SpringButton onPress={onApply} disabled={loading || closing} style={[ai.btn, ai.btnAuto]}>
            <Text style={ai.btnAutoText}>적용하기</Text>
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
// BackgroundMusic.preview_url(presigned URL)을 expo-video 플레이어로 재생한다.
// VideoView는 렌더링하지 않고(오디오만 필요) player 인스턴스만 붙여서 소리를 낸다.
function PreviewBar({ name, previewUrl }: { name: string; previewUrl: string | null }) {
  // player 정지는 별도 effect로 직접 호출하지 않는다 - useVideoPlayer가 컴포넌트
  // unmount 시 내부적으로 이미 player를 release하는데, 여기서 또 pause()를 부르면
  // "shared object that was already released" 네이티브 크래시로 이어진다.
  // PreviewBar는 트랙 전환/시트 닫힘 시 조건부 렌더링으로 unmount되므로, 그 자체로 정지된다.
  const player = useVideoPlayer(previewUrl, (p) => {
    p.loop = true;
    p.timeUpdateEventInterval = 0.25;
    if (previewUrl) p.play();
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

  if (!previewUrl) {
    return (
      <View style={ms.preview}>
        <Text style={ms.previewName}>이 트랙은 미리듣기를 지원하지 않습니다.</Text>
      </View>
    );
  }

  return (
    <View style={ms.preview}>
      <View style={{ flex: 1 }}>
        <Text style={ms.previewName}>{name}</Text>
        <View style={ms.progTrack}>
          <View style={[ms.progFill, { width: `${progress * 100}%` }]} />
        </View>
      </View>
      <SpringButton
        onPress={() => (isPlaying ? player.pause() : player.play())}
        style={ms.playBtn}
        pressScale={0.9}
      >
        {isPlaying ? <PauseBars /> : <PlayTri />}
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
    if (!visible) {
      // 시트를 닫아도 BottomSheet의 Modal은 visible prop만 바뀔 뿐 자식은 계속 마운트돼
      // 있으므로, 재생 중이던 미리듣기가 있으면 여기서 명시적으로 정지시켜야 한다.
      setOpen(null);
      return;
    }
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
                  {open === i ? <PreviewBar name={t.title} previewUrl={t.preview_url} /> : null}
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
