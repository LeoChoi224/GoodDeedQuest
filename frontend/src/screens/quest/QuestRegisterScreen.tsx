/**
 * SCREEN 6 · 퀘스트 등록 (route QuestRegister, back) — 제목/내용 입력 + 카테고리 6종
 * 토글 + AI 보상 판단(idle → 분석중[spinner+shimmer] → 완료[예상 보상 카드]).
 * "등록하기"는 제목·내용·카테고리가 채워지면 활성 → Toast 후 QuestHome.
 */
import React, { useState } from 'react';
import { View, Text, Image, StyleSheet, ScrollView, Pressable, TextInput, KeyboardAvoidingView, Platform } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { LinearGradient } from 'expo-linear-gradient';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Animated, { FadeInDown } from 'react-native-reanimated';
import { colors, fonts, radii, shadow, CATEGORY_DEFS, CATEGORY_ICONS } from '../../theme';
import HazeBackground from '../../components/HazeBackground';
import MainHeader from '../../components/MainHeader';
import GdqInput from '../../components/GdqInput';
import SpringButton from '../../components/SpringButton';
import Shimmer from '../../components/Shimmer';
import Shake from '../../components/Shake';
import { useToast } from '../../components/Toast';
import { previewQuest, createQuest, difficultyLabel, type QuestJudgement } from '../../api/quest';
import { AiIcon, SpinnerRing, CoinW, StarW } from './_parts';

type Stage = 'idle' | 'loading' | 'done';

export default function QuestRegisterScreen({ navigation, route }: any) {
  const insets = useSafeAreaInsets();
  const toast = useToast();

  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  // DB의 quest.category_id가 단일 FK라 카테고리도 하나만 고른다
  const [category, setCategory] = useState('environment');
  const [stage, setStage] = useState<Stage>('idle');
  const [preview, setPreview] = useState<QuestJudgement | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [shake, setShake] = useState(0);

  const over = content.length > 200;
  const ready = title.trim().length > 0 && content.trim().length > 0 && !over;

  const runAI = async () => {
    if (stage === 'loading') return;
    if (!ready) {
      setShake((v) => v + 1);
      return;
    }
    setStage('loading');
    try {
      const result = await previewQuest(title.trim(), content.trim(), category);
      setPreview(result);
      setStage('done');
      if (!result.accepted) toast.show(result.reason, 5000);
    } catch (err: any) {
      setStage('idle');
      toast.show('AI 심사에 실패했어요. 잠시 후 다시 시도해 주세요.');
    }
  };

  const onRegister = async () => {
    if (!ready) {
      setShake((v) => v + 1);
      return;
    }
    if (submitting) return;
    setSubmitting(true);
    try {
      // 미리보기 값이 아니라 서버가 다시 판정한 결과로 등록된다
      const result = await createQuest(title.trim(), content.trim(), category);
      if (!result.accepted) {
        setPreview(result);
        setStage('done');
        toast.show(result.reason, 5000);
        return;
      }
      toast.show(`퀘스트가 등록되었어요 (${result.reward_point}P / ${result.reward_exp} EXP)`, 4000);
      if (route?.params?.returnToTeamCreate) {
        if (result.quest_id === null) {toast.show('등록된 퀘스트 정보를 확인하지 못했어요.');
          return;
        }
        navigation.popTo('TeamList', {openCreate: true, selectedQuestId: result.quest_id});
        return;
      }
      navigation.navigate('QuestHome');
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      toast.show(typeof detail === 'string' ? detail : '등록에 실패했어요. 다시 시도해 주세요.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <View style={styles.root}>
      <StatusBar style="light" />
      <HazeBackground />
      <MainHeader showBack title="퀘스트 등록" onBack={() => navigation.goBack()} />

      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <ScrollView contentContainerStyle={styles.body} showsVerticalScrollIndicator={false} keyboardShouldPersistTaps="handled">
          <Text style={styles.label}>퀘스트 제목</Text>
          <View style={{ marginBottom: 16 }}>
            <GdqInput value={title} onChangeText={setTitle} placeholder="퀘스트 제목을 입력하세요" />
          </View>

          <Text style={styles.label}>퀘스트 내용</Text>
          <View style={styles.descWrap}>
            <TextInput
              value={content}
              onChangeText={setContent}
              placeholder="어떤 선행 퀘스트인지 설명해 주세요"
              placeholderTextColor={colors.textMuted}
              multiline
              style={[styles.textarea, { borderColor: over ? colors.danger : colors.inputBorder }]}
            />
            <Text style={[styles.counter, { color: over ? colors.danger : colors.textMuted }]}>{content.length}/200</Text>
          </View>

          <Text style={styles.section}>카테고리</Text>
          <View style={styles.grid}>
            {CATEGORY_DEFS.map((c, i) => {
              const on = category === c.key;
              return (
                <Animated.View key={c.key} entering={FadeInDown.delay(i * 55).duration(400)} style={styles.gridCell}>
                  <Pressable
                    onPress={() => setCategory(c.key)}
                    style={[styles.catCell, on ? styles.cellOn : styles.cellOff]}
                  >
                    <Image source={CATEGORY_ICONS[c.key]} style={styles.catIcon} />
                    <Text style={[styles.catLabel, { color: on ? colors.white : colors.textPrimary }]}>{c.label}</Text>
                  </Pressable>
                </Animated.View>
              );
            })}
          </View>

          {/* AI reward box */}
          <Pressable onPress={runAI} style={[styles.aiBox, aiBoxStyle(stage, preview?.accepted)]}>
            {stage === 'loading' ? (
              <View style={styles.aiLoadingRow}>
                <SpinnerRing size={20} />
                <View style={{ flex: 1 }}>
                  <Shimmer width="100%" height={14} radius={4} />
                </View>
                <Text style={styles.aiLoadingText}>분석중</Text>
              </View>
            ) : stage === 'done' && preview ? (
              preview.accepted ? (
                <View>
                  <Text style={styles.aiDoneTitle}>
                    AI 예상 보상 · 난이도 {difficultyLabel(preview.difficulty!)}
                  </Text>
                  <View style={styles.aiPills}>
                    <View style={[styles.aiPill, { backgroundColor: colors.xpGreen }]}>
                      <StarW />
                      <Text style={styles.aiPillText}>{preview.reward_exp} EXP</Text>
                    </View>
                    <View style={[styles.aiPill, { backgroundColor: colors.gold }]}>
                      <CoinW />
                      <Text style={styles.aiPillText}>{preview.reward_point} P</Text>
                    </View>
                  </View>
                  <Text style={styles.aiNote}>등록할 때 다시 판정되어 값이 조금 달라질 수 있어요</Text>
                </View>
              ) : (
                <View>
                  <Text style={styles.aiRejectTitle}>등록할 수 없는 퀘스트예요</Text>
                  <Text style={styles.aiRejectText}>{preview.reason}</Text>
                </View>
              )
            ) : (
              <View style={styles.aiIdleRow}>
                <AiIcon />
                <Text style={styles.aiIdleText}>AI 퀘스트 보상 판단</Text>
              </View>
            )}
          </Pressable>
        </ScrollView>
      </KeyboardAvoidingView>

      <LinearGradient
        colors={['rgba(243,250,244,0)', '#F3FAF4']}
        locations={[0, 0.35]}
        style={[styles.footer, { paddingBottom: insets.bottom + 20 }]}
      >
        <Shake trigger={shake}>
          <SpringButton
            onPress={onRegister}
            active={ready}
            bgColors={[colors.disabled, colors.primaryDark]}
            style={[styles.regBtn, ready && shadow.button]}
          >
            <Text style={styles.regText}>등록하기</Text>
          </SpringButton>
        </Shake>
      </LinearGradient>
    </View>
  );
}

function aiBoxStyle(stage: Stage, accepted?: boolean) {
  if (stage === 'loading') return { backgroundColor: '#F3F7F4', borderWidth: 1, borderColor: '#D6E7DC' };
  if (stage === 'done') {
    // 거절이면 초록 대신 경고색으로 — 통과한 것처럼 보이면 안 된다
    return accepted
      ? { backgroundColor: '#F0FFF4', borderWidth: 1.5, borderColor: colors.xpGreen }
      : { backgroundColor: '#FFF5F5', borderWidth: 1.5, borderColor: colors.danger };
  }
  return { backgroundColor: colors.screenBg, borderWidth: 1, borderColor: '#D6E7DC' };
}

const CELL_GAP = 10;

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.screenBg },
  body: { paddingHorizontal: 20, paddingTop: 22, paddingBottom: 120 },

  label: { fontSize: 12, fontWeight: '600', color: colors.textPrimary, marginBottom: 7, fontFamily: fonts.bodyM },
  descWrap: { position: 'relative', marginBottom: 20 },
  textarea: {
    height: 88,
    borderWidth: 1,
    borderRadius: radii.input,
    paddingTop: 12,
    paddingBottom: 12,
    paddingHorizontal: 14,
    fontSize: 14,
    color: colors.textPrimary,
    fontFamily: fonts.bodyR,
    backgroundColor: colors.white,
    textAlignVertical: 'top',
  },
  counter: { position: 'absolute', right: 12, bottom: 10, fontSize: 11, fontFamily: fonts.bodyR },

  section: { fontSize: 14, fontWeight: '700', color: colors.textPrimary, marginBottom: 12, fontFamily: fonts.bodyB },
  grid: { flexDirection: 'row', flexWrap: 'wrap', marginHorizontal: -CELL_GAP / 2, marginBottom: 22 },
  gridCell: { width: '50%', paddingHorizontal: CELL_GAP / 2, marginBottom: CELL_GAP },
  catCell: { flexDirection: 'row', alignItems: 'center', gap: 8, height: 52, borderRadius: radii.chip, paddingHorizontal: 12 },
  cellOn: { backgroundColor: colors.primaryDark, borderWidth: 2, borderColor: colors.primaryDark },
  cellOff: { backgroundColor: colors.white, borderWidth: 1, borderColor: colors.inputBorder },
  catIcon: { width: 32, height: 32, borderRadius: 7 },
  catLabel: { fontSize: 14, fontWeight: '600', fontFamily: fonts.bodyM },

  aiBox: { borderRadius: radii.button, padding: 16 },
  aiIdleRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8 },
  aiIdleText: { fontSize: 14, fontWeight: '700', color: colors.primaryDark, fontFamily: fonts.bodyB },
  aiLoadingRow: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  aiLoadingText: { fontSize: 12, color: colors.textSecondary, fontFamily: fonts.bodyR },
  aiDoneTitle: { fontSize: 12, fontWeight: '700', color: '#2E7D32', marginBottom: 6, fontFamily: fonts.bodyB },
  aiNote: { fontSize: 11, color: colors.textMuted, marginTop: 8, fontFamily: fonts.bodyR },
  aiRejectTitle: { fontSize: 13, fontWeight: '700', color: colors.danger, marginBottom: 6, fontFamily: fonts.bodyB },
  aiRejectText: { fontSize: 12, lineHeight: 18, color: colors.textSecondary, fontFamily: fonts.bodyR },
  aiPills: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  aiPill: { flexDirection: 'row', alignItems: 'center', gap: 4, borderRadius: 999, paddingHorizontal: 12, paddingVertical: 5 },
  aiPillText: { color: colors.white, fontWeight: '700', fontSize: 13, fontFamily: fonts.bodyB },

  footer: { position: 'absolute', bottom: 0, left: 0, right: 0, paddingHorizontal: 20, paddingTop: 16 },
  regBtn: { height: 52, borderRadius: radii.button, alignItems: 'center', justifyContent: 'center' },
  regText: { color: colors.white, fontSize: 16, fontWeight: '700', fontFamily: fonts.bodyB },
});
