/**
 * SCREEN 7 · AI 커스텀 추천 (route AiRecommend, back) — 챗봇 메시지 버블 + 타이핑
 * 인디케이터(3-dot wave). 추천 응답에는 「퀘스트」 + "퀘스트 상세" 칩 → QuestDetail.
 * 전송 시 유저 말풍선 + 타이핑 → 추천 응답. 입력이 비면 전송 비활성.
 */
import React, { useRef, useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TextInput, Pressable, KeyboardAvoidingView, Platform } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Animated, { FadeInDown } from 'react-native-reanimated';
import { colors, fonts } from '../../theme';
import HazeBackground from '../../components/HazeBackground';
import MainHeader from '../../components/MainHeader';
import SpringButton from '../../components/SpringButton';
import { BotAvatar, TypingBubble, ChevRight } from './_parts';

type Quest = { title: string; category: string; point: number; exp: number };
type Msg = { who: 'bot' | 'user' | 'reco'; text: string; quest?: Quest };

const PLOGGING: Quest = { title: '공원 플로깅', category: 'environment', point: 250, exp: 100 };
const ELDERLY: Quest = { title: '독거 어르신 안부 전화', category: 'community', point: 300, exp: 120 };

const INITIAL: Msg[] = [
  { who: 'bot', text: '원하는 요청을 입력하시면 맞춤 선행을 추천해 드립니다.' },
  { who: 'user', text: '퇴근 30분 전! 퇴근하고 할만한 선행 추천해줘' },
  { who: 'reco', text: '「공원 플로깅」 을 추천해 드립니다.', quest: PLOGGING },
];

export default function AiRecommendScreen({ navigation }: any) {
  const insets = useSafeAreaInsets();
  const [msgs, setMsgs] = useState<Msg[]>(INITIAL);
  const [input, setInput] = useState('');
  const [typing, setTyping] = useState(false);
  const scrollRef = useRef<ScrollView>(null);

  const scrollDown = () => requestAnimationFrame(() => scrollRef.current?.scrollToEnd({ animated: true }));

  const openDetail = (q: Quest) =>
    navigation.navigate('QuestDetail', { title: q.title, category: q.category, point: q.point, exp: q.exp, active: false });

  const send = () => {
    const v = input.trim();
    if (!v) return;
    setInput('');
    setMsgs((m) => [...m, { who: 'user', text: v }]);
    setTyping(true);
    scrollDown();
    setTimeout(() => {
      setTyping(false);
      setMsgs((m) => [...m, { who: 'reco', text: '「독거 어르신 안부 전화」 를 추천해 드립니다.', quest: ELDERLY }]);
      scrollDown();
    }, 1300);
  };

  return (
    <View style={styles.root}>
      <StatusBar style="light" />
      <HazeBackground />
      <MainHeader showBack title="AI 커스텀 추천" onBack={() => navigation.goBack()} />

      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : undefined} keyboardVerticalOffset={0}>
        <ScrollView
          ref={scrollRef}
          contentContainerStyle={styles.chat}
          showsVerticalScrollIndicator={false}
          onContentSizeChange={scrollDown}
        >
          {msgs.map((m, i) => (
            <Animated.View key={i} entering={FadeInDown.duration(360)}>
              {m.who === 'user' ? (
                <View style={styles.userRow}>
                  <View style={styles.userBubble}>
                    <Text style={styles.userText}>{m.text}</Text>
                  </View>
                </View>
              ) : (
                <View style={styles.botRow}>
                  <BotAvatar />
                  <View style={styles.botBubble}>
                    <Text style={styles.botText}>{m.text}</Text>
                    {m.who === 'reco' && m.quest ? (
                      <Pressable onPress={() => openDetail(m.quest!)} style={styles.detailChip}>
                        <Text style={styles.detailChipText}>퀘스트 상세</Text>
                        <ChevRight size={16} color="#033236" />
                      </Pressable>
                    ) : null}
                  </View>
                </View>
              )}
            </Animated.View>
          ))}
          {typing ? <TypingBubble /> : null}
        </ScrollView>

        <View style={[styles.inputBar, { paddingBottom: insets.bottom + 14 }]}>
          <TextInput
            value={input}
            onChangeText={setInput}
            placeholder="원하는 선행을 요청해 보세요"
            placeholderTextColor={colors.textMuted}
            style={styles.input}
            returnKeyType="send"
            onSubmitEditing={send}
          />
          <SpringButton onPress={send} disabled={!input.trim()} style={[styles.sendBtn, { opacity: input.trim() ? 1 : 0.5 }]}>
            <Text style={styles.sendText}>전송</Text>
          </SpringButton>
        </View>
      </KeyboardAvoidingView>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.screenBg },
  chat: { padding: 16, gap: 16, paddingBottom: 24 },

  userRow: { flexDirection: 'row', justifyContent: 'flex-end' },
  userBubble: {
    maxWidth: '78%',
    backgroundColor: colors.primaryDark,
    borderTopLeftRadius: 16,
    borderTopRightRadius: 16,
    borderBottomRightRadius: 16,
    borderBottomLeftRadius: 16,
    paddingHorizontal: 14,
    paddingVertical: 11,
  },
  userText: { color: colors.white, fontSize: 14, lineHeight: 21, fontFamily: fonts.bodyR },

  botRow: { flexDirection: 'row', alignItems: 'flex-end', gap: 8 },
  botBubble: {
    maxWidth: '78%',
    backgroundColor: colors.white,
    borderWidth: 1,
    borderColor: '#EDF1EF',
    borderTopLeftRadius: 16,
    borderTopRightRadius: 16,
    borderBottomRightRadius: 16,
    borderBottomLeftRadius: 4,
    paddingHorizontal: 14,
    paddingVertical: 12,
  },
  botText: { fontSize: 14, color: colors.textPrimary, lineHeight: 21, fontFamily: fonts.bodyR },
  detailChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    alignSelf: 'flex-start',
    marginTop: 10,
    backgroundColor: colors.screenBg,
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 6,
  },
  detailChipText: { fontSize: 12, fontWeight: '700', color: colors.primaryDark, fontFamily: fonts.bodyB },

  inputBar: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    paddingHorizontal: 16,
    paddingTop: 14,
    backgroundColor: colors.white,
    borderTopWidth: 1,
    borderTopColor: '#EDF1EF',
  },
  input: {
    flex: 1,
    height: 44,
    backgroundColor: '#F6F6F6',
    borderRadius: 22,
    paddingHorizontal: 16,
    fontSize: 14,
    color: colors.textPrimary,
    fontFamily: fonts.bodyR,
  },
  sendBtn: { height: 44, paddingHorizontal: 18, borderRadius: 22, backgroundColor: colors.primaryDark, alignItems: 'center', justifyContent: 'center' },
  sendText: { color: colors.white, fontSize: 14, fontWeight: '700', fontFamily: fonts.bodyB },
});
