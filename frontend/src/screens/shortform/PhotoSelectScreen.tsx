/**
 * SCREEN 08-1 · 사진 선택 및 상세설정 (route: PhotoSelect — Shortform stack ROOT,
 * reached from the drawer). MainHeader (no back, hamburger) + haze bg.
 * 기간 필터 칩 · 인증 사진 3열 그리드(다중 선택, 골드 체크 배지) · N장 선택됨.
 * Footer: AI 대본 / 음악 → 각 오버레이, 생성하기 → Generating.
 * Motion: grid cells stagger-pop (ZoomIn.delay), chips/buttons spring press.
 *
 * 사진 그리드는 새로 촬영/업로드하는 사진이 아니라, 이미 승인된 "퀘스트 인증 사진"
 * 중에서 골라 숏폼 소재로 쓴다 (short_form.schemas.ScriptGenerateRequest 문서 기준).
 * GET /shortforms/eligible-media(getEligibleMedia)로 조회 — 썸네일 표시용
 * media_url(presigned URL)과 숏폼 생성 요청용 media_s3_key(원본 S3 key)가
 * 분리되어 내려온다.
 */
import React, { useEffect, useMemo, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Pressable,
  ScrollView,
  Image,
  ActivityIndicator,
  useWindowDimensions,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { StatusBar } from 'expo-status-bar';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Animated, { ZoomIn } from 'react-native-reanimated';
import HazeBackground from '../../components/HazeBackground';
import MainHeader from '../../components/MainHeader';
import SpringButton from '../../components/SpringButton';
import { CheckMark } from '../../components/PixelIcons';
import { useToast } from '../../components/Toast';
import { colors, fonts } from '../../theme';
import { AiScriptPopup, MusicSheet } from './_parts';
import { getQuest } from '../../api/quest';
import {
  createShortform,
  generateScript,
  getBackgroundMusicList,
  getEligibleMedia,
  CaptionItem,
  BackgroundMusic,
  EligibleMedia,
} from '../../api/shortform';

const PERIODS = ['전체', '이번주', '1주전', '2주전', '3주전'];
const PERIOD_DAYS: (number | null)[] = [null, 7, 14, 21, 28];
const DEFAULT_TITLE = '나의 선행 숏폼';

export default function PhotoSelectScreen({ navigation, route }: any) {
  const insets = useSafeAreaInsets();
  const { width } = useWindowDimensions();
  const toast = useToast();

  const [period, setPeriod] = useState(0);
  const [submissions, setSubmissions] = useState<EligibleMedia[]>([]);
  const [loadingSubmissions, setLoadingSubmissions] = useState(true);
  const [submissionsError, setSubmissionsError] = useState<string | null>(null);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);

  const [scriptOpen, setScriptOpen] = useState(false);
  const [musicOpen, setMusicOpen] = useState(false);
  const [preparing, setPreparing] = useState(false);
  const [generating, setGenerating] = useState(false);

  // short_form 레코드는 생성 시점의 title/bgm_id가 그대로 굳어버려서(수정 API 없음),
  // 대본/음악 팝업 중 먼저 여는 쪽에서 shortsId를 미리 확보해 AI 대본 호출에 쓴다.
  // 이후 "생성하기" 시점에 실제 선택된 title/bgm과 어긋나 있으면 그때 다시 생성해서
  // 최종 값을 반영한다 (대본을 먼저 하든 음악을 먼저 하든 둘 다 최종적으로 반영되게).
  const [shortsId, setShortsId] = useState<number | null>(null);
  const [shortsIdBgmId, setShortsIdBgmId] = useState<number | undefined>(undefined);
  const [shortsIdTitle, setShortsIdTitle] = useState<string | undefined>(undefined);
  const [selectedBgm, setSelectedBgm] = useState<BackgroundMusic | null>(null);
  const [captions, setCaptions] = useState<CaptionItem[] | null>(null);
  const [scriptTitle, setScriptTitle] = useState<string | null>(null);
  const questTitleCache = React.useRef<Map<number, string>>(new Map());

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        setLoadingSubmissions(true);
        setSubmissionsError(null);
        const result = await getEligibleMedia(0, 100);
        if (!mounted) return;
        setSubmissions(
          result.filter(
            (item): item is EligibleMedia & { media_url: string; media_s3_key: string } =>
              typeof item.media_url === 'string' &&
              item.media_url.trim().length > 0 &&
              typeof item.media_s3_key === 'string' &&
              item.media_s3_key.trim().length > 0,
          ),
        );
      } catch (error) {
        console.error('인증 사진 조회 실패:', error);
        if (mounted) setSubmissionsError('인증 사진을 불러오지 못했습니다.');
      } finally {
        if (mounted) setLoadingSubmissions(false);
      }
    })();
    return () => {
      mounted = false;
    };
  }, []);

  const filteredSubmissions = useMemo(() => {
    const days = PERIOD_DAYS[period];
    if (days == null) return submissions;
    const now = Date.now();
    const from = now - days * 86400000;
    const to = now - (days - 7) * 86400000;
    return submissions.filter((s) => {
      const t = new Date(s.submitted_at).getTime();
      return t >= from && t < to;
    });
  }, [submissions, period]);

  const selectedSubmissions = useMemo(
    () => submissions.filter((s) => selectedIds.includes(s.submission_id)),
    [submissions, selectedIds],
  );
  const mediaKeys = useMemo(
    () => selectedSubmissions.map((s) => s.media_s3_key as string),
    [selectedSubmissions],
  );

  const toggle = (submissionId: number) =>
    setSelectedIds((cur) =>
      cur.includes(submissionId) ? cur.filter((x) => x !== submissionId) : [...cur, submissionId],
    );

  // 백엔드는 quest_title을 문자열 하나로만 받아서, 서로 다른 퀘스트 사진을 섞어
  // 선택하면 전부 나열하지 않고 "A, B" / 3개 이상이면 "A 외 N건"으로 요약한다.
  const resolveQuestTitle = async (): Promise<string> => {
    if (selectedSubmissions.length === 0) return DEFAULT_TITLE;

    const uniqueQuestIds: number[] = [];
    for (const s of selectedSubmissions) {
      if (!uniqueQuestIds.includes(s.quest_id)) uniqueQuestIds.push(s.quest_id);
    }

    const titles = await Promise.all(
      uniqueQuestIds.map(async (questId) => {
        const cached = questTitleCache.current.get(questId);
        if (cached) return cached;
        try {
          const quest = await getQuest(questId);
          questTitleCache.current.set(questId, quest.quest_title);
          return quest.quest_title;
        } catch (error) {
          console.error('퀘스트 제목 조회 실패:', error);
          return null;
        }
      }),
    );
    const resolved = titles.filter((t): t is string => !!t);

    if (resolved.length === 0) return DEFAULT_TITLE;
    const combined =
      resolved.length <= 2 ? resolved.join(', ') : `${resolved[0]} 외 ${resolved.length - 1}건`;
    // ShortFormCreateRequest.title / ScriptGenerateRequest.quest_title 둘 다 max_length=255
    return combined.slice(0, 255);
  };

  /** 대본/음악 팝업 중 먼저 필요해지는 시점에 한 번만 호출해 shorts_id를 확보한다. */
  const ensureShortsId = async (): Promise<number> => {
    if (shortsId != null) return shortsId;
    const title = await resolveQuestTitle();
    const created = await createShortform(title, mediaKeys, selectedBgm?.bgm_id);
    setShortsId(created.shorts_id);
    setShortsIdBgmId(selectedBgm?.bgm_id);
    setShortsIdTitle(title);
    return created.shorts_id;
  };

  const openScriptPopup = async () => {
    if (selectedSubmissions.length === 0) {
      toast.show('사진을 먼저 선택해주세요.');
      return;
    }
    try {
      setPreparing(true);
      await ensureShortsId();
      setScriptOpen(true);
    } catch (error) {
      console.error('숏폼 준비 실패:', error);
      toast.show('숏폼 생성을 시작하지 못했습니다.');
    } finally {
      setPreparing(false);
    }
  };

  const handleGenerate = async () => {
    if (selectedSubmissions.length === 0) {
      toast.show('사진을 먼저 선택해주세요.');
      return;
    }
    try {
      setGenerating(true);
      const finalBgmId = selectedBgm?.bgm_id;
      const finalTitle = scriptTitle ?? (await resolveQuestTitle());

      let finalShortsId = shortsId;
      // shortsId가 없거나(대본 팝업을 아예 안 연 경우), 대본을 먼저 만든 뒤 음악을
      // 나중에 골라서(또는 그 반대) 이미 생성된 레코드의 title/bgm_id와 어긋난 경우
      // → 최종 값으로 다시 생성해서 두 선택이 모두 반영되게 한다.
      if (finalShortsId == null || shortsIdBgmId !== finalBgmId || shortsIdTitle !== finalTitle) {
        const created = await createShortform(finalTitle, mediaKeys, finalBgmId);
        finalShortsId = created.shorts_id;
        setShortsId(finalShortsId);
        setShortsIdBgmId(finalBgmId);
        setShortsIdTitle(finalTitle);
      }

      navigation.navigate('Generating', {
        shortsId: finalShortsId,
        mediaKeys,
        captions,
        title: finalTitle,
        bgmId: finalBgmId,
      });
    } catch (error) {
      console.error('숏폼 생성을 시작하지 못했습니다:', error);
      toast.show('숏폼 생성을 시작하지 못했습니다.');
    } finally {
      setGenerating(false);
    }
  };

  /**
   * "자동 생성" 버튼 - 대본 팝업을 열지 않고, AI가 선택된 사진/영상을 분석해
   * 대본과 음악(RAG 자동 매칭)을 전부 자동으로 정한 뒤 바로 숏폼 생성 화면으로 이동한다.
   * 이미 만들어둔 draft(있다면)와 무관하게 항상 새로 만든다 - 자동 경로는 사용자가
   * 수동으로 골라둔 음악(selectedBgm)도 무시하고 RAG 매칭 결과를 그대로 쓴다.
   */
  const runAutoGenerate = async (): Promise<void> => {
    if (selectedSubmissions.length === 0) {
      throw new Error('사진을 먼저 선택해주세요.');
    }
    const placeholderTitle = await resolveQuestTitle();
    const draft = await createShortform(placeholderTitle, mediaKeys, undefined);
    const scriptResult = await generateScript(draft.shorts_id, mediaKeys, placeholderTitle);

    let finalShortsId = draft.shorts_id;
    let finalBgmId = draft.bgm_id;
    const finalTitle = scriptResult.title || placeholderTitle;

    // title은 생성 이후 고칠 API가 없어서, AI가 만든 제목을 실제로 반영하려면 다시 생성해야 한다.
    if (finalTitle !== placeholderTitle) {
      const recreated = await createShortform(finalTitle, mediaKeys, finalBgmId);
      finalShortsId = recreated.shorts_id;
      finalBgmId = recreated.bgm_id;
    }

    let bgm: BackgroundMusic | null = null;
    try {
      const list = await getBackgroundMusicList();
      bgm = list.items.find((b) => b.bgm_id === finalBgmId) ?? null;
    } catch (error) {
      console.error('자동 매칭된 배경음악 조회 실패:', error);
    }

    setShortsId(finalShortsId);
    setShortsIdBgmId(finalBgmId);
    setShortsIdTitle(finalTitle);
    setSelectedBgm(bgm);
    setCaptions(scriptResult.captions);
    setScriptTitle(finalTitle);
    setScriptOpen(false);

    navigation.navigate('Generating', {
      shortsId: finalShortsId,
      mediaKeys,
      captions: scriptResult.captions,
      title: finalTitle,
      bgmId: finalBgmId,
    });
  };

  const GAP = 4;
  const GRID_PAD = 16;
  const cell = Math.floor((width - GRID_PAD * 2 - GAP * 2) / 3);

  const footerH = 46 + 10 + 52 + 20; // buttons row + gap + primary + top pad

  return (
    <View style={styles.root}>
      <StatusBar style="light" />
      <HazeBackground />
      <MainHeader />

      <ScrollView
        contentContainerStyle={[styles.body, { paddingBottom: footerH + insets.bottom + 40 }]}
        showsVerticalScrollIndicator={false}
      >
        <Text style={styles.h1}>숏폼 생성</Text>
        <Text style={styles.sub}>퀘스트 인증 사진으로 숏폼 영상을 만들어보세요.</Text>

        {/* 기간 필터 칩 */}
        <View style={styles.chipsRow}>
          {PERIODS.map((label, i) => {
            const active = i === period;
            return (
              <SpringButton
                key={label}
                onPress={() => setPeriod(i)}
                pressScale={0.92}
                style={[styles.chip, active ? styles.chipActive : styles.chipIdle]}
              >
                <Text style={[styles.chipText, active ? styles.chipTextActive : styles.chipTextIdle]}>
                  {label}
                </Text>
              </SpringButton>
            );
          })}
        </View>

        {/* 3열 사진 그리드 - 승인된 퀘스트 인증 사진 중 선택 */}
        {loadingSubmissions ? (
          <View style={styles.stateWrap}>
            <ActivityIndicator color={colors.primaryDark} />
            <Text style={styles.stateText}>인증 사진을 불러오는 중입니다</Text>
          </View>
        ) : submissionsError ? (
          <View style={styles.stateWrap}>
            <Text style={styles.errorText}>{submissionsError}</Text>
          </View>
        ) : filteredSubmissions.length === 0 ? (
          <View style={styles.stateWrap}>
            <Text style={styles.stateText}>선택한 기간에 인증 사진이 없습니다</Text>
          </View>
        ) : (
          <View style={styles.grid}>
            {filteredSubmissions.map((item, i) => {
              const sel = selectedIds.includes(item.submission_id);
              return (
                <Animated.View
                  key={item.submission_id}
                  entering={ZoomIn.delay(30 + i * 40).duration(360)}
                  style={{ width: cell, height: cell }}
                >
                  <Pressable
                    onPress={() => toggle(item.submission_id)}
                    style={[styles.cell, sel && styles.cellSelected]}
                  >
                    <Image
                      source={{ uri: item.media_url as string }}
                      style={StyleSheet.absoluteFill}
                      resizeMode="cover"
                    />
                    {sel ? (
                      <View style={styles.badge}>
                        <CheckMark size={12} color="#fff" />
                      </View>
                    ) : null}
                  </Pressable>
                </Animated.View>
              );
            })}
          </View>
        )}

        <Text style={styles.count}>{selectedIds.length}장 선택됨</Text>
      </ScrollView>

      {/* 하단 액션 (사진첩 fade → 배경으로 자연스럽게) */}
      <LinearGradient
        colors={['rgba(238,246,240,0)', colors.screenBg]}
        locations={[0, 0.3]}
        style={[styles.footer, { paddingBottom: insets.bottom + 12 }]}
      >
        <View style={styles.footerRow}>
          <View style={styles.footerHalf}>
            <SpringButton onPress={openScriptPopup} disabled={preparing} style={styles.ghostBtn}>
              {preparing ? (
                <ActivityIndicator color={colors.primaryDark} size="small" />
              ) : (
                <Text style={styles.ghostText}>AI 대본</Text>
              )}
            </SpringButton>
          </View>
          <View style={styles.footerHalf}>
            <SpringButton onPress={() => setMusicOpen(true)} style={styles.ghostBtn}>
              <Text style={styles.ghostText}>음악{selectedBgm ? ` · ${selectedBgm.title}` : ''}</Text>
            </SpringButton>
          </View>
        </View>
        <SpringButton onPress={handleGenerate} disabled={generating} style={styles.primaryBtn}>
          {generating ? (
            <ActivityIndicator color={colors.primaryDark} />
          ) : (
            <Text style={styles.primaryText}>생성하기</Text>
          )}
        </SpringButton>
      </LinearGradient>

      <AiScriptPopup
        visible={scriptOpen}
        onClose={() => setScriptOpen(false)}
        shortsId={shortsId}
        mediaKeys={mediaKeys}
        questTitleResolver={resolveQuestTitle}
        onConfirmed={(result) => {
          setCaptions(result.captions);
          setScriptTitle(result.title);
        }}
        onAutoGenerate={runAutoGenerate}
      />
      <MusicSheet
        visible={musicOpen}
        onClose={() => setMusicOpen(false)}
        selectedBgmId={selectedBgm?.bgm_id ?? null}
        onSelect={setSelectedBgm}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.screenBg },
  body: { paddingHorizontal: 16, paddingTop: 16 },
  h1: { fontFamily: fonts.pixel, fontSize: 18, color: colors.primaryDark },
  sub: { fontSize: 13, color: '#888', marginTop: 2, marginBottom: 14, fontFamily: fonts.bodyR },
  stateWrap: { paddingVertical: 40, alignItems: 'center', justifyContent: 'center', gap: 10 },
  stateText: { fontSize: 13, color: colors.textMuted, fontFamily: fonts.bodyR },
  errorText: { fontSize: 13, color: colors.danger, fontFamily: fonts.bodyR },

  chipsRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 14 },
  chip: { borderRadius: 20, paddingHorizontal: 14, paddingVertical: 6 },
  chipActive: { backgroundColor: colors.primaryDark, borderWidth: 2, borderColor: colors.primaryDark },
  chipIdle: { backgroundColor: colors.white, borderWidth: 1, borderColor: colors.pixelBorder },
  chipText: { fontSize: 13, fontWeight: '700', fontFamily: fonts.bodyB },
  chipTextActive: { color: colors.parchment },
  chipTextIdle: { color: colors.primaryDark },

  grid: { flexDirection: 'row', flexWrap: 'wrap', gap: 4, marginBottom: 12 },
  cell: { flex: 1, borderRadius: 8, overflow: 'hidden', borderWidth: 2, borderColor: 'transparent' },
  cellSelected: { borderColor: colors.gold },
  badge: {
    position: 'absolute',
    top: 5,
    right: 5,
    width: 20,
    height: 20,
    borderRadius: 10,
    backgroundColor: colors.gold,
    alignItems: 'center',
    justifyContent: 'center',
  },
  count: { textAlign: 'right', fontFamily: fonts.pixel, fontSize: 14, color: colors.gold },

  footer: { position: 'absolute', left: 0, right: 0, bottom: 0, paddingHorizontal: 16, paddingTop: 10 },
  footerRow: { flexDirection: 'row', gap: 10, marginBottom: 10 },
  footerHalf: { flex: 1 },
  ghostBtn: {
    height: 46,
    borderRadius: 8,
    borderWidth: 1.5,
    borderColor: colors.pixelBorder,
    backgroundColor: colors.screenBg,
    alignItems: 'center',
    justifyContent: 'center',
  },
  ghostText: { fontFamily: fonts.pixel, fontSize: 15, color: colors.primaryDark },
  primaryBtn: {
    height: 52,
    borderRadius: 8,
    backgroundColor: colors.gold,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: colors.gold,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 14,
    elevation: 5,
  },
  primaryText: { fontFamily: fonts.pixel, fontSize: 18, color: colors.primaryDark },
});
